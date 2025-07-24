# 🪙 Market Chart 

Ứng dụng FastAPI để thu thập, lưu trữ và cung cấp dữ liệu giá vàng từ nhiều nguồn như PNJ,...
Dữ liệu được dùng để vẽ biểu đồ và hiển thị bảng giá vàng theo thời gian.


## 🚀 Cài đặt & chạy

### 1. Tạo môi trường ảo & cài thư viện

python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate      # Windows

pip install -r requirements.txt

### 2. Tạo file .env

### 3. Chạy app

uvicorn app.main:app --reload

