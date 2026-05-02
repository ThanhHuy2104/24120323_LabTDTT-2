# Todo App - LAB 2 (API & Firebase)

Ứng dụng **Todo App**:

- **Backend**: FastAPI (Python) cung cấp REST API.
- **Frontend**: HTML + CSS + JavaScript thuần (không dùng framework).
- **Auth**: Firebase Authentication (Email/Password).
- **Database**: Cloud Firestore (lưu task theo từng user).

---

# Thông Tin Sinh Viên
- Họ và tên: `Huỳnh Thanh Huy`
- MSSV: `24120323`
- Lớp: `24CTT3`

## 1. Cấu trúc thư mục

```
todo-app/
├── backend/
│   └── app/
│       ├── main.py                  # FastAPI app
│       ├── routers/
│       │   ├── auth.py              # /auth/me
│       │   └── tasks.py             # /tasks (GET/POST/PATCH/DELETE)
│       ├── schemas/
│       │   └── task.py              # Pydantic models
│       └── services/
│           ├── auth.py              # Bearer token dependency
│           └── firebase_service.py  # Firebase Admin + Firestore (có fallback in-memory)
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── app.js                       # Logic chính
│   └── config.js                    # CẤU HÌNH Firebase + URL backend
├── requirements.txt
├── .gitignore
└── README.md
```

## 2. Cài đặt môi trường

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## 3. Chạy backend

Từ thư mục `backend/`:

```bash
cd backend
uvicorn app.main:app --reload
```

Truy cập:

- API root: <http://127.0.0.1:8000/>
- Health: <http://127.0.0.1:8000/health>
- Swagger docs: <http://127.0.0.1:8000/docs>

## 4. Chạy frontend

```bash
cd frontend
python -m http.server 5500
```

Sau đó mở: <http://localhost:5500>

## 5. Cấu hình Firebase 

### 5.1. Tạo project Firebase

1. Vào <https://console.firebase.google.com/> tạo project mới.
2. Vào **Authentication** → **Sign-in method** → bật **Email/Password**.
3. Vào **Firestore Database** → **Create database** (chọn test mode hoặc
   đặt rule cho phép user đã đăng nhập đọc/ghi).

### 5.2. Cấu hình frontend

Trong **Project settings → Your apps → Web app**, copy đoạn `firebaseConfig`
và dán vào `frontend/config.js`.

```js
const FIREBASE_CONFIG = {
  apiKey: "...",
  authDomain: "...",
  projectId: "...",
  // ...
};
```

### 5.3. Cấu hình backend

Trong **Project settings → Service accounts** → **Generate new private key**.
Tải file JSON về và đặt tên `serviceAccountKey.json` trong thư mục `backend/`.



## 6. Các endpoint của backend

| Method | Endpoint           | Mô tả                                  | Auth |
|--------|--------------------|----------------------------------------|------|
| GET    | `/`                | Trang gốc, liệt kê endpoints           | ✗    |
| GET    | `/health`          | Health check + storage mode            | ✗    |
| GET    | `/auth/me`         | Lấy thông tin user từ ID token         | ✓    |
| GET    | `/tasks`           | Lấy danh sách task của user            | ✓    |
| POST   | `/tasks`           | Thêm task mới                          | ✓    |
| PATCH  | `/tasks/{id}`      | Cập nhật task (đổi tiêu đề / done)     | ✓    |
| DELETE | `/tasks/{id}`      | Xoá task                               | ✓    |

Auth dùng header: `Authorization: Bearer <ID_TOKEN>`.

## 7. Feature chính

Sau khi đăng nhập:

1. **Thêm task**: nhập nội dung → bấm "Thêm" → frontend gọi `POST /tasks`
   → backend xác thực token → lưu vào Firestore (hoặc memory).
2. **Xem task**: trang load tự động gọi `GET /tasks`.
3. **Đánh dấu đã xong**: tick checkbox → `PATCH /tasks/{id}`.
4. **Xoá**: bấm ✕ → `DELETE /tasks/{id}`.
5. **Lọc**: tab "Tất cả / Chưa xong / Đã xong".
6. **Đăng xuất**: xoá token và quay lại màn hình đăng nhập.

## 8. Video demo

[![Xem video](https://techvccloud.mediacdn.vn/280518386289090560/2021/7/5/api-la-gi-1-640x322-16254795881731210500168-0-30-322-603-crop-16254795955021767193036.jpg)](https://youtu.be/zgrhzv4_Ge0)
