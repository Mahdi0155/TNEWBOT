import sqlite3

conn = sqlite3.connect("videos.db", check_same_thread=False)
cur = conn.cursor()

# جدول ذخیره ویدیوهای هر پک (هر code ممکنه چند ویدیو داشته باشه)
cur.execute("""
CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,
    file_id TEXT NOT NULL,
    downloads INTEGER DEFAULT 0
)
""")

# جدول ذخیره کانال‌های عضویت اجباری
cur.execute("""
CREATE TABLE IF NOT EXISTS required_channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE
)
""")

conn.commit()

# ذخیره یک ویدیو برای یک code خاص
def save_file(file_id, code):
    cur.execute("INSERT INTO videos (code, file_id) VALUES (?, ?)", (code, file_id))
    conn.commit()

# دریافت تمام فایل‌ها برای یک code (برای ارسال پک کامل)
def get_files(code):
    cur.execute("SELECT file_id FROM videos WHERE code = ?", (code,))
    return [row[0] for row in cur.fetchall()]

# افزایش شمارنده دانلود هر فایل در پک
def increment_downloads(code):
    cur.execute("UPDATE videos SET downloads = downloads + 1 WHERE code = ?", (code,))
    conn.commit()

# دریافت تعداد دانلود یک پک
def get_download_count(code):
    cur.execute("SELECT MAX(downloads) FROM videos WHERE code = ?", (code,))
    row = cur.fetchone()
    return row[0] if row and row[0] else 0

# افزودن کانال عضویت
def add_channel(username):
    cur.execute("INSERT OR IGNORE INTO required_channels (username) VALUES (?)", (username,))
    conn.commit()

# حذف کانال عضویت
def remove_channel(username):
    cur.execute("DELETE FROM required_channels WHERE username = ?", (username,))
    conn.commit()

# دریافت لیست کانال‌های عضویت اجباری
def get_required_channels():
    cur.execute("SELECT username FROM required_channels")
    return [row[0] for row in cur.fetchall()]
