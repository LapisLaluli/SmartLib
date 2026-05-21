# SmartLib AI — Trợ Lý Thư Viện Thông Minh HUST

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Gemini](https://img.shields.io/badge/Gemini%20AI-8E75C2?style=flat&logo=google-gemini)](https://deepmind.google/technologies/gemini/)
[![DSpace 7.4](https://img.shields.io/badge/DSpace-7.4-blue?style=flat)](https://dlib.hust.edu.vn)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**SmartLib AI** là hệ thống chatbot trợ lý ảo thông minh được thiết kế chuyên biệt cho **Thư viện Tạ Quang Bửu - Đại học Bách khoa Hà Nội (HUST)**. Hệ thống kết hợp sức mạnh của Mô hình Ngôn ngữ Lớn (Gemini 2.5 Flash) và Dữ liệu Tài nguyên số trực tiếp từ cổng API DSpace 7.4 của nhà trường để mang lại trải nghiệm tra cứu tài liệu học thuật và hỗ trợ thủ tục thư viện bằng tiếng Việt tự nhiên và trực quan nhất.

---

## 🌟 Tính Năng Nổi Bật

- **Tìm kiếm tài liệu thông minh (Semantic Search)**: Nhận diện ý định tự nhiên của người dùng, tự động bóc tách các trường thông tin (tên sách, tác giả, năm, nhà xuất bản, thể loại...) để sinh câu truy vấn DSpace API chính xác.
- **Tóm tắt nội dung bằng AI**: Đọc và tổng hợp nhanh phần tóm tắt (Abstract) của tài liệu và giới thiệu sinh động cho người học (tối đa 3 dòng).
- **Hỏi đáp thông tin thư viện (FAQ)**: Trả lời tự động các câu hỏi về giờ mở cửa, cách làm thẻ, wifi, phòng học nhóm... tích hợp cơ chế tìm kiếm thời gian thực Google Search Grounding.
- **Đề xuất cá nhân hóa**: Tự động gợi ý sách ngẫu nhiên dựa trên chủ đề người dùng thường xuyên tìm kiếm nhất trong phiên chat.
- **Cơ chế dự phòng cao (Failover/Fallback)**: 
  - Hỗ trợ xoay tua nhiều API Key Gemini để tránh lỗi giới hạn hạn mức (Rate Limits).
  - Tự động chuyển sang bộ quy tắc Offline (Rule-based Regex) nếu toàn bộ dịch vụ AI gặp sự cố.
- **Tích hợp đa kênh**: Cung cấp API Webhook `/botstar/search` định dạng dữ liệu phẳng tương thích tốt để tích hợp thẳng lên Chatbot BotStar (Facebook Messenger / Zalo).
- **Giao diện Glassmorphism**: Thiết kế hiệu ứng kính mờ tối màu hiện đại, đa chủ đề màu sắc (Cyan, Green, Purple, Rose), tương thích hoàn toàn trên thiết bị di động.

---

## 📂 Cấu Trúc Thư Mục Dự Án

```text
SmartLib/
├── backend/                  # Mã nguồn Backend (FastAPI & AI Services)
│   ├── services/             # Các dịch vụ nghiệp vụ chính
│   │   ├── dspace_client.py  # Client gọi API DSpace 7.4 HUST
│   │   ├── history_client.py # Quản lý lịch sử chat và phân tích sở thích
│   │   └── nlp.py            # AI Engine (Phân loại ý định, Grounding, Fallback)
│   ├── main.py               # Điểm khởi chạy FastAPI ứng dụng
│   ├── requirements.txt      # Thư viện Python phụ thuộc
│   ├── Dockerfile            # Cấu hình container đóng gói backend
│   └── .env.example          # Tệp mẫu cấu hình biến môi trường
├── frontend/                 # Mã nguồn Frontend (Web App tĩnh)
│   ├── index.html            # Giao diện chính (HTML, CSS Glassmorphism, JS)
│   └── *.jpg / *.png         # Tài nguyên hình ảnh, hình nền & logo
├── DEPLOY_FREE_30_DAYS.md    # Hướng dẫn chi tiết triển khai lên cloud miễn phí
├── Dockerfile                # Dockerfile chung cho toàn bộ dự án
├── render.yaml               # Cấu hình Render Blueprint deploy nhanh
└── index.html                # Tệp chuyển hướng tự động vào thư mục frontend/
```

---

## 🛠️ Hướng Dẫn Cài Đặt & Chạy Dưới Local

### 1. Yêu Cầu Hệ Thống
- Đã cài đặt **Python 3.9** trở lên.
- Đã đăng ký và có khóa API của Google Gemini (lấy miễn phí tại [Google AI Studio](https://aistudio.google.com/)).

### 2. Cài Đặt Backend
1. Di chuyển vào thư mục `backend`:
   ```bash
   cd backend
   ```
2. Cài đặt các thư viện phụ thuộc:
   ```bash
   pip install -r requirements.txt
   ```
3. Tạo tệp cấu hình môi trường `.env` từ file ví dụ:
   ```bash
   copy .env.example .env
   ```
4. Điền các khóa API Gemini của bạn vào `.env` (ngăn cách bởi dấu phẩy nếu cấu hình nhiều khóa):
   ```text
   GEMINI_API_KEYS=key_thu_nhat,key_thu_hai
   PORT=8001
   ```
5. Chạy server backend:
   ```bash
   python main.py
   ```
   *Lúc này backend sẽ chạy mặc định tại địa chỉ: `http://localhost:8001`*

### 3. Chạy Frontend
1. Mở tệp `frontend/index.html` và chỉnh sửa dòng cấu hình API ở đầu thẻ `<script>` trỏ về địa chỉ backend cục bộ của bạn:
   ```javascript
   const API = "http://localhost:8001";
   ```
2. Mở trực tiếp file `frontend/index.html` trên trình duyệt web, hoặc sử dụng các tiện ích Live Server (VS Code) / chạy máy chủ HTTP tĩnh:
   ```bash
   cd frontend
   python -m http.server 8000
   ```
   *Mở trình duyệt truy cập: `http://localhost:8000`*

---

## 🚀 Triển Khai Trực Tuyến (Deployment)

### 1. Backend (Triển khai trên Render / Railway)
- **Render**: Hệ thống đã cấu hình sẵn file `render.yaml`. Trên Render, tạo một **Blueprint** mới, liên kết với repo này và điền biến môi trường `GEMINI_API_KEYS`.
- **Railway**: Tạo dịch vụ mới từ thư mục `backend`, sử dụng lệnh chạy mặc định:
  ```text
  gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
  ```

### 2. Frontend (Triển khai trên Vercel / GitHub Pages)
- Chọn thư mục gốc (Root Directory) là `frontend/`.
- Cấu hình Framework Preset là **Other**, bỏ trống mục build command.
- Nhớ cập nhật lại biến `const API = "https://your-backend-domain.com"` trong [frontend/index.html](file:///d:/SmartLib/frontend/index.html) để kết nối đúng với server backend trực tuyến.

*Chi tiết các bước triển khai trực tuyến vui lòng xem thêm tại tệp [DEPLOY_FREE_30_DAYS.md](file:///d:/SmartLib/DEPLOY_FREE_30_DAYS.md).*

---

## 📝 Bản Quyền & Giấy Phép
Dự án được phân phối dưới giấy phép **MIT License**. Bạn được tự do học tập, sửa đổi và triển khai cho các mục đích phi thương mại.
