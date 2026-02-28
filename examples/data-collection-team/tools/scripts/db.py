#!/usr/bin/env python3
"""
SQLite数据仓库管理脚本
用法:
  python3 db.py init                              # 初始化数据库
  python3 db.py import --file data.csv --table search_keywords
  python3 db.py query --sql "SELECT * FROM search_keywords LIMIT 10"
  python3 db.py stats                             # 数据库统计
  python3 db.py export --table search_keywords --output export.csv
"""

import sqlite3
import csv
import json
import sys
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "warehouse", "warehouse.db")


def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    """初始化数据库表"""
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS search_keywords (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT NOT NULL,
        search_popularity REAL,
        search_popularity_estimated REAL,
        click_rate REAL,
        payment_conversion_rate REAL,
        online_product_count INTEGER,
        category TEXT,
        category_id TEXT,
        rank INTEGER,
        trend TEXT,
        platform TEXT NOT NULL,
        collected_date TEXT NOT NULL,
        data_period TEXT,
        imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(keyword, category, platform, collected_date)
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS market_overview (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        category_id TEXT,
        date TEXT NOT NULL,
        transaction_index REAL,
        transaction_estimated REAL,
        volume_index REAL,
        avg_price REAL,
        buyer_count_index REAL,
        platform TEXT NOT NULL,
        collected_date TEXT NOT NULL,
        imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(category, date, platform, collected_date)
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS competitor (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shop_name TEXT NOT NULL,
        shop_id TEXT,
        product_name TEXT,
        price REAL,
        sales_index REAL,
        category TEXT,
        platform TEXT NOT NULL,
        collected_date TEXT NOT NULL,
        imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS collection_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT NOT NULL,
        platform TEXT,
        data_type TEXT,
        rows_imported INTEGER,
        source_file TEXT,
        imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()
    print(json.dumps({"action": "init", "status": "success", "db_path": DB_PATH}, ensure_ascii=False))


def import_csv(filepath, table_name):
    """导入CSV到指定表"""
    if not os.path.exists(filepath):
        print(json.dumps({"error": f"文件不存在: {filepath}"}))
        return

    conn = get_conn()
    c = conn.cursor()

    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print(json.dumps({"error": "CSV为空"}))
        return

    # 获取表的列名
    c.execute(f"PRAGMA table_info({table_name})")
    table_cols = {row[1] for row in c.fetchall()}

    # 只导入表中存在的列
    csv_cols = [col for col in rows[0].keys() if col in table_cols]
    if not csv_cols:
        print(json.dumps({"error": "CSV字段与表字段无交集"}))
        return

    placeholders = ",".join(["?"] * len(csv_cols))
    col_names = ",".join(csv_cols)

    imported = 0
    skipped = 0
    for row in rows:
        values = []
        for col in csv_cols:
            val = row.get(col, "")
            if val == "" or val is None:
                values.append(None)
            else:
                values.append(val)
        try:
            c.execute(f"INSERT OR IGNORE INTO {table_name} ({col_names}) VALUES ({placeholders})", values)
            if c.rowcount > 0:
                imported += 1
            else:
                skipped += 1
        except sqlite3.Error as e:
            skipped += 1

    # 记录导入日志
    task_id = os.path.basename(filepath).replace(".csv", "")
    c.execute(
        "INSERT INTO collection_log (task_id, platform, data_type, rows_imported, source_file) VALUES (?,?,?,?,?)",
        (task_id, "", table_name, imported, filepath)
    )

    conn.commit()
    conn.close()

    print(json.dumps({
        "action": "import",
        "table": table_name,
        "file": filepath,
        "imported": imported,
        "skipped": skipped,
        "total": len(rows),
    }, ensure_ascii=False, indent=2))


def query_db(sql):
    """执行SQL查询"""
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(sql)
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    print(json.dumps(rows, ensure_ascii=False, indent=2, default=str))


def stats():
    """数据库统计"""
    conn = get_conn()
    c = conn.cursor()

    tables = ["search_keywords", "market_overview", "competitor", "collection_log"]
    result = {"db_path": DB_PATH, "tables": {}}

    for table in tables:
        try:
            c.execute(f"SELECT COUNT(*) FROM {table}")
            count = c.fetchone()[0]
            result["tables"][table] = count
        except sqlite3.OperationalError:
            result["tables"][table] = "表不存在"

    # 数据库文件大小
    if os.path.exists(DB_PATH):
        size = os.path.getsize(DB_PATH)
        result["db_size_bytes"] = size
        result["db_size_mb"] = round(size / 1024 / 1024, 2)

    conn.close()
    print(json.dumps(result, ensure_ascii=False, indent=2))


def export_table(table_name, output_path):
    """导出表为CSV"""
    conn = get_conn()
    c = conn.cursor()
    c.execute(f"SELECT * FROM {table_name}")
    rows = c.fetchall()
    cols = [desc[0] for desc in c.description]
    conn.close()

    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(cols)
        writer.writerows(rows)

    print(json.dumps({"action": "export", "table": table_name, "output": output_path, "rows": len(rows)}, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 db.py init|import|query|stats|export")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "init":
        init_db()
    elif cmd == "import":
        filepath = sys.argv[sys.argv.index("--file") + 1]
        table = sys.argv[sys.argv.index("--table") + 1]
        import_csv(filepath, table)
    elif cmd == "query":
        sql = sys.argv[sys.argv.index("--sql") + 1]
        query_db(sql)
    elif cmd == "stats":
        stats()
    elif cmd == "export":
        table = sys.argv[sys.argv.index("--table") + 1]
        output = sys.argv[sys.argv.index("--output") + 1]
        export_table(table, output)
    else:
        print(f"未知命令: {cmd}")
