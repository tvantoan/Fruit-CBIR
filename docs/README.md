# Hướng dẫn Setup & Chạy Fruit CBIR Project

## 📋 Checklist trước khi chạy

### 1. **Prerequisites**
- Python 3.8+ đã cài đặt
- PostgreSQL 12+ đã cài đặt và chạy
- Node.js 16+ (nếu chạy frontend)
- `pip` package manager

### 2. **Backend Setup**

#### 2.1. Tạo Python environment
```bash
cd /home/kiiri/projects/fruit
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc trên Windows: venv\Scripts\activate
```

#### 2.2. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

#### 2.3. Cấu hình Database
Kiểm tra file `.env` và đảm bảo cấu hình PostgreSQL:
```
DB_USER=fruit_app_user
DB_PASSWORD=aaavbb121213
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fruit_db
FRONTEND_URL=http://localhost:5173
BACKEND_PORT=5001
```

#### 2.4. Tạo database và schema
```bash
# Trong PostgreSQL (hoặc từ terminal)
createdb fruit_db -U fruit_app_user
psql -U fruit_app_user -d fruit_db -f infrastructure/database/schema.sql
```

Hoặc tạo database từ PostgreSQL client:
```sql
CREATE DATABASE fruit_db OWNER fruit_app_user;
\c fruit_db
-- Sau đó chạy schema từ file schema.sql trong client
```

**Quan trọng**: Cần cài extension pgvector trên database (nếu chưa có):
```bash
psql -U fruit_app_user -d fruit_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

#### 2.5. Chuẩn bị dữ liệu
Project cần các ảnh trái cây được tiền xử lý trong thư mục:
- `static/Fruits_data_processed/Apples_processed/`
- `static/Fruits_data_processed/Bananas_processed/`
- v.v.

Nếu chưa có, có thể chạy preprocessing script:
```bash
python infrastructure/AI_models/preprocessing/rembg_module_preprocess.py
```

#### 2.6. Chạy Backend
```bash
python app.py
```

Backend sẽ:
1. Khởi tạo connection pool database
2. Seed dữ liệu từ `static/Fruits_data_processed/` (nếu database chưa có)
3. Chạy FastAPI trên port 5001

### 3. **Frontend Setup** (tùy chọn)

#### 3.1. Setup React frontend
```bash
cd view
npm install
npm run dev
```

Frontend sẽ chạy trên `http://localhost:5173`

### 4. **Test API**

#### 4.1. Kiểm tra API health
```bash
curl http://localhost:5001/api/images/1
```

#### 4.2. Chạy evaluation script (nếu có ground truth)
```bash
python infrastructure/AI_models/evaluation/evaluate_fruit.py --mode direct
```

---

## 🔧 Troubleshooting

### Lỗi: "ImportError: No module named 'psycopg2'"
**Giải pháp**: Cài đặt psycopg2-binary
```bash
pip install psycopg2-binary
```

### Lỗi: "Could not connect to database"
- Kiểm tra PostgreSQL đang chạy: `systemctl status postgresql` (Linux)
- Kiểm tra cấu hình `.env` đúng
- Kiểm tra user `fruit_app_user` có quyền truy cập database

### Lỗi: "No module named 'rembg'"
```bash
pip install rembg==3.0.0
# Lần đầu chạy sẽ download model (~400MB)
```

### Lỗi: "relation 'images' does not exist"
- Schema chưa được tạo - chạy lại `schema.sql`
- Hoặc database sai

### Lỗi: "pgvector extension not found"
```bash
psql -U fruit_app_user -d fruit_db
CREATE EXTENSION IF NOT EXISTS vector;
\q
```

---

## 📝 Cấu trúc Project

```
fruit/
├── app.py                 # Entry point (Flask)
├── domain/                # Business logic & interfaces
├── infrastructure/        # Database, repos, AI models
├── presentation/          # API controllers
├── usecases/              # Use cases
├── static/                # Data (images)
├── view/                  # React frontend
└── requirements.txt       # Python dependencies
```

---

## 🚀 Command summary

```bash
# Setup
cd /home/kiiri/projects/fruit
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Database
createdb fruit_db -U fruit_app_user
psql -U fruit_app_user -d fruit_db -f infrastructure/database/schema.sql

# Run backend
python app.py

# Run frontend (separate terminal)
cd view && npm install && npm run dev
```

---

## ⚠️ Cảnh báo quan trọng

1. **Thời gian lần đầu**: Lần đầu chạy, app sẽ:
   - Tải model `rembg` (~400MB)
   - Extract features cho tất cả ảnh (có thể mất vài phút)

2. **disk space**: Cần ít nhất 500MB free để tải dependencies + models

3. **GPU optional**: Có GPU sẽ nhanh hơn (CUDA) nhưng CPU cũng chạy được

---

## 📞 Ghi chú

- File `.env` chứa cấu hình nhạy cảm - không commit lên git
- Nếu muốn reset data, xóa tables rồi chạy `seed_data.py` lại
