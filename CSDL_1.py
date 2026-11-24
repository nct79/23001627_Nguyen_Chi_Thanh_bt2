import os
import time
import pyarrow.parquet as pq

# Đổi thành thư mục đang chứa file .parquet của bạn (ví dụ: "data" hoặc "real_data")
PARQUET_DIR = "csv_output"
OUT_DIR = "csv_output"
os.makedirs(OUT_DIR, exist_ok=True)

months = ["2024-02", "2024-03", "2024-04"]
# Các cột chính gọn nhẹ (nếu muốn giữ toàn bộ cột gốc thì đặt cols = None)
cols = [
    "VendorID",
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "passenger_count",
    "trip_distance",
    "PULocationID",
    "DOLocationID",
    "payment_type",
    "total_amount",
]

merged_csv = os.path.join(OUT_DIR, "nyc_taxi_feb_mar_apr.csv")
if os.path.exists(merged_csv):
  os.remove(merged_csv)

t0 = time.perf_counter()
total_merged_rows = 0
wrote_merged_header = False

for m in months:
  pq_path = os.path.join(PARQUET_DIR, f"yellow_tripdata_{m}.parquet")
  if not os.path.exists(pq_path):
    print(f"[Cảnh báo] Không tìm thấy file: {pq_path}")
    continue

  single_csv = os.path.join(OUT_DIR, f"yellow_tripdata_{m}.csv")
  if os.path.exists(single_csv):
    os.remove(single_csv)

  pf = pq.ParquetFile(pq_path)
  month_rows = 0
  wrote_single_header = False

  # Đọc theo từng batch nhỏ để không tốn nhiều RAM
  for batch in pf.iter_batches(batch_size=200_000, columns=cols):
    df_chunk = batch.to_pandas()

    # Ghi vào file CSV riêng của tháng đó
    df_chunk.to_csv(
        single_csv,
        mode="a",
        header=not wrote_single_header,
        index=False,
    )
    wrote_single_header = True

    # Ghi nối vào file CSV gộp chung 3 tháng
    df_chunk.to_csv(
        merged_csv,
        mode="a",
        header=not wrote_merged_header,
        index=False,
    )
    wrote_merged_header = True

    month_rows += len(df_chunk)

  total_merged_rows += month_rows
  print(f"Tháng {m}: {month_rows:,} dòng -> đã xuất {single_csv}")

elapsed = time.perf_counter() - t0
merged_size_mb = (
    os.path.getsize(merged_csv) / (1024 * 1024)
    if os.path.exists(merged_csv)
    else 0
)
print("-" * 50)
print(f"File gộp: {merged_csv}")
print(f"Tổng số dòng gộp: {total_merged_rows:,} dòng | {merged_size_mb:.1f} MB")
print(f"Thời gian xử lý: {elapsed:.2f}s")