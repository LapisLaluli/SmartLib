import json
import os
from collections import Counter

# Sử dụng bộ nhớ tạm (In-memory) thay vì ghi file vì Render không cho phép ghi vào ổ đĩa.
_MEMORY_HISTORY = {}

def save_search(session_id: str, subjects: list[str]):
    """Lưu các chủ đề đã tìm kiếm của một phiên."""
    if session_id not in _MEMORY_HISTORY:
        _MEMORY_HISTORY[session_id] = []
    _MEMORY_HISTORY[session_id].extend(subjects)
    _MEMORY_HISTORY[session_id] = _MEMORY_HISTORY[session_id][-50:]  # Giữ 50 mục gần nhất

def get_favorite_subject(session_id: str) -> str | None:
    """Trả về chủ đề được tìm nhiều nhất của phiên."""
    subjects = _MEMORY_HISTORY.get(session_id, [])
    if not subjects:
        return None
    return Counter(subjects).most_common(1)[0][0]

def save_chat_message(session_id: str, role: str, content: str, msg_type: str = "text", books: list = None):
    """Lưu tin nhắn chat vào lịch sử."""
    chat_key = f"chat_{session_id}"
    if chat_key not in _MEMORY_HISTORY:
        _MEMORY_HISTORY[chat_key] = []
    
    msg_data = {"role": role, "content": content, "type": msg_type}
    if books:
        msg_data["books"] = books
        
    _MEMORY_HISTORY[chat_key].append(msg_data)
    # Giữ lại 20 tin nhắn gần nhất
    _MEMORY_HISTORY[chat_key] = _MEMORY_HISTORY[chat_key][-20:]

def get_chat_history(session_id: str) -> list:
    """Lấy lịch sử trò chuyện của một phiên."""
    chat_key = f"chat_{session_id}"
    return _MEMORY_HISTORY.get(chat_key, [])
