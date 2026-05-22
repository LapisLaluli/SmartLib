import re
import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load biến môi trường
load_dotenv()

# Cấu hình Gemini (Hỗ trợ xoay vòng nhiều API Key)
keys_raw = os.getenv("GEMINI_API_KEYS", "")
API_KEYS = [k.strip() for k in keys_raw.split(",") if k.strip()]
current_key_index = 0

def get_client():
    if not API_KEYS:
        return None
    return genai.Client(api_key=API_KEYS[current_key_index])

def switch_key():
    global current_key_index
    if len(API_KEYS) > 1:
        current_key_index = (current_key_index + 1) % len(API_KEYS)
        print(f"🔄 Đã chuyển sang API Key thứ {current_key_index + 1}")
        return True
    return False

# === TỪ ĐIỂN MỞ RỘNG TỪ KHÓA (Static Mapping) ===
TERM_MAP = {
    "ai": ["trí tuệ nhân tạo", "artificial intelligence"],
    "ml": ["machine learning", "học máy"],
    "dl": ["deep learning", "học sâu"],
    "nlp": ["natural language processing", "xử lý ngôn ngữ tự nhiên"],
    "cv": ["computer vision", "thị giác máy tính"],
    "iot": ["internet of things", "internet vạn vật"],
    "cntt": ["công nghệ thông tin", "information technology"],
    "csdl": ["cơ sở dữ liệu", "database"],
    "oop": ["lập trình hướng đối tượng", "object oriented programming"],
    "uml": ["unified modeling language"],
    "erp": ["enterprise resource planning", "hoạch định tài nguyên doanh nghiệp"],
    "plc": ["programmable logic controller", "bộ điều khiển lập trình"],
    "cad": ["computer aided design", "thiết kế có sự hỗ trợ của máy tính"],
    "cam": ["computer aided manufacturing"],
    "cnc": ["computer numerical control", "điều khiển số"],
    "bim": ["building information modeling"],
    "gis": ["geographic information system", "hệ thống thông tin địa lý"],
    "5g": ["fifth generation", "mạng 5G"],
    "blockchain": ["chuỗi khối", "công nghệ blockchain"],
    "big data": ["dữ liệu lớn"],
    "data science": ["khoa học dữ liệu"],
    "cloud computing": ["điện toán đám mây"],
    "cyber security": ["an ninh mạng", "an toàn thông tin"],
    "robotics": ["robot học", "kỹ thuật robot"],
    "embedded": ["hệ thống nhúng", "embedded system"],
    "fpga": ["field programmable gate array"],
    "vi điều khiển": ["microcontroller", "vi xử lý"],
    "trí tuệ nhân tạo": ["artificial intelligence", "AI"],
    "học máy": ["machine learning"],
    "học sâu": ["deep learning"],
    "mạng nơ-ron": ["neural network", "mạng thần kinh nhân tạo"],
    "xử lý ảnh": ["image processing", "computer vision"],
    "cơ điện tử": ["mechatronics"],
    "tự động hóa": ["automation", "điều khiển tự động"],
    "năng lượng tái tạo": ["renewable energy"],
    "vật liệu": ["materials science", "khoa học vật liệu"],
    "kinh tế lượng": ["econometrics"],
    "quản trị kinh doanh": ["business administration"],
    "kế toán": ["accounting"],
    "marketing": ["tiếp thị"],
    "machine learning": ["học máy", "ML"],
    "deep learning": ["học sâu"],
    "artificial intelligence": ["trí tuệ nhân tạo", "AI"],
    "natural language processing": ["xử lý ngôn ngữ tự nhiên", "NLP"],
    "computer vision": ["thị giác máy tính"],
    "internet of things": ["internet vạn vật", "IoT"],
    "information technology": ["công nghệ thông tin"],
    "database": ["cơ sở dữ liệu"],
    "neural network": ["mạng nơ-ron", "mạng thần kinh nhân tạo"],
    "image processing": ["xử lý ảnh"],
    "mechatronics": ["cơ điện tử"],
    "automation": ["tự động hóa"],
    "renewable energy": ["năng lượng tái tạo"],
    "data mining": ["khai phá dữ liệu"],
    "software engineering": ["công nghệ phần mềm"],
    "web development": ["phát triển web", "lập trình web"],
}

def expand_keywords(keyword: str) -> list[str]:
    """Mở rộng từ khóa bằng static mapping. Trả về list các từ đồng nghĩa."""
    if not keyword:
        return []
    key = keyword.lower().strip()
    synonyms = []
    # Tìm exact match
    if key in TERM_MAP:
        synonyms.extend(TERM_MAP[key])
    # Tìm partial match — chỉ khi key đủ dài (>= 3 ký tự) và là từ con rõ ràng
    if len(key) >= 3:
        for term, expansions in TERM_MAP.items():
            if term != key and len(term) >= 3:
                # Chỉ match nếu term chứa key hoặc key chứa term, và là từ đứng riêng
                if f" {key}" in f" {term}" or f" {term}" in f" {key}":
                    synonyms.extend(expansions)
    # Loại bỏ trùng lặp, giữ thứ tự
    seen = set()
    unique = []
    for s in synonyms:
        if s.lower() not in seen and s.lower() != key:
            seen.add(s.lower())
            unique.append(s)
    return unique[:5]  # Tối đa 5 synonyms

# Schema định dạng đầu ra của AI
class IntentResponse(BaseModel):
    intent: str = Field(description="Phân loại ý định: 'search' (tìm sách), 'suggest' (gợi ý sách), 'faq' (thông tin thư viện), 'chat' (hỏi đáp/kiến thức chung), 'greeting' (chào hỏi)")
    keyword: str = Field(description="Từ khóa chính để tìm kiếm (tên sách, chủ đề cốt lõi). CHỈ chứa nội dung tìm kiếm, KHÔNG chứa loại tài liệu hay tên tác giả.", default="")
    keyword_vi: str = Field(description="Bản dịch tiếng Việt của keyword nếu keyword là tiếng Anh. Để trống nếu keyword đã là tiếng Việt.", default="")
    keyword_en: str = Field(description="Bản dịch tiếng Anh của keyword nếu keyword là tiếng Việt. Để trống nếu keyword đã là tiếng Anh.", default="")
    author: str = Field(description="Tên tác giả nếu người dùng có nhắc đến (ví dụ: viết bởi Nguyễn Văn A -> Nguyễn Văn A).", default="")
    publisher: str = Field(description="Nhà xuất bản (ví dụ: NXB Trẻ, NXB Bách khoa).", default="")
    subject: str = Field(description="Chủ đề/Thể loại tài liệu (ví dụ: Trí tuệ nhân tạo, Toán cao cấp).", default="")
    collection: str = Field(description="Bộ sưu tập/Loại tài liệu (ví dụ: Luận văn, Đồ án tốt nghiệp, Giáo trình).", default="")
    year: str = Field(description="Năm xuất bản nếu có nhắc đến (ví dụ: 2023, 2024).", default="")
    language: str = Field(description="Ngôn ngữ tài liệu nếu có nhắc đến (ví dụ: tiếng anh, tiếng việt, english).", default="")
    reply: str = Field(description="Câu trả lời của AI dành cho người dùng. Dùng ngôn ngữ tự nhiên, thân thiện và chi tiết. Hướng dẫn từng bước nếu là 'faq'.")

# --- Thêm thông tin nội bộ (Context) cho Thư viện ---
FAQ_CONTEXT = """
# 1. GIỚI THIỆU THƯ VIỆN
- Tên thư viện: Thư viện Tạ Quang Bửu - Đại học Bách khoa Hà Nội (HUST).
- Chức năng, nhiệm vụ: Lưu trữ, quản lý và cung cấp tài nguyên thông tin khoa học công nghệ. Hỗ trợ đắc lực cho công tác giảng dạy, học tập và nghiên cứu khoa học của sinh viên, giảng viên HUST.
- Các dịch vụ cơ bản: Dịch vụ mượn/trả tài liệu (sách giáo trình, tham khảo); Dịch vụ không gian học tập (phòng tự học, phòng học nhóm); Dịch vụ tài liệu điện tử (số hóa); Dịch vụ hỗ trợ tra cứu thông tin khoa học.

# 2. HƯỚNG DẪN NGƯỜI DÙNG
- Làm thẻ thư viện:
  + Đối tượng: Miễn phí hoàn toàn cho sinh viên, học viên, cán bộ HUST.
  + Thủ tục: Chỉ cần mang Thẻ sinh viên hoặc Căn cước công dân đến Quầy Dịch vụ tầng 1. Thẻ sẽ được kích hoạt ngay trong ngày.
- Mượn/trả tài liệu:
  + Mượn sách: Tra cứu mã sách trên hệ thống OPAC, lấy sách tại kho và làm thủ tục mượn tại Quầy dịch vụ (Tầng 1) hoặc máy mượn tự động. Được mượn tối đa 5 cuốn trong 14 ngày.
  + Trả sách: Trả tại Quầy dịch vụ. Nếu quá hạn sẽ bị phạt 2.000 VNĐ/cuốn/ngày.
- Tra cứu tài liệu:
  + Sử dụng Cổng thông tin (dlib.hust.edu.vn) hoặc máy tra cứu tại sảnh. Nhập tên sách/tác giả để lấy "Mã xếp giá" tìm vị trí sách trên kệ.

# 3. HỎI ĐÁP TỰ ĐỘNG (10 CÂU HỎI THƯỜNG GẶP - FAQ)
1. Giờ mở cửa của thư viện là khi nào? -> Thứ 2 – Thứ 6 (8:00 – 21:00); Thứ 7 (8:00 – 17:00); Chủ nhật và ngày lễ nghỉ.
2. Thư viện nằm ở đâu? -> Tòa nhà Tạ Quang Bửu, Số 1 Đại Cồ Việt, Hai Bà Trưng, Hà Nội.
3. Sinh viên trường ngoài có được vào thư viện không? -> Có, khách ngoài trường có thể mua vé ngày hoặc đăng ký thẻ đọc ngoài giờ.
4. Mật khẩu wifi của thư viện là gì? -> Tên wifi: "HUST_Library" - Mật khẩu: "thuviendhbk".
5. Làm sao để đặt phòng học nhóm? -> Bạn cần đăng ký trước qua website thư viện và sử dụng tại Tầng 4.
6. Mất sách thư viện thì phải làm sao? -> Báo ngay cho thủ thư tại Quầy tầng 1 để làm thủ tục đền bù sách mới hoặc đóng tiền theo quy định.
7. Có được mang đồ ăn, thức uống vào thư viện không? -> Tuyệt đối cấm mang đồ ăn. Chỉ được mang nước lọc đựng trong bình/chai có nắp đậy kín.
8. Quá hạn trả sách bị phạt bao nhiêu tiền? -> Mức phạt là 2.000 VNĐ cho mỗi cuốn sách bị quá hạn 1 ngày.
9. Thư viện có sách ngoại văn không? -> Có, sách ngoại văn và tạp chí quốc tế chủ yếu tập trung ở kho Tầng 4 và Tầng 5.
10. Làm sao để tải tài liệu điện tử (PDF)? -> Truy cập trang dlib.hust.edu.vn, đăng nhập bằng tài khoản email sinh viên HUST (@hust.edu.vn) để đọc và tải tài liệu số.

# 4. KÊNH THÔNG TIN CHÍNH THỨC (LIÊN HỆ)
- Website Đại học Bách khoa Hà Nội: [hust.edu.vn](https://hust.edu.vn)
- Facebook Đại học Bách khoa Hà Nội: [facebook.com/dhbkhanoi](https://www.facebook.com/dhbkhanoi)
- Website Thư viện Tạ Quang Bửu: [library.hust.edu.vn](https://library.hust.edu.vn)
- Facebook Thư viện Tạ Quang Bửu: [facebook.com/libraryhust](https://www.facebook.com/libraryhust)
- Cổng tài liệu số: [dlib.hust.edu.vn](https://dlib.hust.edu.vn)
"""

# Instruction hệ thống thay vì prompt cộng gộp
SYSTEM_INSTRUCTION = f"""
Bạn là SmartLib AI, trợ lý ảo thông minh, thân thiện và hiểu biết của thư viện Tạ Quang Bửu (Đại học Bách khoa Hà Nội - HUST).
Nhiệm vụ của bạn là đọc hiểu tin nhắn của người dùng, xác định ý định (intent), trích xuất từ khóa (nếu có) và tạo câu trả lời phù hợp nhất.

Dưới đây là thông tin nội bộ của thư viện để bạn tham khảo khi trả lời:
{FAQ_CONTEXT}

# QUY TRÌNH TƯ DUY & PHÂN LOẠI Ý ĐỊNH:

1. Chào hỏi ("greeting"):
   - Khi người dùng chào hỏi.
   - Reply: Chào lại thân thiện và giới thiệu ngắn gọn khả năng của bạn.

2. Tìm kiếm sách/tài liệu ("search"):
   - Dùng khi người dùng CÓ NHU CẦU lấy danh sách sách/tài liệu.
   - **QUAN TRỌNG VỀ KEYWORD**: Chỉ đặt NỘI DUNG TÌM KIẾM vào keyword. KHÔNG gộp loại tài liệu (luận văn, đồ án, giáo trình) vào keyword → đặt vào collection.
   - **keyword_vi**: Nếu keyword là tiếng Anh, dịch sang tiếng Việt. Ví dụ: keyword="machine learning" → keyword_vi="học máy".
   - **keyword_en**: Nếu keyword là tiếng Việt, dịch sang tiếng Anh. Ví dụ: keyword="trí tuệ nhân tạo" → keyword_en="artificial intelligence".
   - Reply: Giới thiệu ngắn gọn và dẫn dắt "Dưới đây là một số tài liệu tôi tìm thấy:".

3. Hỏi thông tin thư viện ("faq"):
   - Dùng khi hỏi về giờ mở cửa, địa chỉ, cách làm thẻ, wifi, mượn trả sách...
   - Reply: Dựa vào [Thông tin nội bộ], trả lời chính xác, rõ ràng. Có thể dùng gạch đầu dòng, format rõ ràng (Bước 1, Bước 2...).

4. Gợi ý sách ("suggest"):
   - Dùng khi yêu cầu gợi ý chung chung, không có từ khóa cụ thể.
   - Reply: Nói lời động viên và dẫn dắt "Dựa trên sở thích của bạn, đây là những quyển sách tôi gợi ý:".

5. Trò chuyện kiến thức/Hỏi đáp chung ("chat"):
   - Dùng khi hỏi về kiến thức, tâm sự, hoặc các câu hỏi không thuộc các loại trên.
   - Reply: Nhập vai chuyên gia, trả lời đầy đủ và trực quan.

# VÍ DỤ PHÂN TÁCH (FEW-SHOT):

Input: "tìm luận văn về học máy của tác giả Nguyễn Văn A năm 2022"
→ intent="search", keyword="học máy", keyword_en="machine learning", keyword_vi="", author="Nguyễn Văn A", collection="Luận văn", year="2022"

Input: "tìm sách machine learning"
→ intent="search", keyword="machine learning", keyword_vi="học máy", keyword_en="", collection=""

Input: "có đồ án tốt nghiệp nào về IoT không?"
→ intent="search", keyword="IoT", keyword_vi="internet vạn vật", keyword_en="internet of things", collection="Đồ án tốt nghiệp"

Input: "tìm giáo trình toán cao cấp"
→ intent="search", keyword="toán cao cấp", keyword_en="advanced mathematics", keyword_vi="", collection="Giáo trình"

Input: "sách về AI viết bằng tiếng anh"
→ intent="search", keyword="AI", keyword_vi="trí tuệ nhân tạo", keyword_en="artificial intelligence", language="tiếng anh"

# QUAN TRỌNG:
- Bạn LUÔN tuân thủ đúng định dạng JSON được yêu cầu.
- Nếu câu hỏi không thể trả lời hoặc vô nghĩa, chọn "chat" và xin lỗi lịch sự.
- LUÔN cung cấp keyword_vi hoặc keyword_en (bản dịch song ngữ) khi intent là "search".
"""

def build_messages(text: str, chat_history: list = None) -> list:
    """Chuyển đổi lịch sử chat thành định dạng chuẩn của Gemini."""
    messages = []
    if chat_history:
        for msg in chat_history:
            role = "user" if msg["role"] == "user" else "model"
            content = msg.get("content")
            if not content:
                continue
            messages.append({"role": role, "parts": [{"text": content}]})
    messages.append({"role": "user", "parts": [{"text": text}]})
    return messages

def fallback_intent(text: str) -> dict:
    """Hệ thống Fallback Rule-based truyền thống."""
    text_lower = text.lower().strip()
    
    FAQ_MAP = {
        ("giờ", "m mở cửa", "đóng cửa", "mấy giờ", "hoạt động"): "🕐 Thư viện mở cửa:\n• Thứ 2 – Thứ 6: 8:00 – 21:00\n• Thứ 7: 8:00 – 17:00\n• Chủ nhật: Nghỉ",
        ("địa chỉ", "ở đâu", "chỗ nào", "vị trí"): "📍 Địa chỉ: Tòa nhà Tạ Quang Bửu, Số 1 Đại Cồ Việt, Hai Bà Trưng, Hà Nội.\n🌐 Website: [library.hust.edu.vn](https://library.hust.edu.vn)\n📱 Fanpage: [fb.com/libraryhust](https://www.facebook.com/libraryhust)",
        ("thẻ thư viện", "làm thẻ", "đăng ký"): "📋 Làm thẻ thư viện (Miễn phí):\n1. Mang Thẻ SV/CCCD và ảnh 3x4\n2. Đến quầy dịch vụ tầng 1\n3. Lấy thẻ trong ngày",
        ("mượn sách", "trả sách", "quá hạn"): "📚 Mượn tối đa 5 cuốn/lần, thời hạn 14 ngày. Quá hạn phạt 2.000 VNĐ/cuốn/ngày.",
        ("wifi", "mạng", "internet"): "📶 Wifi thư viện:\n• Tên: HUST_Library\n• Pass: thuviendhbk",
        ("phòng tự học", "phòng học", "học nhóm"): "🏢 Phòng tự học ở tầng 3, 4, 5. Tầng 4 có phòng học nhóm (đăng ký qua web).",
        ("website", "facebook", "fanpage", "liên hệ", "kết nối"): "🔗 Các kênh thông tin chính thức:\n• Website HUST: [hust.edu.vn](https://hust.edu.vn)\n• Facebook HUST: [fb.com/dhbkhanoi](https://www.facebook.com/dhbkhanoi)\n• Website Thư viện: [library.hust.edu.vn](https://library.hust.edu.vn)\n• Facebook Thư viện: [fb.com/libraryhust](https://www.facebook.com/libraryhust)"
    }

    if any(w in text_lower for w in ("hi", "hello", "xin chào", "chào")):
        return {"intent": "greeting", "keyword": "", "answer": "Chào bạn! Hiện tại kết nối AI đang gián đoạn, nhưng tôi vẫn có thể tra cứu sách và thông tin cơ bản."}

    for keywords, answer in FAQ_MAP.items():
        if any(k in text_lower for k in keywords):
            return {"intent": "faq", "keyword": "", "answer": answer}

    if any(trigger in text_lower for trigger in ["tìm", "sách về", "tài liệu"]):
        keyword = re.sub(r"^(tìm|sách về|tài liệu về)\s+", "", text_lower)
        kw = keyword or text
        synonyms = expand_keywords(kw)
        return {
            "intent": "search", "keyword": kw,
            "keyword_vi": "", "keyword_en": "",
            "synonyms": synonyms,
            "author": "", "publisher": "", "subject": "",
            "collection": "", "year": "", "language": "",
            "answer": f"Đang tìm kiếm tài liệu về '{kw}'..."
        }

    return {
        "intent": "chat", 
        "keyword": "", "keyword_vi": "", "keyword_en": "", "synonyms": [],
        "author": "", "publisher": "", "subject": "",
        "collection": "", "year": "", "language": "",
        "answer": "⚠️ Xin lỗi, hệ thống AI đang bảo trì. Tuy nhiên, bạn vẫn có thể dùng các lệnh như:\n• *tìm sách [tên sách]*\n• *giờ mở cửa*\n• *làm thẻ thư viện*"
    }

async def detect_intent(text: str, chat_history: list = None) -> dict:
    """Xác định ý định với Gemini Structured Output & System Instruction (Async)."""
    max_retries = len(API_KEYS)
    for attempt in range(max_retries):
        client = get_client()
        if not client:
            break

        try:
            messages = build_messages(text, chat_history)

            # Bước 1: Phân loại Ý định (Cần JSON, KHÔNG được bật Google Search cùng lúc)
            response = await client.aio.models.generate_content(
                model='gemini-2.5-flash',
                contents=messages,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    response_schema=IntentResponse,
                    temperature=0.7
                )
            )
            
            raw_text = response.text.strip() if response.text else ""
            
            if raw_text:
                result = json.loads(raw_text)
                intent = result.get("intent", "chat")
                keyword = result.get("keyword", "")
                keyword_vi = result.get("keyword_vi", "")
                keyword_en = result.get("keyword_en", "")
                author = result.get("author", "")
                publisher = result.get("publisher", "")
                subject = result.get("subject", "")
                collection = result.get("collection", "")
                year = result.get("year", "")
                language = result.get("language", "")
                answer = result.get("reply", "Tôi có thể giúp gì cho bạn?")

                # Mở rộng từ khóa bằng static mapping
                synonyms = expand_keywords(keyword)
                # Bổ sung keyword song ngữ từ AI vào synonyms nếu chưa có
                for kw in [keyword_vi, keyword_en]:
                    if kw and kw.lower() not in [s.lower() for s in synonyms] and kw.lower() != keyword.lower():
                        synonyms.insert(0, kw)
                
                print(f"🔍 Intent: {intent} | Keyword: {keyword} | VI: {keyword_vi} | EN: {keyword_en} | Synonyms: {synonyms}")
                
                # Bước 2: Nếu cần trả lời thông tin (faq/chat), kích hoạt Google Search Grounding riêng biệt
                if intent in ["faq", "chat"]:
                    try:
                        grounded_response = await client.aio.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=f"Dựa trên tìm kiếm thời gian thực, hãy trả lời câu hỏi sau một cách chi tiết và chính xác nhất (ưu tiên thông tin về thư viện Đại học Bách khoa Hà Nội - HUST nếu có): {text}",
                            config=types.GenerateContentConfig(
                                temperature=0.5,
                                tools=[types.Tool(google_search=types.GoogleSearch())]
                            )
                        )
                        if grounded_response.text:
                            answer = grounded_response.text.strip()
                    except Exception as search_err:
                        print(f"⚠️ Grounding Error (Dùng câu trả lời Offline): {search_err}")

                return {
                    "intent": intent,
                    "keyword": keyword,
                    "keyword_vi": keyword_vi,
                    "keyword_en": keyword_en,
                    "synonyms": synonyms,
                    "author": author,
                    "publisher": publisher,
                    "subject": subject,
                    "collection": collection,
                    "year": year,
                    "language": language,
                    "answer": answer
                }
            
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "quota" in error_str or "limit" in error_str:
                print(f"⚠️ Key hiện tại lỗi/hết quota: {e}")
                if switch_key():
                    continue
                else:
                    break
            else:
                print(f"⚠️ Gemini Error: {e}")
                break

    # Nếu tất cả các keys đều lỗi hoặc AI lỗi chung
    return fallback_intent(text)

async def summarize_books(keyword: str, books: list) -> str:
    """Sử dụng AI để tóm tắt 2-3 tài liệu đầu tiên tìm được (Async)."""
    if not books:
        return f"Rất tiếc, tôi không tìm thấy tài liệu nào về '{keyword}'."
        
    client = get_client()
    if not client:
        return f"📚 Tôi đã tìm thấy một số tài liệu về **\"{keyword}\"**. Bạn có thể xem danh sách bên dưới:"
        
    # Chuẩn bị context tóm tắt
    context = ""
    for idx, b in enumerate(books[:3]):
        context += f"{idx+1}. Tiêu đề: {b.get('title')}. Tác giả: {', '.join(b.get('authors', []))}. Tóm tắt: {b.get('abstract', 'Không có')}\n"
        
    prompt = f"Bạn là một thủ thư thư viện thông minh. Người dùng vừa tìm kiếm từ khóa '{keyword}'. Dưới đây là top {len(books[:3])} tài liệu hàng đầu:\n{context}\nViết 1 đoạn văn ngắn gọn (tối đa 3 dòng) bằng tiếng Việt để giới thiệu khái quát nội dung nổi bật của các cuốn sách này thật hấp dẫn. KHÔNG LIỆT KÊ LẠI TIÊU ĐỀ SÁCH VÀ TÁC GIẢ vì chúng tôi đã hiển thị trên giao diện rồi."
    
    try:
        response = await client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.5)
        )
        if response.text:
            return response.text.strip()
    except Exception as e:
        print(f"⚠️ Lỗi summarize_books: {e}")
        
    return f"📚 Dưới đây là các tài liệu nổi bật nhất về **\"{keyword}\"** mà tôi tìm thấy:"
