import json
import os
from collections import Counter

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "..", "history.json")


def _load_history() -> dict:
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_history(data: dict):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_search(session_id: str, subjects: list[str]):
    """Lưu các chủ đề đã tìm kiếm của một phiên."""
    data = _load_history()
    if session_id not in data:
        data[session_id] = []
    data[session_id].extend(subjects)
    data[session_id] = data[session_id][-50:]  # Giữ 50 mục gần nhất
    _save_history(data)


def get_favorite_subject(session_id: str) -> str | None:
    """Trả về chủ đề được tìm nhiều nhất của phiên."""
    data = _load_history()
    subjects = data.get(session_id, [])
    if not subjects:
        return None
    return Counter(subjects).most_common(1)[0][0]


def save_chat_message(session_id: str, role: str, content: str, msg_type: str = "text", books: list = None):
    """Lưu tin nhắn chat vào lịch sử."""
    data = _load_history()
    chat_key = f"chat_{session_id}"
    if chat_key not in data:
        data[chat_key] = []
    
    msg_data = {"role": role, "content": content, "type": msg_type}
    if books:
        msg_data["books"] = books
        
    data[chat_key].append(msg_data)
    # Giữ lại 20 tin nhắn gần nhất
    data[chat_key] = data[chat_key][-20:]
    _save_history(data)


def get_chat_history(session_id: str) -> list:
    """Lấy lịch sử trò chuyện của một phiên."""
    data = _load_history()
    chat_key = f"chat_{session_id}"
    return data.get(chat_key, [])
