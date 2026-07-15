import requests
from PIL import Image, ImageDraw
import io

# 1. Create a dummy image with some text
img = Image.new('RGB', (400, 100), color=(255, 255, 255))
d = ImageDraw.Draw(img)
# Draw text (default font)
d.text((10, 40), "HELLO WORLD", fill=(0, 0, 0))

# 2. Save to bytes
buf = io.BytesIO()
img.save(buf, format='PNG')
buf.seek(0)

# 3. POST to OCR endpoint
url = "http://127.0.0.1:7860/api/ocr"
files = {'image': ('test.png', buf, 'image/png')}
data = {'language': 'eng', 'preprocess': 'false'}

print("Sending request to OCR server...")
try:
    response = requests.post(url, files=files, data=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")
