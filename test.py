import csv
import os
from pathlib import Path
import sqlite3
import time

# 1. Thiết lập đường dẫn an toàn (tự tìm file CSV ở thư mục hiện tại hoặc thư mục chứa script)
BASE_DIR = Path(__file__).resolve().parent
CANDIDATE_CSVS = [
    BASE_DIR / "yellow_tripdata_2024-02.csv",
    BASE_DIR.parent / "yellow_tripdata_2024-02.csv",
    BASE_DIR.parent / "csv_output" / "yellow_tripdata_2024-02.csv",
]

INPUT_CSV = next((p for p in CANDIDATE_CSVS if p.exists()), CANDIDATE_CSVS[0])

# Lưu file db output ở thư mục cha CSDL (nếu script nằm trong .venv) cho gọn
OUTPUT_DIR = BASE_DIR.parent if BASE_DIR.name == ".venv" else BASE_DIR
DB_ROW = OUTPUT_DIR / "compare_row.sqlite"
DB_BATCH = OUTPUT_DIR / "compare_batch.sqlite"

BATCH_SIZE = 25000
MAX_ROWS = (
    50000  # Đổi thành None nếu muốn chạy toàn bộ file (row-by-row sẽ lâu)
)


def init_db(db_path: Path) -> sqlite3.Connection:
  if db_path.exists():
    db_path.unlink()
  conn = sqlite3.connect(db_path)
  cur = conn.cursor()
  cur.execute("""
        CREATE TABLE trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id INTEGER,
            passenger_count REAL,
            trip_distance REAL,
            fare_amount REAL,
            total_amount REAL
        );
    """)
  conn.commit()
  return conn


def extract_values(row: dict) -> tuple:
  def to_int(val):
    try:
      return int(float(val)) if val not in (None, "") else None
    except ValueError:
      return None

  def to_float(val):
    try:
      return float(val) if val not in (None, "") else None
    except ValueError:
      return None

  return (
      to_int(row.get("VendorID")),
      to_float(row.get("passenger_count")),
      to_float(row.get("trip_distance")),
      to_float(row.get("fare_amount")),
      to_float(row.get("total_amount")),
  )


def cách_1_row_by_row(csv_path: Path, db_path: Path, max_rows=None):
  """Cách 1: Insert và commit từng dòng một."""
  conn = init_db(db_path)
  cur = conn.cursor()
  sql = """
        INSERT INTO trips (vendor_id, passenger_count, trip_distance, fare_amount, total_amount)
        VALUES (?, ?, ?, ?, ?);
    """

  count = 0
  t0 = time.perf_counter()

  with open(
      csv_path, mode="r", encoding="utf-8-sig", errors="replace", newline=""
  ) as f:
    reader = csv.DictReader(f)
    for row in reader:
      cur.execute(sql, extract_values(row))
      conn.commit()
      count += 1
      if max_rows is not None and count >= max_rows:
        break

  elapsed = time.perf_counter() - t0
  conn.close()
  return count, elapsed


def cách_2_batch(
    csv_path: Path, db_path: Path, batch_size=25000, max_rows=None
):
  """Cách 2: Gom từng lô (batch) rồi executemany + commit."""
  conn = init_db(db_path)
  cur = conn.cursor()
  sql = """
        INSERT INTO trips (vendor_id, passenger_count, trip_distance, fare_amount, total_amount)
        VALUES (?, ?, ?, ?, ?);
    """

  buffer = []
  count = 0
  t0 = time.perf_counter()

  with open(
      csv_path, mode="r", encoding="utf-8-sig", errors="replace", newline=""
  ) as f:
    reader = csv.DictReader(f)
    for row in reader:
      buffer.append(extract_values(row))
      count += 1

      if len(buffer) >= batch_size:
        cur.executemany(sql, buffer)
        conn.commit()
        buffer.clear()

      if max_rows is not None and count >= max_rows:
        break

    if buffer:
      cur.executemany(sql, buffer)
      conn.commit()

  elapsed = time.perf_counter() - t0
  conn.close()
  return count, elapsed


def check_result(db_path: Path):
  conn = sqlite3.connect(db_path)
  cur = conn.cursor()
  total_rows, sum_dist, sum_total = cur.execute("""
        SELECT
            COUNT(*),
            COALESCE(SUM(trip_distance), 0),
            COALESCE(SUM(total_amount), 0)
        FROM trips;
    """).fetchone()
  conn.close()
  size_mb = os.path.getsize(db_path) / (1024 * 1024)
  return total_rows, sum_dist, sum_total, size_mb


def main():
  if not INPUT_CSV.exists():
    print(f"Không tìm thấy file CSV. Đã kiểm tra: {CANDIDATE_CSVS}")
    return

  print(f"File đầu vào chung : {INPUT_CSV}")
  print(f"Giới hạn dòng test  : {MAX_ROWS if MAX_ROWS else 'Toàn bộ file'}")
  print(f"Batch size         : {BATCH_SIZE}\n")

  n1, t1 = cách_1_row_by_row(INPUT_CSV, DB_ROW, MAX_ROWS)
  n2, t2 = cách_2_batch(INPUT_CSV, DB_BATCH, BATCH_SIZE, MAX_ROWS)

  r1, dist1, tot1, sz1 = check_result(DB_ROW)
  r2, dist2, tot2, sz2 = check_result(DB_BATCH)

  print("=" * 45)
  print(f"Cách 1 (Row-by-Row) : {t1:7.2f}s | {r1:,} dòng | {sz1:.2f} MB")
  print(f"Cách 2 (Batch)      : {t2:7.2f}s | {r2:,} dòng | {sz2:.2f} MB")
  print("=" * 45)
  if t2 > 0:
    print(f"Batch nhanh hơn     : {t1 / t2:.1f}x")
  print(f"Khớp số dòng        : {r1 == r2}")
  print(f"Khớp tổng quãng đg  : {abs(dist1 - dist2) < 1e-6}")
  print(f"Khớp tổng tiền      : {abs(tot1 - tot2) < 1e-6}")


if __name__ == "__main__":
  main()