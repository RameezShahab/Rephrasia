"""
grammar_checker.py — Grammar checking using the existing T5 paraphrase model.

Strategy:
  - Uses the same T5 model (humarin/chatgpt_paraphraser_on_T5_base) as a
    grammar-correction proxy: the model naturally corrects grammatical errors
    when paraphrasing.
  - Computes basic readability and difference metrics to produce scores.
  - Generates issue annotations by diffing original vs. corrected text.

For a production-grade grammar checker, consider integrating:
  - LanguageTool API (rule-based, multilingual)
  - GECToR model (specialized for grammatical error correction)
"""

from __future__ import annotations

import logging
import difflib
from typing import List, Dict, Any

from model import paraphrase

logger = logging.getLogger(__name__)


def check_grammar(text: str) -> Dict[str, Any]:
    """
    Check grammar by running text through the T5 paraphraser and diffing
    the result against the original.

    Returns:
        {
            "corrected_text": str,
            "scores": {"grammar": int, "readability": int, "clarity": int},
            "issues": [{"type": str, "original": str, "suggestion": str, "position": dict}],
            "issue_count": int,
        }
    """
    try:
        paraphrased = paraphrase(text)
        corrected = paraphrased[0] if paraphrased else text
    except Exception as exc:
        logger.exception("Grammar check model inference failed.")
        raise RuntimeError("Grammar check failed") from exc

    issues = _diff_issues(text, corrected)
    scores = _compute_scores(text, corrected, issues)

    return {
        "corrected_text": corrected,
        "scores": scores,
        "issues": issues,
        "issue_count": len(issues),
    }


def _diff_issues(original: str, corrected: str) -> List[Dict[str, Any]]:
    """
    Generate a list of grammar issues by diffing original vs corrected text.

    Uses SequenceMatcher to find changed blocks and classifies them.
    """
    issues: List[Dict[str, Any]] = []
    matcher = difflib.SequenceMatcher(None, original, corrected)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue

        orig_fragment = original[i1:i2]
        corr_fragment = corrected[j1:j2]

        # Classify the type of issue
        issue_type = _classify_issue(orig_fragment, corr_fragment)

        issues.append({
            "type": issue_type,
            "original": orig_fragment,
            "suggestion": corr_fragment,
            "position": {"start": i1, "end": i2},
        })

    return issues


def _classify_issue(original: str, suggestion: str) -> str:
    """Heuristically classify a diff as grammar, punctuation, style, or clarity."""
    punct_chars = set(".,;:!?'\"-()[]{}…–—")

    # Pure punctuation change
    if all(c in punct_chars or c.isspace() for c in original + suggestion):
        return "punctuation"

    # Word order or small word replacement → grammar
    orig_words = set(original.lower().split())
    sugg_words = set(suggestion.lower().split())
    if orig_words & sugg_words:  # Overlapping words → structural change
        return "grammar"

    # Completely different phrasing → style
    if len(original.split()) >= 3 and len(suggestion.split()) >= 3:
        return "style"

    return "clarity"


def _compute_scores(
    original: str, corrected: str, issues: List[Dict[str, Any]]
) -> Dict[str, int]:
    """
    Compute grammar, readability, and clarity scores.

    Scoring is heuristic-based:
      - grammar:     100 minus penalty per issue
      - readability: Based on average sentence length
      - clarity:     Based on similarity ratio between original and corrected
    """
    # Grammar: start at 100, deduct per issue
    issue_penalty = min(len(issues) * 8, 60)
    grammar_score = max(100 - issue_penalty, 40)

    # Readability: based on average sentence length (ideal: 15-20 words/sentence)
    sentences = [s.strip() for s in corrected.replace("!", ".").replace("?", ".").split(".") if s.strip()]
    if sentences:
        avg_words = sum(len(s.split()) for s in sentences) / len(sentences)
        if 10 <= avg_words <= 25:
            readability_score = 90 + min(int(avg_words), 10)
        elif avg_words < 10:
            readability_score = max(70, int(avg_words * 8))
        else:
            readability_score = max(60, 100 - int((avg_words - 25) * 2))
    else:
        readability_score = 75

    # Clarity: based on text similarity (high similarity = minor changes = good input)
    similarity = difflib.SequenceMatcher(None, original, corrected).ratio()
    clarity_score = max(50, min(100, int(similarity * 100)))

    return {
        "grammar": min(grammar_score, 100),
        "readability": min(readability_score, 100),
        "clarity": min(clarity_score, 100),
    }
