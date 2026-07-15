import io
import logging
from pypdf import PdfReader
from config import MAX_TEXT_LENGTH

logger = logging.getLogger(__name__)

def extract_chunks_from_pdf(pdf_bytes: bytes, max_chunk_size: int = MAX_TEXT_LENGTH) -> list[str]:
    """
    Extracts text from a PDF and splits it into chunks that fit within max_chunk_size.
    Splits on paragraphs or sentences to avoid breaking words.
    """
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        full_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text.append(text)
        
        combined_text = "\n".join(full_text)
        
        # Simple chunking logic
        chunks = []
        current_chunk = ""
        
        paragraphs = [p.strip() for p in combined_text.split('\n') if p.strip()]
        
        for p in paragraphs:
            if len(current_chunk) + len(p) + 1 <= max_chunk_size:
                current_chunk += p + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                if len(p) > max_chunk_size:
                    words = p.split(' ')
                    temp_chunk = ""
                    for w in words:
                        if len(temp_chunk) + len(w) + 1 <= max_chunk_size:
                            temp_chunk += w + " "
                        else:
                            chunks.append(temp_chunk.strip())
                            temp_chunk = w + " "
                    current_chunk = temp_chunk
                else:
                    current_chunk = p + " "
                    
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
            
        return chunks
    except Exception as exc:
        logger.exception("Failed to parse PDF.")
        raise ValueError("Invalid or corrupted PDF file.") from exc
