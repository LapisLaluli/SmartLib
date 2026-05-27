import json
import os
import random

def load_local_books() -> list[dict]:
    """Đọc tệp history.json và trích xuất tất cả sách độc nhất đã từng tìm thấy."""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    history_path = os.path.join(base_dir, "history.json")
    
    books_dict = {}
    
    if os.path.exists(history_path):
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            for key, value in data.items():
                if key.startswith("chat_"):
                    # Đây là danh sách tin nhắn chat
                    for msg in value:
                        if msg.get("type") in ["books", "suggest_books"] and "books" in msg:
                            for book in msg["books"]:
                                uuid = book.get("uuid") or book.get("url")
                                if uuid and uuid not in books_dict:
                                    books_dict[uuid] = book
        except Exception as e:
            print(f"Lỗi đọc history.json cho recommender: {e}")
            
    return list(books_dict.values())

# Load sách một lần khi khởi động module (đơn giản, hiệu quả)
LOCAL_BOOKS_CATALOG = load_local_books()

def get_local_suggestions(subject: str, size: int = 3) -> list[dict]:
    """Tìm kiếm sách từ danh mục cục bộ theo chủ đề (Content-based filtering)."""
    if not subject or not LOCAL_BOOKS_CATALOG:
        return []
        
    subject_lower = subject.lower().strip()
    
    scored_books = []
    
    for book in LOCAL_BOOKS_CATALOG:
        score = 0
        
        # Chấm điểm dựa trên subjects (chủ đề) của sách
        book_subjects = book.get("subjects", [])
        for s in book_subjects:
            s_lower = s.lower().strip()
            if s_lower == subject_lower:
                score += 10
            elif subject_lower in s_lower or s_lower in subject_lower:
                score += 5
                
        # Chấm điểm dựa trên title (tiêu đề)
        title = book.get("title", "").lower()
        if subject_lower in title:
            score += 3
            
        # Chấm điểm dựa trên abstract (tóm tắt)
        abstract = book.get("abstract", "").lower()
        if subject_lower in abstract:
            score += 1
            
        if score > 0:
            scored_books.append((score, book))
            
    if not scored_books:
        return []
        
    # Sắp xếp theo điểm giảm dần
    scored_books.sort(key=lambda x: x[0], reverse=True)
    
    # Lấy top `size` cuốn (nếu có trùng điểm, thêm một chút random để gợi ý đa dạng hơn)
    top_candidates = [b for s, b in scored_books if s >= scored_books[0][0] * 0.5]
    if len(top_candidates) > size:
        # Xáo trộn nhẹ trong nhóm ứng viên điểm cao để tạo sự đa dạng
        random.shuffle(top_candidates)
        return top_candidates[:size]
        
    return [b for s, b in scored_books[:size]]
