import requests
import random

DSPACE_BASE = "https://dlib.hust.edu.vn/server/api"


def search_documents(keyword: str, author: str = "", publisher: str = "", subject: str = "", collection: str = "", year: str = "", size: int = 5) -> list[dict]:
    """Tìm kiếm tài liệu trên DSpace 7.4 HUST theo từ khóa và các bộ lọc chính xác."""
    try:
        url = f"{DSPACE_BASE}/discover/search/objects"

        # Khởi tạo các tham số cơ bản
        params = {
            "dsoType": "item",
            "size": size
        }

        # Xử lý phần query chung (từ khóa hoặc nhà xuất bản nếu có)
        query_parts = []
        if keyword:
            query_parts.append(keyword)
        if publisher:
            query_parts.append(f"dc.publisher:({publisher})")

        if query_parts:
            params["query"] = " AND ".join(query_parts)
        else:
            params["query"] = "*" # Mặc định lấy tất cả để áp bộ lọc

        # Áp dụng bộ lọc chính xác (DSpace Discovery Filters)
        if author:
            params["f.author"] = f"{author},contains"
        if subject:
            params["f.subject"] = f"{subject},contains"
        if collection:
            # Lọc theo loại tài liệu (Khóa luận, Luận văn, Đồ án, Giáo trình...)
            params["f.itemtype"] = f"{collection},contains"
        if year:
            params["f.dateIssued"] = f"{year},contains"

        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()

        objects = resp.json()["_embedded"]["searchResult"]["_embedded"]["objects"]
        results = []

        for obj in objects:
            item = obj["_embedded"]["indexableObject"]
            meta = item.get("metadata", {})

            title = meta.get("dc.title", [{}])[0].get("value", "Không có tiêu đề")
            authors = [a["value"] for a in meta.get("dc.contributor.author", [])]
            subjects = [s["value"] for s in meta.get("dc.subject", [])]
            abstract = meta.get("dc.description.abstract", [{}])[0].get("value", "")
            date = meta.get("dc.date.issued", [{}])[0].get("value", "")
            doc_type = meta.get("dc.type", [{}])[0].get("value", "Tài liệu")
            handle = item.get("handle", "")
            url_item = f"https://dlib.hust.edu.vn/handle/{handle}" if handle else "https://dlib.hust.edu.vn"

            results.append({
                "title": title,
                "authors": authors[:3],  # Tối đa 3 tác giả
                "subjects": subjects,
                "abstract": (abstract[:250] + "...") if len(abstract) > 250 else abstract,
                "date": date,
                "type": doc_type,
                "url": url_item,
                "uuid": item.get("uuid", "")
            })

        return results

    except Exception as e:
        print(f"[DSpace Error] {e}")
        return []


def get_books_by_subject(subject: str, size: int = 3) -> list[dict]:
    """Gợi ý sách ngẫu nhiên theo chủ đề từ lịch sử tìm kiếm."""
    try:
        url = f"{DSPACE_BASE}/discover/search/objects"
        params = {
            "query": subject,
            "dsoType": "item",
            "size": size + 5  # Lấy thêm để random
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()

        objects = resp.json()["_embedded"]["searchResult"]["_embedded"]["objects"]
        random.shuffle(objects)

        results = []
        for obj in objects[:size]:
            item = obj["_embedded"]["indexableObject"]
            meta = item.get("metadata", {})
            title = meta.get("dc.title", [{}])[0].get("value", "Không rõ")
            authors = [a["value"] for a in meta.get("dc.contributor.author", [])]
            handle = item.get("handle", "")
            url_item = f"https://dlib.hust.edu.vn/handle/{handle}" if handle else "https://dlib.hust.edu.vn"
            results.append({"title": title, "authors": authors[:2], "url": url_item})

        return results

    except Exception as e:
        print(f"[DSpace Subject Error] {e}")
        return []
