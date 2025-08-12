# 🟡 Market Backend API

- (routers → services → repositories → models) và có middleware xử lý lỗi, CORS, migrations.
- Schema la DTO cho response
---

## 🛠️ CÀI ĐẶT

### 1. **Yêu cầu**
- Python 3.8+
- PostgreSQL 12+
- pip

### 2. **Clone code & tạo môi trường**

- git clone <repo_url>
- cd <repo_folder>
- python -m venv venv
- source venv/bin/activate  # Hoặc .\venv\Scripts\activate trên Windows
- pip install -r requirements.txt
 
### 3. Tạo file .env

### 4. Khởi tạo database
alembic upgrade head

⚡️ CHẠY SERVER
uvicorn app.main:app --reload

API docs tự động: http://localhost:8000/docs
