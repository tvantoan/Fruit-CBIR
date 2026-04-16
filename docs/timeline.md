# TIMELINE DỰ ÁN FRUIT-CBIR (4 TUẦN: 19/03 → 19/04/2026)

## Tổng quan Gantt

```
            Tuần 1 (19-25/03)    Tuần 2 (26/03-01/04)   Tuần 3 (02-08/04)    Tuần 4 (09-19/04)
            ──────────────────   ──────────────────────  ──────────────────   ──────────────────
Thành viên A ████ Fix pochih     ████ Ground-truth       ████ Hỗ trợ test    ████ Báo cáo data
             ████ Bổ sung data   ████ Hỗ trợ B extract   ████ Evaluation     ████ Review & fix

Thành viên B ████ Adapt pochih   ████ Viết 4 features    ████ Fusion + Index ████ Báo cáo thuật toán
             ████ (color,gabor   ████ (CM, Hu, GLCM,     ████ Tối ưu P@5    ████ Review & fix
              edge, HOG)          LBP)

Thành viên C ████ Flask setup    ████ DB layer + API     ████ Kết quả TG     ████ Báo cáo hệ thống
             ████ Templates       ████ Upload + search    ████ Tích hợp full  ████ Demo + fix
             ████ (từ SoTu)

Mốc quan     ▲ Kick-off         ▲ Features chạy được   ▲ Hệ thống chạy    ▲ DEADLINE 19/04
trọng        19/03               trên 100 ảnh test      end-to-end          Demo + Nộp báo cáo
```

---

## Tuần 1: 19/03 → 25/03 — Setup & Nền tảng

**Mốc:** Tất cả module cơ bản compile được, chạy được trên 1 ảnh test.

| Thành viên | Công việc | Deliverable | Deadline |
|------------|-----------|-------------|----------|
| **A** | Fix `scipy.misc.imread` → `cv2.imread` trong tất cả code pochih | Code pochih chạy được với Python 3.10+ | 21/03 (T6) |
| **A** | Bổ sung thêm 2-7 loại quả từ Fruits-360 (đạt ≥10 loại) | Thư mục data có ≥10 categories | 23/03 (CN) |
| **A** | Chạy preprocess cho data mới (resize 224×224, rembg) | Tất cả ảnh mới đã processed | 25/03 (T3) |
| **B** | Adapt `color.py` từ pochih → chạy được trên dataset quả | `features/color.py` output vector đúng | 21/03 (T6) |
| **B** | Adapt `gabor.py`, `edge.py`, `HOG.py` từ pochih | 4 file feature chạy được | 25/03 (T3) |
| **C** | Setup Flask app từ SoTu (factory, blueprint, templates) | `flask run` hiển thị trang upload | 22/03 (T7) |
| **C** | Tạo SQLite schema + `db_manager.py` (CRUD cơ bản) | Insert/query image metadata hoạt động | 25/03 (T3) |

---

## Tuần 2: 26/03 → 01/04 — Features & Database

**Mốc:** Trích xuất đặc trưng chạy được trên 100 ảnh test, lưu vào SQLite.

| Thành viên | Công việc | Deliverable | Deadline |
|------------|-----------|-------------|----------|
| **A** | Xây ground-truth: chọn 25 ảnh query, xác định top-5 thủ công | `evaluation/ground_truth.json` | 29/03 (T7) |
| **A** | Hỗ trợ B chạy extract features trên toàn bộ 7000+ ảnh | Features extracted cho full dataset | 01/04 (T3) |
| **B** | Viết `color_moments.py` + `hu_moments.py` | 2 feature modules test passed | 28/03 (T6) |
| **B** | Viết `glcm.py` + `lbp.py` | 4/4 features mới hoàn thành | 30/03 (CN) |
| **B** | Viết `extractor.py` — gom tất cả features thành 1 vector | `extract_all(image)` → combined vector | 01/04 (T3) |
| **C** | API upload ảnh + lưu metadata vào SQLite | POST /upload hoạt động | 28/03 (T6) |
| **C** | Tích hợp feature extraction vào pipeline | Upload → extract → lưu DB tự động | 01/04 (T3) |

---

## Tuần 3: 02/04 → 08/04 — Tích hợp & Tìm kiếm

**Mốc:** Hệ thống chạy end-to-end: upload ảnh → trả top-5 kết quả.

| Thành viên | Công việc | Deliverable | Deadline |
|------------|-----------|-------------|----------|
| **A** | Chạy evaluation trên ground-truth, báo cáo P@5 ban đầu | Bảng P@5 cho từng loại quả | 05/04 (T7) |
| **A** | Test edge cases: ảnh nền phức tạp, ảnh chất lượng thấp | Danh sách bugs/issues | 08/04 (T3) |
| **B** | Adapt `fusion.py` — weighted fusion tối ưu cho quả | Trọng số cho từng nhóm feature | 04/04 (T6) |
| **B** | Xây KD-Tree/FAISS index (`indexer.py`) | Index build + query < 100ms | 05/04 (T7) |
| **B** | Viết `search/engine.py` — top-5 retrieval | `search(query_image)` → 5 results | 06/04 (CN) |
| **B** | Tune weights dựa trên P@5 từ A | P@5 ≥ 0.7 | 08/04 (T3) |
| **C** | Trang kết quả: hiển thị top-5 + similarity scores | Result page hoạt động | 05/04 (T7) |
| **C** | Trang kết quả trung gian: histogram charts, distance table | Tabs Histogram/Features/Distances | 07/04 (T2) |
| **C** | Tích hợp full: upload → preprocess → search → display | Demo end-to-end chạy mượt | 08/04 (T3) |

---

## Tuần 4: 09/04 → 19/04 — Hoàn thiện & Báo cáo

**Mốc cuối: 19/04 — Demo + Nộp báo cáo.**

| Thành viên | Công việc | Deliverable | Deadline |
|------------|-----------|-------------|----------|
| **A** | Viết báo cáo phần dữ liệu (thu thập, tiền xử lý, thống kê) | Section trong report.docx | 13/04 (CN) |
| **A** | Viết phần evaluation trong báo cáo (P@5, mAP, so sánh) | Section trong report.docx | 16/04 (T4) |
| **B** | Viết báo cáo phần thuật toán (features, fusion, distance) | Section trong report.docx | 13/04 (CN) |
| **B** | Fix bugs về accuracy, tối ưu nếu P@5 < 0.7 | Code final | 16/04 (T4) |
| **C** | Viết báo cáo phần hệ thống (DB, API, giao diện) | Section trong report.docx | 13/04 (CN) |
| **C** | Polish UI, fix bugs, chụp screenshots demo | Demo sẵn sàng | 16/04 (T4) |
| **Cả nhóm** | Review chéo báo cáo, ghép thành 1 file hoàn chỉnh | report.docx final | 17/04 (T5) |
| **Cả nhóm** | Làm slide thuyết trình | slides.pptx | 18/04 (T6) |
| **Cả nhóm** | **Dry-run demo + nộp** | **DONE** | **19/04 (T7)** |

---

## Dependency Map (thứ tự phụ thuộc)

```
A: Fix pochih code ──────┐
                         ├──→ B: Adapt 4 features pochih ──→ B: Viết 4 features mới
A: Bổ sung data ─────────┘                                          │
                                                                     ▼
C: Flask setup ──→ C: DB layer ──→ C: API upload ──→  B: extractor.py + fusion.py
                                                        │
                                              ┌─────────┘
                                              ▼
                              A: Extract full dataset ──→ B: Build index
                                                              │
                              A: Ground-truth ────────────────┤
                                                              ▼
                                                    B: search/engine.py
                                                              │
                                                              ▼
                                               C: Tích hợp + UI kết quả TG
                                                              │
                                                              ▼
                                              A: Evaluation (P@5) ──→ B: Tune weights
                                                                           │
                                                                           ▼
                                                              Cả nhóm: Báo cáo + Demo
```

---

## Checklist theo mốc kiểm tra

- [ ] **25/03** — Code pochih đã fix, Flask app chạy, SQLite schema ready
- [ ] **01/04** — 8 features (4 adapt + 4 mới) chạy được, extract 100 ảnh test OK
- [ ] **08/04** — Hệ thống end-to-end: upload → top-5 results + kết quả trung gian
- [ ] **16/04** — Báo cáo draft xong, P@5 ≥ 0.7, UI hoàn thiện
- [ ] **19/04** — DEADLINE: Demo + nộp báo cáo + slide

---

## Lưu ý quan trọng

1. **Tuần 1 là critical path** — B phụ thuộc vào A fix code pochih, C có thể làm song song.
2. **Tuần 3 là tuần tích hợp** — cả 3 thành viên cần sync thường xuyên (recommend daily standup 15 phút).
3. **Buffer 3 ngày cuối** (16-19/04) — dành cho fix bugs, polish, và unexpected issues.
4. **Ground-truth (A, tuần 2)** là bottleneck cho evaluation — nên bắt đầu sớm.
