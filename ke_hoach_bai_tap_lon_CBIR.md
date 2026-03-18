# KẾ HOẠCH BÀI TẬP LỚN: HỆ CSDL LƯU TRỮ VÀ TÌM KIẾM ẢNH QUẢ

## Nhóm: 3 thành viên

---

## I. TỔNG QUAN DỰ ÁN

**Mục tiêu:** Xây dựng hệ cơ sở dữ liệu lưu trữ và tìm kiếm ảnh quả (fruit image retrieval system) sử dụng kỹ thuật CBIR (Content-Based Image Retrieval). Hệ thống nhận đầu vào là một ảnh quả bất kỳ, trả về 5 ảnh tương tự nhất từ CSDL xếp theo độ tương đồng giảm dần.

**Chiến lược triển khai:** Ghép thuật toán từ **pochih/CBIR** với kiến trúc web từ **SoTu**, kết hợp ~60-65% code tự viết mới.

**Công nghệ:**
- **Ngôn ngữ:** Python 3.10+
- **Backend/Web framework:** Flask (factory pattern + Blueprint từ SoTu)
- **CSDL:** SQLite
- **Xử lý ảnh:** OpenCV, scikit-image, Pillow
- **Trích xuất đặc trưng:** OpenCV + NumPy (adapt từ pochih/CBIR + viết mới)
- **Frontend:** HTML/CSS/JavaScript (Bootstrap, templates từ SoTu)
- **Lập chỉ mục không gian:** scipy.spatial.KDTree hoặc FAISS

---

## II. NGUỒN THAM KHẢO & PHÂN BỔ CODE

### Từ pochih/CBIR (nền tảng thuật toán):
| File gốc | Chuyển thành | Ghi chú |
|----------|-------------|---------|
| `src/color.py` | `features/color.py` | Adapt, fix `scipy.misc.imread` → `cv2.imread` |
| `src/gabor.py` | `features/gabor.py` | Adapt |
| `src/edge.py` | `features/edge.py` | Adapt |
| `src/HOG.py` | `features/hog.py` | Adapt |
| `src/evaluate.py` | `evaluation/evaluate.py` | Adapt |
| `src/fusion.py` | `features/fusion.py` | Adapt — weighted fusion cho quả |

### Từ SoTu (kiến trúc web):
| File gốc | Chuyển thành | Ghi chú |
|----------|-------------|---------|
| `app/__init__.py` | `src/app/__init__.py` | Flask factory pattern |
| `app/main/views.py` | `src/app/main/views.py` | Routes |
| `app/main/forms.py` | `src/app/main/forms.py` | Upload form |
| `templates/base.html` | `src/app/templates/base.html` | Layout |
| `templates/index.html` | `src/app/templates/index.html` | Upload page |
| `templates/result.html` | `src/app/templates/result.html` | Results page |
| `config.py` | `config.py` | Config |
| Error handling | `src/app/errors/` | 404/500 |

### Code tự viết mới (~60-65%):
| File | Mô tả |
|------|--------|
| `features/color_moments.py` | Color Moments (mean, std, skew) |
| `features/hu_moments.py` | 7 Hu Moments |
| `features/glcm.py` | GLCM texture |
| `features/lbp.py` | Local Binary Pattern |
| `database/db_manager.py` | SQLite (schema + CRUD) — thay thế DB.py (pochih) & pickle (SoTu) |
| `database/indexer.py` | KD-Tree / FAISS index |
| `search/engine.py` | Search engine (top-5) |
| `templates/result.html` | Kết quả trung gian (histogram charts, distance breakdown) |
| `evaluation/evaluate_fruit.py` | Precision@5 cho quả |
| `preprocessing/preprocess.py` | Chuẩn hóa ảnh |

---

## III. PHÂN CÔNG NHÓM (CẬP NHẬT)

### Thành viên A — Dữ liệu & Tiền xử lý ảnh
**Phụ trách chính:** Thu thập dữ liệu, tiền xử lý, chuẩn hóa ảnh, fix code pochih

| Công việc | Trạng thái |
|-----------|------------|
| Thu thập bộ dữ liệu ≥1000 ảnh quả (Kaggle: Fruits-360). Phân loại theo thư mục. | ✅ Hoàn thành — 7.147 ảnh, 8 loại quả |
| Chuẩn hóa ảnh: resize 256×256, đồng nhất định dạng. Viết script `preprocess.py` tự động hóa. | ✅ Hoàn thành — `rembg_module_preprocess.py` (224×224 PNG, có background removal) |
| Fix `scipy.misc.imread` → `cv2.imread` trong code pochih/CBIR | ❌ Chưa làm |
| Xây dựng bộ ground-truth: chọn 20-30 ảnh truy vấn mẫu, xác định thủ công top-5 tương tự nhất. | ❌ Chưa làm |
| Chạy evaluation, hỗ trợ thành viên B trích xuất đặc trưng toàn bộ dataset. | ❌ Chưa làm |
| Viết báo cáo phần dữ liệu, đánh giá kết quả cùng nhóm. | ❌ Chưa làm |

**Dữ liệu hiện có:**
| Loại quả | Số ảnh |
|----------|--------|
| Bananas | 1.408 |
| Mangoes | 1.368 |
| Oranges | 1.358 |
| Grapes | 1.295 |
| Apples | 911 |
| Pomegranates | 310 |
| Strawberries | 249 |
| Peaches | 248 |
| **Tổng** | **7.147** |

### Thành viên B — Trích xuất đặc trưng & Thuật toán tìm kiếm
**Phụ trách chính:** Adapt thuật toán pochih, viết đặc trưng mới, fusion, index

| Công việc | Trạng thái |
|-----------|------------|
| Adapt `color.py`, `gabor.py`, `edge.py`, `HOG.py` từ pochih/CBIR | ❌ Chưa làm |
| Viết mới: `color_moments.py`, `hu_moments.py`, `glcm.py`, `lbp.py` | ❌ Chưa làm |
| Adapt `fusion.py` — weighted fusion tối ưu cho ảnh quả | ❌ Chưa làm |
| Xây dựng KD-Tree / FAISS index | ❌ Chưa làm |
| Cài đặt các hàm đo khoảng cách (Euclidean, Chi-Square, Cosine) | ❌ Chưa làm |
| Đánh giá Precision/Recall. Viết báo cáo phần thuật toán. | ❌ Chưa làm |

### Thành viên C — CSDL, Backend & Giao diện
**Phụ trách chính:** Kiến trúc Flask từ SoTu, SQLite database, giao diện, tích hợp

| Công việc | Trạng thái |
|-----------|------------|
| Lấy kiến trúc Flask từ SoTu (Blueprint, factory pattern, templates, form upload, drag-drop, error handling) | ❌ Chưa làm |
| Viết SQLite database layer (`db_manager.py`) — thay thế DB.py (pochih) & pickle (SoTu) | ❌ Chưa làm |
| Xây dựng giao diện web: upload ảnh, hiển thị kết quả top-5 | ❌ Chưa làm |
| Thêm trang hiển thị kết quả trung gian (histogram charts, distance breakdown table) | ❌ Chưa làm |
| Tích hợp toàn bộ hệ thống. Demo, sửa lỗi, viết báo cáo phần hệ thống. | ❌ Chưa làm |

---

## IV. CHI TIẾT KỸ THUẬT

### 1. Bộ dữ liệu (Yêu cầu 1)

**Yêu cầu:**
- Tối thiểu 1000 ảnh ✅ (đã có 7.147)
- Ít nhất 10-15 loại quả khác nhau (hiện có 8, cần bổ sung thêm)
- Cùng kích thước: 256×256 pixels (hoặc 224×224)
- Vật trong ảnh có tỉ lệ khung hình tương đồng

**Cấu trúc thư mục hiện tại:**
```
Fruits_data_processed/
├── Apples_processed/       (911 ảnh)
├── Bananas_processed/      (1.408 ảnh)
├── Grapes_processed/       (1.295 ảnh)
├── Mangoes_processed/      (1.368 ảnh)
├── Oranges_processed/      (1.358 ảnh)
├── Peaches_processed/      (248 ảnh)
├── Pomegranates_processed/ (310 ảnh)
└── Strawberries_processed/ (249 ảnh)
```

### 2. Bộ thuộc tính đặc trưng (Yêu cầu 2)

Bộ đặc trưng gồm 2 nguồn: adapt từ pochih/CBIR + viết mới.

#### 2.1. Từ pochih/CBIR (adapt):

| Đặc trưng | File gốc | Mô tả |
|-----------|----------|-------|
| **Color Histogram** | `color.py` | Histogram màu HSV |
| **Gabor Filter** | `gabor.py` | Đặc trưng texture theo tần số & hướng |
| **Edge Histogram** | `edge.py` | Phân bố cạnh (edge direction) |
| **HOG** | `HOG.py` | Histogram of Oriented Gradients |

#### 2.2. Viết mới:

| Đặc trưng | Mô tả | Chiều vector | Lý do chọn |
|-----------|-------|-------------|------------|
| **Color Moments** | Mean, std, skewness mỗi kênh HSV | 9 | Tóm tắt compact phân bố màu |
| **Hu Moments** | 7 mô men bất biến Hu | 7 | Phân biệt hình dạng (tròn vs dài) |
| **GLCM** | Contrast, correlation, energy, homogeneity | 4 | Phân biệt bề mặt mịn vs sần |
| **LBP** | Local Binary Pattern histogram | 10-26 | Bất biến xoay, mô tả kết cấu vi mô |

#### 2.3. Tổng hợp:

**Tổng vector đặc trưng:** ~305 chiều (có thể dùng PCA giảm chiều)

**Weighted fusion:** Kết hợp các nhóm đặc trưng với trọng số tối ưu cho ảnh quả (adapt từ `fusion.py` của pochih).

### 3. Thiết kế CSDL (Yêu cầu 3)

#### Lược đồ (Schema):

```sql
-- Bảng chính lưu metadata ảnh
CREATE TABLE images (
    image_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    filename        TEXT NOT NULL,
    filepath        TEXT NOT NULL,
    fruit_label     TEXT NOT NULL,
    width           INTEGER,
    height          INTEGER,
    file_size_kb    REAL,
    date_added      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Bảng lưu vector đặc trưng (BLOB)
CREATE TABLE features (
    feature_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    image_id        INTEGER NOT NULL,
    feature_type    TEXT NOT NULL,
    feature_vector  BLOB NOT NULL,
    vector_dim      INTEGER NOT NULL,
    FOREIGN KEY (image_id) REFERENCES images(image_id)
);

-- Bảng lưu kết quả truy vấn (log)
CREATE TABLE query_logs (
    query_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    query_image     TEXT NOT NULL,
    result_ids      TEXT NOT NULL,
    distances       TEXT NOT NULL,
    query_time_ms   REAL,
    query_date      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Index cho tìm kiếm nhanh
CREATE INDEX idx_images_label ON images(fruit_label);
CREATE INDEX idx_features_type ON features(feature_type);
CREATE INDEX idx_features_image ON features(image_id);
```

**Ghi chú:** SQLite thay thế cả `DB.py` (pochih) lẫn pickle (SoTu). Feature vectors serialize bằng NumPy `tobytes()` → lưu BLOB.

### 4. Hệ thống tìm kiếm (Yêu cầu 4)

#### 4a. Sơ đồ khối hệ thống:

```
┌─────────────────────────────────────────────────────────────┐
│                    GIAO DIỆN NGƯỜI DÙNG                     │
│         (Từ SoTu: Flask Blueprint + templates)              │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ Upload ảnh   │  │ Chọn loại    │  │ Hiển thị kết quả  │  │
│  │ (drag-drop)  │  │ đặc trưng    │  │ (Top-5 + scores)  │  │
│  └──────┬───────┘  └──────┬───────┘  └────────▲──────────┘  │
└─────────┼─────────────────┼───────────────────┼─────────────┘
          │                 │                   │
          ▼                 ▼                   │
┌─────────────────────────────────┐             │
│      BỘ TIỀN XỬ LÝ ẢNH        │             │
│  - Resize 256×256               │             │
│  - Background removal (rembg)   │             │
└─────────────┬───────────────────┘             │
              ▼                                 │
┌─────────────────────────────────┐             │
│   BỘ TRÍCH XUẤT ĐẶC TRƯNG     │             │
│  Từ pochih:                     │             │
│  - Color Histogram (HSV)        │             │
│  - Gabor Filter                 │             │
│  - Edge Histogram               │             │
│  - HOG                          │             │
│  Viết mới:                      │             │
│  - Color Moments                │             │
│  - Hu Moments                   │             │
│  - GLCM Texture                 │             │
│  - LBP Texture                  │             │
│  → Weighted Fusion → VECTOR     │             │
└─────────────┬───────────────────┘             │
              ▼                                 │
┌─────────────────────────────────┐             │
│      MÁY TÌM KIẾM TƯƠNG TỰ     │             │
│  - Load index (KD-Tree/FAISS)    │             │
│  - Tính khoảng cách              │             │
│  - Sắp xếp theo distance tăng   │             │
│  - Trả về Top-5 kết quả         │             │
└─────────────┬───────────────────┘             │
              ▼                                 │
┌─────────────────────────────────┐             │
│         CƠ SỞ DỮ LIỆU          │─────────────┘
│  ┌────────────┐ ┌─────────────┐ │
│  │  Metadata   │ │  Feature    │ │
│  │  (SQLite)   │ │  Vectors    │ │
│  └────────────┘ └─────────────┘ │
│  ┌─────────────────────────────┐│
│  │  Index (KD-Tree / FAISS)    ││
│  └─────────────────────────────┘│
└─────────────────────────────────┘
```

#### 4b. Kết quả trung gian cần hiển thị:
1. **Ảnh đã tiền xử lý** (sau resize + background removal)
2. **Vector đặc trưng của ảnh truy vấn** (hiển thị dạng bảng hoặc bar chart)
3. **So sánh histogram màu** giữa ảnh truy vấn và từng ảnh kết quả
4. **Bảng khoảng cách chi tiết**: distance theo từng nhóm đặc trưng + distance tổng hợp
5. **Thời gian truy vấn**

### 5. Giao diện Demo (Yêu cầu 5)

Kiến trúc web từ SoTu:
- **Flask factory pattern** với Blueprint
- **Drag-drop upload** cho ảnh truy vấn
- **Error handling** (404/500)
- **Responsive layout** với Bootstrap

```
┌─────────────────────────────────────────────────────────┐
│  HỆ THỐNG TÌM KIẾM ẢNH QUẢ TƯƠNG TỰ                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────┐   Thống kê CSDL:                  │
│  │                 │   - Tổng số ảnh: 7,147             │
│  │   [Kéo thả     │   - Số loại quả: 8                 │
│  │    ảnh vào đây] │   - Thời gian index: ...           │
│  │                 │                                    │
│  └─────────────────┘                                    │
│  [Chọn file]  [Tìm kiếm]                               │
│                                                         │
│  ── KẾT QUẢ TÌM KIẾM ──────────────────────────────── │
│                                                         │
│  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐         │
│  │ #1  │  │ #2  │  │ #3  │  │ #4  │  │ #5  │         │
│  │     │  │     │  │     │  │     │  │     │         │
│  │d=.12│  │d=.18│  │d=.21│  │d=.25│  │d=.31│         │
│  │98.8%│  │98.2%│  │97.9%│  │97.5%│  │96.9%│         │
│  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘         │
│                                                         │
│  ── KẾT QUẢ TRUNG GIAN ─────────────────────────────── │
│                                                         │
│  [Tab: Histogram] [Tab: Features] [Tab: Distances]      │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Color Histogram so sánh:                       │   │
│  │  Query  ████████░░░░░░░░                        │   │
│  │  #1     ███████░░░░░░░░░                        │   │
│  │  #2     ██████░░░░░░░░░░                        │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Thời gian truy vấn: 45ms                               │
└─────────────────────────────────────────────────────────┘
```

### 6. Đánh giá hệ thống (Yêu cầu 5)

**Phương pháp đánh giá:**
- **Precision@5:** P@5 = (số ảnh đúng loại) / 5
- **Mean Average Precision (mAP):** Trung bình Precision trên nhiều truy vấn
- **Thời gian truy vấn:** Trung bình ms/truy vấn
- **So sánh đặc trưng:** Color only vs Texture only vs kết hợp → so sánh P@5

---

## V. CẤU TRÚC THƯ MỤC DỰ ÁN

```
Fruit-CBIR/
├── README.md
├── requirements.txt
├── config.py                       # Config (từ SoTu)
├── Fruits_data_processed/          # Bộ dữ liệu đã xử lý (7.147 ảnh)
│   ├── Apples_processed/
│   ├── Bananas_processed/
│   ├── Grapes_processed/
│   ├── Mangoes_processed/
│   ├── Oranges_processed/
│   ├── Peaches_processed/
│   ├── Pomegranates_processed/
│   └── Strawberries_processed/
├── rembg_module_preprocess.py      # Script tiền xử lý (background removal)
├── src/
│   ├── preprocessing/
│   │   └── preprocess.py           # Chuẩn hóa 256×256
│   ├── features/
│   │   ├── color.py                # Color Histogram (từ pochih)
│   │   ├── gabor.py                # Gabor Filter (từ pochih)
│   │   ├── edge.py                 # Edge Histogram (từ pochih)
│   │   ├── hog.py                  # HOG (từ pochih)
│   │   ├── color_moments.py        # Color Moments (viết mới)
│   │   ├── hu_moments.py           # Hu Moments (viết mới)
│   │   ├── glcm.py                 # GLCM texture (viết mới)
│   │   ├── lbp.py                  # LBP texture (viết mới)
│   │   ├── fusion.py               # Weighted fusion (từ pochih, adapt)
│   │   └── extractor.py            # Kết hợp tất cả đặc trưng
│   ├── database/
│   │   ├── schema.sql              # Lược đồ CSDL
│   │   ├── db_manager.py           # SQLite CRUD (viết mới)
│   │   └── indexer.py              # KD-Tree / FAISS index (viết mới)
│   ├── search/
│   │   └── engine.py               # Search engine top-5 (viết mới)
│   └── app/
│       ├── __init__.py             # Flask factory (từ SoTu)
│       ├── main/
│       │   ├── views.py            # Routes (từ SoTu)
│       │   └── forms.py            # Upload form (từ SoTu)
│       ├── templates/
│       │   ├── base.html           # Layout (từ SoTu)
│       │   ├── index.html          # Upload page (từ SoTu)
│       │   └── result.html         # Kết quả + trung gian (viết mới)
│       └── static/                 # CSS, JS
├── evaluation/
│   ├── ground_truth.json           # Dữ liệu đánh giá (thành viên A)
│   ├── evaluate.py                 # Evaluate gốc (từ pochih)
│   └── evaluate_fruit.py           # Precision@5 cho quả (viết mới)
├── docs/
│   ├── report.docx                 # Báo cáo
│   └── slides.pptx                 # Slide thuyết trình
└── demo/
    └── screenshots/                # Ảnh chụp demo
```

---

## VI. REQUIREMENTS.TXT

```
opencv-python>=4.8.0
numpy>=1.24.0
scikit-image>=0.21.0
scikit-learn>=1.3.0
scipy>=1.11.0
Pillow>=10.0.0
flask>=3.0.0
matplotlib>=3.7.0
rembg>=2.0.0
faiss-cpu>=1.7.4
```

---

## VII. RỦI RO VÀ GIẢI PHÁP

| Rủi ro | Xác suất | Giải pháp |
|--------|----------|-----------|
| Không đủ 1000 ảnh chất lượng | Thấp | Đã có 7.147 ảnh từ Fruits-360 |
| Tốc độ truy vấn chậm với brute-force | Trung bình | Dùng KD-Tree hoặc FAISS; PCA giảm chiều nếu cần |
| Precision thấp khi quả có màu tương tự | Cao | Tăng trọng số texture + shape; thử weighted fusion khác nhau |
| Code pochih dùng API cũ (`scipy.misc.imread`) | Cao | Thành viên A fix → `cv2.imread` |
| Tích hợp giữa pochih + SoTu + code mới | Trung bình | Định nghĩa rõ interface từ đầu; dùng Git quản lý |
| Chỉ có 8 loại quả (yêu cầu 10-15) | Trung bình | Bổ sung thêm từ Fruits-360 (có 131 loại) |
