import httpx
import asyncio
import random
import hashlib
import json
from datetime import datetime
from cachetools import TTLCache

# === CONNECTION POOL: Tái sử dụng kết nối TCP thay vì tạo mới mỗi lần ===
_http_client: httpx.AsyncClient | None = None

DSPACE_BASE = "https://dlib.hust.edu.vn/server/api"

# === CACHE: Lưu kết quả tìm kiếm 10 phút, tối đa 200 query ===
_search_cache = TTLCache(maxsize=200, ttl=600)


async def get_http_client() -> httpx.AsyncClient:
    """Lazy-init một AsyncClient duy nhất (connection pooling)."""
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            follow_redirects=True,
        )
    return _http_client


def _cache_key(keyword: str, author: str, publisher: str, subject: str,
               collection: str, year: str, language: str, synonyms: list[str] | None) -> str:
    """Tạo cache key duy nhất từ các tham số tìm kiếm."""
    raw = json.dumps({
        "k": keyword.lower().strip(),
        "a": author, "p": publisher, "s": subject,
        "c": collection, "y": year, "l": language,
        "syn": sorted([s.lower() for s in (synonyms or [])])
    }, ensure_ascii=False, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()


def _score_result(item: dict, keyword: str, synonyms: list[str] = None) -> float:
    """Tính điểm liên quan cho một kết quả dựa trên title, abstract, và năm."""
    score = 0.0
    meta = item.get("metadata", {})

    title = meta.get("dc.title", [{}])[0].get("value", "").lower()
    abstract = meta.get("dc.description.abstract", [{}])[0].get("value", "").lower()
    date = meta.get("dc.date.issued", [{}])[0].get("value", "")

    kw_lower = keyword.lower().strip()
    all_terms = [kw_lower]
    if synonyms:
        all_terms.extend([s.lower() for s in synonyms])

    for term in all_terms:
        # Trọng số cao cho title match
        if term in title:
            score += 10.0
            # Bonus nếu title bắt đầu bằng keyword
            if title.startswith(term):
                score += 3.0
        # Trọng số trung bình cho abstract match
        if term in abstract:
            score += 3.0

    # Bonus cho tài liệu mới hơn (năm gần đây ưu tiên hơn)
    try:
        year = int(date[:4]) if date else 0
        current_year = datetime.now().year
        if year > 0:
            recency = max(0, 5 - (current_year - year))  # 0-5 điểm
            score += recency * 0.5
    except (ValueError, IndexError):
        pass

    return score


def _build_query(keyword: str, synonyms: list[str] = None) -> str:
    """Xây dựng query DSpace với keyword chính và synonyms (OR)."""
    if not keyword:
        return "*"

    parts = [keyword]
    if synonyms:
        parts.extend(synonyms[:4])  # Tối đa 4 synonyms để tránh query quá dài

    # Nối bằng OR để mở rộng phạm vi tìm kiếm
    if len(parts) == 1:
        return parts[0]
    return " OR ".join(f"({p})" for p in parts)


async def _fetch_strategy(client: httpx.AsyncClient, strategy: dict,
                           author: str, publisher: str, subject: str,
                           collection: str, year: str, language: str) -> list[dict]:
    """Thực hiện một chiến lược tìm kiếm đơn lẻ (async)."""
    url = f"{DSPACE_BASE}/discover/search/objects"
    params = {
        "dsoType": "item",
        "size": 20
    }

    # Xử lý phần query
    query_parts = [strategy["query"]]
    if publisher:
        query_parts.append(f"dc.publisher:({publisher})")
    if language:
        lang_code = "en" if any(w in language.lower() for w in ["anh", "english"]) else \
                    "vi" if any(w in language.lower() for w in ["việt", "vietnamese"]) else ""
        if lang_code:
            query_parts.append(f"dc.language.iso:({lang_code})")

    params["query"] = " AND ".join(query_parts) if query_parts else "*"

    # Áp dụng bộ lọc chính xác (DSpace Discovery Filters)
    if author:
        params["f.author"] = f"{author},contains"
    if subject:
        params["f.subject"] = f"{subject},contains"
    if collection:
        params["f.itemtype"] = f"{collection},contains"
    if year:
        params["f.dateIssued"] = f"{year},contains"

    try:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        objects = resp.json()["_embedded"]["searchResult"]["_embedded"]["objects"]
        items = []
        for obj in objects:
            item = obj["_embedded"]["indexableObject"]
            items.append(item)
        print(f"📊 Strategy '{strategy['label']}': tìm thấy {len(items)} kết quả")
        return items
    except Exception as e:
        print(f"[DSpace Strategy '{strategy['label']}' Error] {e}")
        return []


async def search_documents(keyword: str, author: str = "", publisher: str = "",
                           subject: str = "", collection: str = "", year: str = "",
                           language: str = "", size: int = 5,
                           synonyms: list[str] = None) -> list[dict]:
    """Tìm kiếm tài liệu trên DSpace 7.4 HUST với bilingual search, re-ranking, và cache."""
    try:
        # === CHECK CACHE ===
        ck = _cache_key(keyword, author, publisher, subject, collection, year, language, synonyms)
        if ck in _search_cache:
            cached = _search_cache[ck]
            print(f"⚡ Cache HIT cho '{keyword}' — trả {len(cached)} kết quả từ cache")
            return cached[:size]

        # === XÂY DỰNG CHIẾN LƯỢC TÌM KIẾM ===
        strategies = []

        # Tầng 1: Query đầy đủ (keyword + synonyms + filters)
        main_query = _build_query(keyword, synonyms)
        strategies.append({"query": main_query, "label": "full"})

        # Tầng 2: Chỉ keyword gốc (không synonyms)
        if synonyms:
            strategies.append({"query": keyword, "label": "keyword_only"})

        # Tầng 3: Từng từ riêng lẻ (fuzzy)
        words = keyword.split()
        if len(words) > 1:
            fuzzy_query = " OR ".join(f"({w})" for w in words if len(w) > 2)
            if fuzzy_query:
                strategies.append({"query": fuzzy_query, "label": "fuzzy"})

        # === CHẠY SONG SONG TẤT CẢ STRATEGIES ===
        client = await get_http_client()
        tasks = [
            _fetch_strategy(client, s, author, publisher, subject, collection, year, language)
            for s in strategies
        ]
        results_per_strategy = await asyncio.gather(*tasks, return_exceptions=True)

        # === GỘP VÀ LOẠI TRÙNG ===
        all_results = {}  # uuid -> item dict
        for result in results_per_strategy:
            if isinstance(result, Exception):
                print(f"[Strategy Error] {result}")
                continue
            for item in result:
                uuid = item.get("uuid", "")
                if uuid and uuid not in all_results:
                    all_results[uuid] = item

        if not all_results:
            return []

        # === RE-RANKING ===
        scored_items = []
        for uuid, item in all_results.items():
            score = _score_result(item, keyword, synonyms)
            scored_items.append((score, item))

        # Sắp xếp theo điểm giảm dần
        scored_items.sort(key=lambda x: x[0], reverse=True)

        # Lấy tất cả kết quả đã rank
        results = []
        for score, item in scored_items:
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
                "authors": authors[:3],
                "subjects": subjects,
                "abstract": (abstract[:250] + "...") if len(abstract) > 250 else abstract,
                "date": date,
                "type": doc_type,
                "url": url_item,
                "uuid": item.get("uuid", ""),
                "score": round(score, 2)
            })

        # Lưu vào cache (toàn bộ kết quả, không chỉ top N)
        _search_cache[ck] = results
        print(f"✅ Re-ranked: trả về {min(size, len(results))}/{len(all_results)} kết quả (top scores: {[r['score'] for r in results[:3]]})")
        return results[:size]

    except Exception as e:
        print(f"[DSpace Error] {e}")
        return []


async def get_books_by_subject(subject: str, size: int = 3) -> list[dict]:
    """Gợi ý sách ngẫu nhiên theo chủ đề từ lịch sử tìm kiếm."""
    try:
        url = f"{DSPACE_BASE}/discover/search/objects"
        params = {
            "query": subject,
            "dsoType": "item",
            "size": size + 5  # Lấy thêm để random
        }
        client = await get_http_client()
        resp = await client.get(url, params=params)
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
