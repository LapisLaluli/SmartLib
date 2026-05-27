from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from services.nlp import detect_intent, summarize_books
from services.dspace_client import search_documents, get_books_by_subject
from services.history_client import save_search, get_favorite_subject, save_chat_message, get_chat_history, get_stats
import uvicorn

app = FastAPI(title="SmartLib AI Backend")

# Cho phép frontend gọi API (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    type: str          # "text" | "books" | "suggest_books"
    text: str
    books: list = []


@app.get("/history/{session_id}")
async def get_history(session_id: str):
    """Lấy lịch sử trò chuyện của phiên."""
    return get_chat_history(session_id)

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Endpoint chính xử lý tin nhắn từ người dùng."""
    try:
        # Lấy lịch sử trò chuyện để AI có ngữ cảnh
        chat_history = get_chat_history(req.session_id)
        result = await detect_intent(req.message, chat_history)
        intent = result["intent"]

        response_data = None

        # --- Intent: Chào hỏi ---
        if intent == "greeting":
            ai_text = result.get("answer")
            display_text = ai_text if ai_text and ai_text != "Tôi có thể giúp gì cho bạn?" else "👋 Xin chào! Tôi là **SmartLib AI** – trợ lý thư viện thông minh.\n\nBạn có thể:\n• 🔍 Tìm tài liệu: *\"tìm sách về trí tuệ nhân tạo\"*\n• 💡 Gợi ý sách: *\"gợi ý sách hay cho tôi\"*\n• ❓ Hỏi thông tin: *\"giờ mở cửa\"*, *\"địa chỉ thư viện\"*"
            
            response_data = ChatResponse(
                type="text",
                text=display_text
            )

        # --- Intent: FAQ ---
        elif intent == "faq":
            response_data = ChatResponse(type="text", text=result["answer"])

        # --- Intent: Tìm tài liệu ---
        elif intent == "search":
            keyword = result.get("keyword", "")
            author = result.get("author", "")
            publisher = result.get("publisher", "")
            subject = result.get("subject", "")
            collection = result.get("collection", "")
            year = result.get("year", "")
            language = result.get("language", "")
            synonyms = result.get("synonyms", [])

            if not any([keyword, author, publisher, subject, collection, year, language]):
                keyword = req.message

            books = await search_documents(
                keyword=keyword,
                author=author,
                publisher=publisher,
                subject=subject,
                collection=collection,
                year=year,
                language=language,
                size=6,
                synonyms=synonyms
            )

            if not books:
                dlib_search_url = f"https://dlib.hust.edu.vn/discover?query={keyword}"
                response_data = ChatResponse(
                    type="text",
                    text=f"😔 Xin lỗi, hệ thống không tìm thấy tài liệu nào về **\"{keyword}\"**.\n\n🌐 Bạn có thể thử tìm kiếm trực tiếp trên cổng tài liệu số của thư viện tại đây: [Truy cập dlib.hust.edu.vn]({dlib_search_url})"
                )
            else:
                # Lưu chủ đề vào lịch sử
                all_subjects = [s for b in books for s in b.get("subjects", [])]
                if all_subjects:
                    save_search(req.session_id, all_subjects)

                # Sử dụng câu trả lời giải thích từ AI nếu có hoặc tóm tắt AI
                ai_text = result.get("answer")
                if not ai_text or ai_text.startswith("Đang tìm kiếm") or ai_text == "Tôi có thể giúp gì cho bạn?":
                    display_text = await summarize_books(keyword or req.message, books)
                else:
                    display_text = ai_text

                response_data = ChatResponse(
                    type="books",
                    text=display_text,
                    books=books
                )

        # --- Intent: Gợi ý sách ---
        elif intent == "suggest":
            subject = get_favorite_subject(req.session_id)

            if not subject:
                response_data = ChatResponse(
                    type="text",
                    text="💬 Bạn chưa có lịch sử tìm kiếm. Hãy tìm vài tài liệu trước để tôi gợi ý cho bạn nhé!"
                )
            else:
                from services.recommender import get_local_suggestions
                books = get_local_suggestions(subject, size=3)
                
                # Nếu local không đủ kết quả, gọi thêm API để bù vào
                if len(books) < 3:
                    needed = 3 - len(books)
                    api_books = await get_books_by_subject(subject, size=needed)
                    existing_urls = {b.get("url") for b in books}
                    for ab in api_books:
                        if ab.get("url") not in existing_urls:
                            books.append(ab)

                # Sử dụng câu trả lời giải thích từ AI nếu có
                ai_text = result.get("answer")
                display_text = ai_text if ai_text else f"✨ Dựa trên lịch sử của bạn, tôi gợi ý tài liệu về chủ đề **\"{subject}\"**:"

                response_data = ChatResponse(
                    type="suggest_books",
                    text=display_text,
                    books=books
                )

        # --- Intent: Chat/General (Sử dụng AI phản hồi) ---
        elif intent == "chat":
            response_data = ChatResponse(type="text", text=result.get("answer", "Tôi có thể giúp gì cho bạn?"))

        # --- Fallback ---
        else:
            response_data = ChatResponse(
                type="text",
                text="🤔 Tôi chưa hiểu câu hỏi của bạn. Thử nói *\"tìm sách về [chủ đề]\"* hoặc hỏi *\"giờ mở cửa\"* nhé!"
            )

        # --- Lưu lịch sử trò chuyện trước khi trả về ---
        save_chat_message(req.session_id, "user", req.message)
        save_chat_message(req.session_id, "bot", response_data.text, response_data.type, response_data.books)

        return response_data
    except Exception as e:
        print(f"❌ Lỗi xử lý chat: {e}")
        return ChatResponse(
            type="text",
            text=f"⚙️ Hệ thống đang gặp sự cố và không thể trả lời ngay lúc này.\n\n🌐 Bạn có thể tra cứu thông tin và tài liệu trực tiếp trên trang web của Thư viện Tạ Quang Bửu tại: [dlib.hust.edu.vn](https://dlib.hust.edu.vn/)"
        )



class BotStarRequest(BaseModel):
    query: str
    session_id: str = "botstar_default"


@app.post("/botstar/search")
async def botstar_search(req: BotStarRequest):
    """Endpoint chuyên dụng hỗ trợ BotStar gọi API tìm sách."""
    # Nhờ AI phân tích intent và rút trích từ khóa
    result = await detect_intent(req.query)
    intent = result.get("intent")
    
    if intent == "search":
        keyword = result.get("keyword", "")
        author = result.get("author", "")
        publisher = result.get("publisher", "")
        subject = result.get("subject", "")
        collection = result.get("collection", "")
        year = result.get("year", "")
        language = result.get("language", "")
        synonyms = result.get("synonyms", [])

        if not any([keyword, author, publisher, subject, collection, year, language]):
            keyword = req.query

        books = await search_documents(
            keyword=keyword,
            author=author,
            publisher=publisher,
            subject=subject,
            collection=collection,
            year=year,
            language=language,
            size=3,
            synonyms=synonyms
        ) # Lấy top 3 cuốn chất lượng
        
        if not books:
            return {
                "found": False,
                "message": f"😔 Rất tiếc, thư viện hiện tại chưa có tài liệu phù hợp về **\"{keyword}\"**."
            }
            
        # Chuyển dữ liệu sách thành mảng phẳng, đơn giản để hiển thị trên BotStar
        book_list = []
        for b in books:
            book_list.append({
                "title": b.get("title", "Không rõ tiêu đề"),
                "author": ", ".join(b.get("authors", ["Ẩn danh"])),
                "url": b.get("url", "https://library.hust.edu.vn"),
                "summary": (b.get("abstract")[:90] + "...") if b.get("abstract") else "Tài liệu tham khảo số."
            })
            
        return {
            "found": True,
            "keyword": keyword,
            "message": f"📚 Dưới đây là một số tài liệu hàng đầu về chủ đề **\"{keyword}\"** mà tôi tìm thấy:",
            "books": book_list
        }
        
    # Với các câu hỏi FAQ/Trò chuyện, gửi thẳng phản hồi từ AI
    return {
        "found": False,
        "message": result.get("answer", "SmartLib AI chưa hiểu rõ ý của bạn, vui lòng thử lại nhé!")
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "SmartLib AI"}


@app.get("/stats")
def stats():
    """Endpoint monitor: trạng thái cache và bộ nhớ."""
    from services.dspace_client import _search_cache
    return {
        "session": get_stats(),
        "search_cache": {
            "cached_queries": len(_search_cache),
            "max_queries": _search_cache.maxsize,
            "ttl_seconds": _search_cache.ttl,
        }
    }


if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8001))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
