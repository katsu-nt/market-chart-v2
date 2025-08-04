# 🟡 Market Backend API

**Market Backend API** là hệ thống backend quản lý giá vàng, tỷ giá ngoại tệ và chỉ số tài chính,  
xây dựng theo kiến trúc **clean architecture** với FastAPI, SQLAlchemy, Alembic và các công nghệ hiện đại.  
Hỗ trợ crawler tự động (scheduler), import dữ liệu, migration, RESTful API cho quản trị và frontend.

---

## 🚀 TÍNH NĂNG CHÍNH

- Quản lý giá vàng (trong nước, thế giới) theo loại, vùng, thời gian
- Quản lý tỷ giá trung tâm, thị trường, chỉ số tài chính
- Scheduler tự động crawl dữ liệu PNJ, XAU/USD, tỷ giá, v.v.
- Import/export dữ liệu từ file JSON
- API thống kê, lấy bảng giá, biểu đồ, chi tiết từng loại, v.v.
- Response chuẩn hóa, dễ dùng cho mọi frontend/mobile
- Xử lý exception, middleware log, CORS, environment, v.v.

---

## 🛠️ CÀI ĐẶT

### 1. **Yêu cầu**
- Python 3.8+
- PostgreSQL 12+
- pip

### 2. **Clone code & tạo môi trường**

git clone <repo_url>
cd <repo_folder>
python -m venv venv
source venv/bin/activate  # Hoặc .\venv\Scripts\activate trên Windows
pip install -r requirements.txt
 
### 3. Tạo file .env

### 4. Khởi tạo database
alembic revision --autogenerate -m "init tables"
alembic upgrade head

⚡️ CHẠY SERVER
uvicorn app.main:app --reload

API docs tự động: http://localhost:8000/docs