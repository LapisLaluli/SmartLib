# Deploy SmartLib mien phi khoang 30 ngay

## Phuong an khuyen nghi

- Backend: Railway Trial 30 ngay hoac Render Free.
- Frontend: Vercel Hobby hoac Netlify/GitHub Pages.

Backend can chay Python FastAPI trong thu muc `backend`.
Frontend la file tinh trong thu muc `frontend`.

## Backend tren Railway

1. Vao Railway va tao project moi tu GitHub repo `LapisLaluli/SmartLib`.
2. Chon service deploy tu thu muc `backend`.
3. Dat bien moi truong:

```text
GEMINI_API_KEYS=your_gemini_api_key_here
```

4. Cau hinh neu Railway khong tu nhan:

```text
Build command: pip install -r requirements.txt
Start command: gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
```

5. Sau khi deploy xong, copy domain backend dang:

```text
https://your-service.up.railway.app
```

## Backend tren Render

Repo da co `render.yaml`, Render co the doc Blueprint tu file nay.

1. Vao Render, chon New Blueprint.
2. Ket noi GitHub repo `LapisLaluli/SmartLib`.
3. Tao service `smartlib-backend`.
4. Nhap bien moi truong:

```text
GEMINI_API_KEYS=your_gemini_api_key_here
```

5. Sau khi deploy xong, copy domain backend dang:

```text
https://smartlib-backend.onrender.com
```

## Frontend tren Vercel

1. Tao project moi tu GitHub repo `LapisLaluli/SmartLib`.
2. Dat Root Directory la `frontend`.
3. Framework Preset: Other.
4. Build Command: de trong.
5. Output Directory: de trong.
6. Deploy.

## Cap nhat frontend tro ve backend moi

Trong `frontend/index.html`, sua dong:

```js
const API = "https://smartlib-p0j7.onrender.com".replace(/\/$/, "");
```

Thanh URL backend moi, vi du:

```js
const API = "https://your-service.up.railway.app".replace(/\/$/, "");
```

Sau do commit va push lai GitHub, Vercel se tu deploy lai.

## Luu y

- Khong commit file `backend/.env`.
- `backend/history.json` dang bi ignore, nen lich su chat tren hosting mien phi co the mat khi service restart.
- Render Free co the sleep khi khong co request, request dau tien sau khi sleep se cham.
