"""
pdf_parser.py — Extract, clean, and chunk text from PDF files for Rephrasia.

CHANGELOG v2.3:
  - FIX (Header Confusion v2): _detect_repeating_lines() now NORMALIZES each line
    before counting — trailing page numbers (e.g. "M.Nadeem 3", "M.Nadeem 7") are
    stripped so the normalized form "M.Nadeem" is the same on every page, making the
    counter correctly identify it as a repeating header.  _strip_headers_from_page()
    also uses normalized matching so it strips "M.Nadeem 3" even though the stored
    canonical form is "M.Nadeem".

  - FIX (Header Confusion v2): Added _apply_slide_header_regex() as a hard-coded
    backstop regex pass for common "course code / university / instructor" slide
    patterns (e.g. "HS 411 - Entrepreneurship - SSUET ... M.Nadeem 3").  This catches
    headers where pypdf merges multiple text boxes onto one line in a way that the
    line-based detector cannot split reliably.

  - FIX (Chunk Truncation): get_paraphrase_chunks() → 700 chars (T5 safe).
    get_translation_chunks() → 1200 chars (NLLB safe).  (unchanged from v2.2)
"""

import io
import logging
import re
from collections import Counter

from pypdf import PdfReader
from chunking import get_paraphrase_chunks, get_translation_chunks

logger = logging.getLogger(__name__)

# ── Header/Footer Detection ───────────────────────────────────────────────────

# A line is considered a repeating header/footer if it appears on at least this
# fraction of all pages (after normalization).
HEADER_DETECTION_THRESHOLD = 0.4

# Minimum and maximum length (of the NORMALIZED line) to consider for detection.
MIN_HEADER_LINE_LEN = 6
MAX_HEADER_LINE_LEN = 200   # raised from 120 to catch longer course-header lines


# ── Slide Header Regex Patterns ───────────────────────────────────────────────
#
# These are INDEPENDENT, FOCUSED patterns applied line-by-line as a backstop after
# the statistical _detect_repeating_lines() pass.  Each pattern targets exactly one
# component of a typical slide/lecture-PDF running header.
#
# WHY THE PREVIOUS VERSION FAILED:
#   The old Pattern 1 required 'nadeem' AND 'HS 411' to appear on the SAME line.
#   pypdf extracts PowerPoint slides with each text box as a separate line, so:
#     Line A: "HS 411 - Entrepreneurship - SSUET"  ← no 'nadeem' → NOT matched
#     Line B: "Prepared By: Dr. Engr. M.Nadeem, Jr." ← no 'HS 411' → pattern 1 skips
#   Pattern 2 caught Line B but Line A survived, making T5/NLLB weave the course
#   name into the narrative ("the author of two case studies on Tesla Inc.").
#
# THE FIX:
#   Each pattern now stands alone.  Line A is caught by Pattern 1 (course-code only).
#   Line B is caught by Pattern 2 (Prepared/Preparation By).  They don't need to
#   co-occur on the same line.
#
_SLIDE_HEADER_PATTERNS: list[str] = [
    # ── Pattern 1: Course code lines ────────────────────────────────────────
    # Matches: "HS 411 - Entrepreneurship - SSUET"
    #          "CS 301 - Data Structures - NED"
    #          "MGT 501 – Business Ethics – IBA"
    # Logic: starts with 2-5 uppercase letters, then 3-4 digits, then a dash separator.
    # Does NOT require the instructor name on the same line.
    r"^\s*[A-Z]{2,5}\s+\d{3,4}\s*[-\u2013\u2014].*$",

    # ── Pattern 2: "Prepared By / Preparation By" lines ─────────────────────
    # Matches: "Prepared By: Dr. Engr. M. Nadeem, Jr."
    #          "Preparation By: Prof. Ahmed Khan"
    r"^\s*prep(?:ared?|aration)\s+by\s*[:\-].*$",

    # ── Pattern 3: Standalone instructor title + name lines ──────────────────
    # Matches: "Dr. Engr. M. Nadeem, Jr."
    #          "Prof. Sara Ahmed"  "Engr. Usman Ali"
    # Logic: starts with an academic title abbreviation followed by a name.
    r"^\s*(?:dr\.?|prof\.?|engr\.?|mr\.?|ms\.?)\s+(?:[A-Z]\.\s+)?[A-Z][a-z]+.*$",

    # ── Pattern 4: University / department acronym lines ─────────────────────
    # Matches: "SSUET"  "NUST"  "IBA"  "NED"  "FAST"
    # Logic: line contains ONLY 3-8 uppercase letters (and optional whitespace).
    r"^\s*[A-Z]{3,8}\s*$",

    # ── Pattern 5: Bullet/symbol noise lines ─────────────────────────────────
    # Matches lines that are entirely Unicode symbols / checkmarks / stars
    # (e.g. "✓ Innovation. ⭐") left behind by slide formatting.
    r"^[\s\u2600-\u27BF\u2B50\u2714\u2022\u25CF\u25E6\u2713\u2705\u274C]+$",

    # ── Pattern 6: Bare page-number lines ────────────────────────────────────
    # Matches: "3"  "Page 3"  "3 / 12"  "- 3 -"  "3 of 12"
    r"^[\-\s]*(?:page\s+)?\d{1,4}(?:\s*(?:of|/)\s*\d{1,4})?[\-\s]*$",
]

_COMPILED_SLIDE_PATTERNS = [
    re.compile(p, re.IGNORECASE | re.MULTILINE)
    for p in _SLIDE_HEADER_PATTERNS
]


def _normalize_header_line(line: str) -> str:
    """
    Normalize a line for header-detection comparison.

    Strips trailing page numbers (e.g. "M.Nadeem 3" → "M.Nadeem") and
    collapses internal whitespace so minor formatting differences don't
    prevent two identical lines from matching.
    """
    # Remove trailing standalone digits (page numbers)
    normalized = re.sub(r"\s+\d{1,4}\s*$", "", line).strip()
    # Collapse internal whitespace
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def _detect_repeating_lines(pages: list[str]) -> dict[str, str]:
    """
    Find lines that recur across many pages — indicating running headers/footers.

    Returns a dict mapping NORMALIZED form → one example of the RAW form.
    The normalized form is used for matching; the raw form is used for logging.

    v2.3 change: lines are normalized before counting so that trailing page
    numbers (e.g. "M.Nadeem 3" vs "M.Nadeem 7") don't prevent detection.
    """
    if len(pages) < 2:
        return {}

    # Count how many pages each NORMALIZED line appears on
    normalized_page_count: Counter = Counter()
    # Also track a canonical raw example for logging
    normalized_to_raw: dict[str, str] = {}

    for page_text in pages:
        # Unique normalized lines per page (deduplicated so one long page
        # with a repeated header doesn't inflate the count)
        unique_normalized: set[str] = set()
        for raw_line in page_text.split("\n"):
            raw = raw_line.strip()
            if not (MIN_HEADER_LINE_LEN <= len(raw) <= MAX_HEADER_LINE_LEN):
                continue
            norm = _normalize_header_line(raw)
            if len(norm) < MIN_HEADER_LINE_LEN:
                continue
            unique_normalized.add(norm)
            if norm not in normalized_to_raw:
                normalized_to_raw[norm] = raw

        for norm in unique_normalized:
            normalized_page_count[norm] += 1

    min_pages = max(2, int(len(pages) * HEADER_DETECTION_THRESHOLD))
    repeating = {
        norm: normalized_to_raw[norm]
        for norm, count in normalized_page_count.items()
        if count >= min_pages
    }

    if repeating:
        logger.info(
            "Header/footer detection: found %d repeating line(s) across %d page(s): %s",
            len(repeating),
            len(pages),
            [v[:60] for v in repeating.values()],
        )
    return repeating


def _strip_headers_from_page(page_text: str, header_norms: dict[str, str]) -> str:
    """
    Remove detected header/footer lines from a single page's text.

    v2.3 change: uses NORMALIZED matching so "M.Nadeem 3" is removed even
    though the stored key is "M.Nadeem" (the normalized form).
    """
    output_lines: list[str] = []
    for raw_line in page_text.split("\n"):
        raw = raw_line.strip()
        norm = _normalize_header_line(raw)

        # Drop if the normalized form is a known header
        if norm in header_norms:
            continue

        # Drop bare page-number lines: "3", "Page 3", "3 / 12", "- 3 -"
        if re.fullmatch(r"[\-\s]*(?:page\s*)?\d{1,4}(?:\s*[/of]\s*\d{1,4})?[\-\s]*",
                        raw, re.IGNORECASE):
            continue

        output_lines.append(raw_line)

    return "\n".join(output_lines)


def _apply_slide_header_regex(text: str) -> str:
    """
    Hard-coded backstop: remove slide-header lines that the statistical detector
    might miss (e.g. lines that vary slightly per page, or that pypdf merges).

    Applies each pattern in _COMPILED_SLIDE_PATTERNS line-by-line.
    Logs exactly which lines were removed so the server log gives full visibility.
    """
    lines = text.split("\n")
    cleaned_lines: list[str] = []
    removed_count = 0

    for line in lines:
        matched = False
        for pattern in _COMPILED_SLIDE_PATTERNS:
            if pattern.search(line):
                # Only remove lines that are ENTIRELY matched by the pattern
                # (i.e. the pattern covers the whole stripped line).
                stripped = line.strip()
                if pattern.fullmatch(stripped) if hasattr(pattern, 'fullmatch') else pattern.match(stripped):
                    logger.debug("Header regex stripped: %r", stripped[:80])
                    removed_count += 1
                    matched = True
                    break
        if not matched:
            cleaned_lines.append(line)

    if removed_count:
        logger.info(
            "Regex backstop: removed %d header/footer line(s) from PDF text.",
            removed_count,
        )

    cleaned = "\n".join(cleaned_lines)
    # Collapse 3+ consecutive blank lines into a single blank line
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned


# ── Public helpers ────────────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract raw text from all pages of a PDF document.

    Pre-processing pipeline (applied before chunking):
      1. Extract text page-by-page via pypdf.
      2. Detect repeating lines (normalized, so trailing page numbers don't
         prevent matching) → strip them from every page.
      3. Apply slide-header regex backstop for merged/concatenated header text.
      4. Collapse residual blank lines.

    Args:
        pdf_bytes: Raw bytes of the PDF file.

    Returns:
        Full cleaned text as a single string (pages joined with double newlines).

    Raises:
        ValueError: If the PDF cannot be parsed or is empty.
    """
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        raw_pages: list[str] = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                raw_pages.append(text.strip())

        if not raw_pages:
            raise ValueError("PDF contains no extractable text.")

        # Step 1: Detect repeating headers/footers (normalized matching)
        header_norms = _detect_repeating_lines(raw_pages)

        # Step 2: Strip them from each page
        cleaned_pages = [_strip_headers_from_page(p, header_norms) for p in raw_pages]

        # Step 3: Join pages
        full_text = "\n\n".join(p.strip() for p in cleaned_pages if p.strip())

        # Step 4: Regex backstop for slide headers that survived line-based stripping
        full_text = _apply_slide_header_regex(full_text)

        logger.debug(
            "Extracted %d chars from %d PDF page(s) (headers stripped).",
            len(full_text),
            len(raw_pages),
        )
        return full_text

    except ValueError:
        raise
    except Exception as exc:
        logger.exception("Failed to parse PDF.")
        raise ValueError("Invalid or corrupted PDF file.") from exc


def extract_chunks_from_pdf(
    pdf_bytes: bytes,
    mode: str = "paraphrase",
) -> list[str]:
    """
    Extract cleaned text from a PDF and return it as overlapping chunks.

    Mode-aware chunk sizing:
      mode='paraphrase'  → get_paraphrase_chunks() — 700-char chunks
                           ≈ 175-220 T5 tokens, under T5's 256-token hard cap.
      mode='translate'   → get_translation_chunks() — 1200-char chunks
                           ≈ 300 tokens, fits NLLB's 512-token output window.

    Args:
        pdf_bytes: Raw bytes of the PDF file.
        mode:      'paraphrase' (default) or 'translate'.

    Returns:
        List of text chunks ready for parallel processing.

    Raises:
        ValueError: If the PDF cannot be parsed or mode is invalid.
    """
    if mode not in ("paraphrase", "translate"):
        raise ValueError(f"Invalid mode {mode!r}. Use 'paraphrase' or 'translate'.")

    full_text = extract_text_from_pdf(pdf_bytes)

    if mode == "paraphrase":
        chunks = get_paraphrase_chunks(full_text)
        chunk_desc = "700-char paraphrase"
    else:
        chunks = get_translation_chunks(full_text)
        chunk_desc = "1200-char translation"

    logger.info(
        "PDF split into %d %s chunk(s) (header-stripped, ready for pipeline).",
        len(chunks),
        chunk_desc,
    )
    return chunks
