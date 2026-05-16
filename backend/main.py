from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from services.nlp import detect_intent
from services.dspace_client import search_documents, get_books_by_subject
from services.history_client import save_search, get_favorite_subject, save_chat_message, get_chat_history
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
    
    # Lấy lịch sử trò chuyện để AI có ngữ cảnh
    chat_history = get_chat_history(req.session_id)
    result = detect_intent(req.message, chat_history)
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
        keyword = result.get("keyword")
        if not keyword:
            keyword = req.message
        books = search_documents(keyword, size=6)

        if not books:
            response_data = ChatResponse(
                type="text",
                text=f"😔 Xin lỗi, tôi không tìm thấy tài liệu nào về **\"{keyword}\"**.\nBạn thử từ khóa khác nhé!"
            )
        else:
            # Lưu chủ đề vào lịch sử
            all_subjects = [s for b in books for s in b.get("subjects", [])]
            if all_subjects:
                save_search(req.session_id, all_subjects)

            # Sử dụng câu trả lời giải thích từ AI nếu có
            ai_text = result.get("answer")
            display_text = ai_text if ai_text else f"📚 Tìm thấy tài liệu về **\"{keyword}\"**:"

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
            books = get_books_by_subject(subject, size=3)
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



class BotStarRequest(BaseModel):
    query: str
    session_id: str = "botstar_default"


@app.post("/botstar/search")
async def botstar_search(req: BotStarRequest):
    """Endpoint chuyên dụng hỗ trợ BotStar gọi API tìm sách."""
    # Nhờ AI phân tích intent và rút trích từ khóa
    result = detect_intent(req.query)
    intent = result.get("intent")
    
    if intent == "search":
        keyword = result.get("keyword") or req.query
        books = search_documents(keyword, size=3) # Lấy top 3 cuốn chất lượng
        
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


if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8001))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
