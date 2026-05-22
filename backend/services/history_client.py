import json
import os
import time
from collections import Counter
from cachetools import TTLCache

# === TTL CACHE: Session tự động xóa sau 2 giờ không hoạt động ===
# maxsize=500: tối đa 500 session cùng lúc
# ttl=7200: mỗi session hết hạn sau 7200 giây (2 tiếng)
_MEMORY_HISTORY = TTLCache(maxsize=500, ttl=7200)

# Lock đơn giản để tránh race condition khi nhiều request cùng session
import threading
_lock = threading.Lock()


def save_search(session_id: str, subjects: list[str]):
    """Lưu các chủ đề đã tìm kiếm của một phiên."""
    with _lock:
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
    with _lock:
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


def get_stats() -> dict:
    """Trả về thống kê bộ nhớ cache (debug)."""
    return {
        "active_sessions": len(_MEMORY_HISTORY),
        "max_sessions": _MEMORY_HISTORY.maxsize,
        "ttl_seconds": _MEMORY_HISTORY.ttl,
    }
