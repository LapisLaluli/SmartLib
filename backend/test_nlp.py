import sys
import os

# Thêm thư mục hiện tại vào sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.nlp import detect_intent

print("Testing detect_intent...")
try:
    res = detect_intent("Xin chào, bạn là ai?")
    print("SUCCESS:", res)
except Exception as e:
    print("ERROR:", e)
