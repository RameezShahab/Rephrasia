# ── Base image ────────────────────────────────────────────────────────────────
FROM python:3.11-slim

# ── System dependencies ───────────────────────────────────────────────────────
# tesseract-ocr: Required for ocr.py (Tesseract OCR engine + Urdu language data)
# libgomp1:      OpenMP runtime required by some torch builds
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-urd \
    libtesseract-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# ── Non-root user (required by Hugging Face Spaces) ──────────────────────────
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# ── Working directory ─────────────────────────────────────────────────────────
WORKDIR $HOME/app

# ── Install Python dependencies ───────────────────────────────────────────────
# Copy requirements first to leverage Docker layer caching
COPY --chown=user requirements.txt $HOME/app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# ── Copy application source ───────────────────────────────────────────────────
COPY --chown=user . $HOME/app

# ── Create runtime directories ────────────────────────────────────────────────
RUN mkdir -p static/exports static/audio templates

# ── Run with Gunicorn ─────────────────────────────────────────────────────────
# --workers 1     : Single worker (models are loaded in-process; multiple workers
#                   would each load their own model copy, exhausting RAM)
# --threads 4     : Thread-based concurrency for I/O-bound requests
# --timeout 300   : Allow up to 5 minutes for heavy model inference
# --access-logfile -: Log HTTP requests to stdout for HF Spaces visibility
CMD ["gunicorn", \
     "--bind", "0.0.0.0:7860", \
     "--workers", "1", \
     "--threads", "4", \
     "--timeout", "300", \
     "--access-logfile", "-", \
     "app:app"]