import sys
sys.path.append('.')
from translation import translate_to_urdu, translate_to_english

try:
    print("EN -> UR:", repr(translate_to_urdu("Hello world, this is a test.")))
    print("UR -> EN:", repr(translate_to_english("ہیلو دنیا، یہ ایک ٹیسٹ ہے۔")))
except Exception as e:
    print("Error:", e)
