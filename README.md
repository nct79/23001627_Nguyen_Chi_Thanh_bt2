# 23001627_Nguyen_Chi_Thanh_bt2
# So sánh hiệu năng nạp dữ liệu vào SQLite: Row-by-Row vs. Batch

Dự án thực nghiệm so sánh hiệu năng và tính toàn vẹn dữ liệu khi nạp dữ liệu NYC Taxi (`yellow_tripdata_2024-02.csv`) vào cơ sở dữ liệu **SQLite** bằng Python theo hai phương pháp:
- **Cách 1 (Row-by-Row):** Thực hiện `INSERT` và `commit` từng bản ghi một.
- **Cách 2 (Batch):** Gom dữ liệu theo từng lô (`executemany`) rồi mới `commit`.

## Môi trường & Công cụ
- **Ngôn ngữ:** Python 3.13 (`sqlite3`, `csv`, `pathlib`, `os`, `time`)
- **Cơ sở dữ liệu:** SQLite
## Kết quả thực nghiệm (50,000 dòng đầu vào)
| Tiêu chí | Cách 1 (Row-by-Row) | Cách 2 (Batch) | Chênh lệch / Kiểm chứng |
| :--- | :---: | :---: | :---: |
| **Thời gian chạy** | `127.84s` | `0.32s` | Batch nhanh hơn **398.3x** |
| **Số dòng nạp** | `50,000` | `50,000` | Khớp (`True`) |
| **Dung lượng DB** | `1.38 MB` | `1.38 MB` | Bằng nhau |
| **Tổng quãng đường (`SUM`)** | - | - | Khớp (`True`) |
| **Tổng tiền (`SUM`)** | - | - | Khớp (`True`) |
## Nhận xét
- Việc gọi `commit()` sau mỗi dòng ở phương pháp **Row-by-Row** tạo ra số lượng lớn giao dịch ghi đĩa (disk I/O), khiến thời gian thực thi tăng lên đáng kể.
- Phương pháp **Batch** gom nhiều bản ghi trong mỗi giao dịch giúp giảm overhead của transaction và I/O, tăng tốc độ nạp lên **398.3x** mà vẫn đảm bảo tính chính xác tuyệt đối về số lượng dòng và các giá trị tổng hợp.
# Chạy thử với bộ dữ liệu "yellow_tripdata_2024-02.csv"
