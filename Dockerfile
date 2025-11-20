# Use Python 3.9 as the base
FROM python:3.9

# 1. Install Tesseract OCR (Required for ocr.py)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Create a new user "user" (Required by Hugging Face)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# 3. Set up working directory
WORKDIR $HOME/app

# 4. Copy files and install dependencies
COPY --chown=user . $HOME/app
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# 5. Create necessary directories for your app
RUN mkdir -p static/exports static/audio

# 6. Run the app using Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:7860", "app:app", "--timeout", "120"]