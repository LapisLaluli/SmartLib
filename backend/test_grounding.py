import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
keys_raw = os.getenv("GEMINI_API_KEYS", "")
API_KEYS = [k.strip() for k in keys_raw.split(",") if k.strip()]

if not API_KEYS:
    print("No API Keys found")
    sys.exit(1)

client = genai.Client(api_key=API_KEYS[0])

print("Testing Google Search Grounding...")
try:
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents="Thời tiết Hà Nội hôm nay thế nào?",
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
    )
    print("\n--- Response ---")
    print(response.text)
    
    # Kiểm tra xem có metadata tìm kiếm không
    if hasattr(response, "candidates") and response.candidates:
        candidate = response.candidates[0]
        if hasattr(candidate, "grounding_metadata") and candidate.grounding_metadata:
            print("\n--- Grounding Metadata Found ---")
            # print(candidate.grounding_metadata)
except Exception as e:
    print("ERROR:", e)
