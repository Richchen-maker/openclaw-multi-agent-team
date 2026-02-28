#!/usr/bin/env python3
"""
数据采集团队 Pipeline — 自动处理导出文件
REFINER(清洗) → WAREHOUSE(入库) → SENTINEL(校验) → ANALYST(报告)
"""

import json
import os
import sys
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path

# 路径配置
TEAM_DIR = Path(__file__).resolve().parent.parent.parent  # data-collection-team/
WAREHOUSE_DB = TEAM_DIR / "warehouse" / "warehouse.db"
RAW_DIR = TEAM_DIR / "warehouse" / "raw"
CLEANED_DIR = TEAM_DIR / "warehouse" / "cleaned"
ARCHIVE_DIR = TEAM_DIR / "warehouse" / "archive"
OUTPUT_DIR = TEAM_DIR / "output"
INCIDENTS_FILE = TEAM_DIR / "blackboard" / "INCIDENTS.md"

# 数据类型 → 表名映射
TYPE_MAP = {
    "search_keywords": "search_keywords",
    "market_overview": "market_overview",
    "competitors": "competitors",
}

# 必填字段（来自SCHEMA.md）
REQUIRED_FIELDS = {
    "search_keywords": ["keyword", "search_popularity", "click_rate", "payment_conversion_rate", "category", "platform", "collected_date", "data_period"],
    "market_overview": ["category", "date", "transaction_index", "platform", "collected_date"],
    "competitors": ["shop_name", "category", "platform", "collected_date"],
}


def detect_type(filename):
    """从文件名推断数据类型"""
    for key in TYPE_MAP:
        if key in filename:
            return key
    return None


def compute_hash(row):
    """生成行级去重哈希"""
    raw = json.dumps(row, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(raw.encode()).hexdigest()


# ============================================================
# REFINER — 清洗
# ============================================================
def refine(data, data_type):
    """清洗：类型转换、缺失字段检查、去重、指数还原"""
    required = REQUIRED_FIELDS.get(data_type, [])
    cleaned = []
    errors = []
    seen_hashes = set()

    for i, row in enumerate(data):
        # 必填字段检查
        missing = [f for f in required if f not in row or row[f] is None or row[f] == ""]
        if missing:
            errors.append(f"Row {i}: missing fields {missing}")
            continue

        # 去重
        h = compute_hash(row)
        if h in seen_hashes:
            continue
        seen_hashes.add(h)
        row["_hash"] = h

        # 类型标准化
        if data_type == "search_keywords":
            row["click_rate"] = float(row.get("click_rate", 0))
            row["payment_conversion_rate"] = float(row.get("payment_conversion_rate", 0))
            row["search_popularity"] = float(row.get("search_popularity", 0))
            # 指数还原（简化公式）
            row["search_popularity_estimated"] = round(row["search_popularity"] * 1.35, 1)

        elif data_type == "market_overview":
            row["transaction_index"] = float(row.get("transaction_index", 0))
            row["transaction_estimated"] = round(row["transaction_index"] * 2.1, 1)

        cleaned.append(row)

    return cleaned, errors


# ============================================================
# WAREHOUSE — 入库
# ============================================================
def init_db():
    """初始化SQLite表"""
    conn = sqlite3.connect(str(WAREHOUSE_DB))
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS search_keywords (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT, search_popularity REAL, search_popularity_estimated REAL,
        click_rate REAL, payment_conversion_rate REAL, online_product_count INTEGER,
        category TEXT, rank INTEGER, trend TEXT, platform TEXT,
        collected_date TEXT, data_period TEXT, _hash TEXT UNIQUE,
        inserted_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS market_overview (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT, date TEXT, transaction_index REAL, transaction_estimated REAL,
        volume_index REAL, avg_price REAL, buyer_count_index REAL,
        platform TEXT, collected_date TEXT, _hash TEXT UNIQUE,
        inserted_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS competitors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shop_name TEXT, shop_id TEXT, product_name TEXT, price REAL,
        sales_index REAL, category TEXT, platform TEXT, collected_date TEXT,
        _hash TEXT UNIQUE, inserted_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS pipeline_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_at TEXT, files_processed INTEGER, rows_inserted INTEGER,
        errors INTEGER, duration_ms INTEGER
    )""")

    conn.commit()
    return conn


def insert_rows(conn, table, rows):
    """插入数据，跳过重复。自动过滤表中不存在的列。"""
    if not rows:
        return 0
    # 获取表的实际列名
    c = conn.cursor()
    c.execute(f"PRAGMA table_info({table})")
    table_cols = {r[1] for r in c.fetchall()}

    # 只取数据中存在于表的列
    all_keys = [k for k in rows[0].keys() if (not k.startswith("_") or k == "_hash") and k in table_cols]
    if not all_keys:
        print(f"  ⚠️ No matching columns for table {table}")
        return 0
    placeholders = ",".join(["?"] * len(all_keys))
    col_names = ",".join(all_keys)
    inserted = 0
    for row in rows:
        vals = [row.get(col) for col in all_keys]
        try:
            c.execute(f"INSERT OR IGNORE INTO {table} ({col_names}) VALUES ({placeholders})", vals)
            if c.rowcount > 0:
                inserted += 1
        except sqlite3.Error as e:
            print(f"  ⚠️ Insert error: {e}")
    conn.commit()
    return inserted


# ============================================================
# SENTINEL — 校验
# ============================================================
def validate(conn):
    """数据质量检查"""
    issues = []
    c = conn.cursor()

    # 检查空表
    for table in TYPE_MAP.values():
        c.execute(f"SELECT COUNT(*) FROM {table}")
        count = c.fetchone()[0]
        if count == 0:
            issues.append(f"⚠️ 表 {table} 为空")

    # 检查搜索词异常值
    c.execute("SELECT keyword, search_popularity FROM search_keywords WHERE search_popularity > 100000")
    for row in c.fetchall():
        issues.append(f"⚠️ 异常搜索人气: {row[0]} = {row[1]}")

    # 检查点击率范围
    c.execute("SELECT keyword, click_rate FROM search_keywords WHERE click_rate > 1 OR click_rate < 0")
    for row in c.fetchall():
        issues.append(f"⚠️ 点击率越界: {row[0]} = {row[1]}")

    return issues


# ============================================================
# ANALYST — 报告
# ============================================================
def generate_report(conn, run_stats):
    """生成分析报告"""
    c = conn.cursor()
    report_lines = [
        f"# 数据采集报告",
        f"",
        f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**处理文件**: {run_stats['files']} 个",
        f"**入库行数**: {run_stats['inserted']} 行",
        f"**清洗错误**: {run_stats['errors']} 条",
        f"",
    ]

    # Top 10 搜索词
    c.execute("SELECT keyword, search_popularity, click_rate, trend FROM search_keywords ORDER BY search_popularity DESC LIMIT 10")
    rows = c.fetchall()
    if rows:
        report_lines.append("## 🔥 Top 10 搜索热词")
        report_lines.append("")
        report_lines.append("| 排名 | 关键词 | 搜索人气 | 点击率 | 趋势 |")
        report_lines.append("|------|--------|---------|--------|------|")
        for i, (kw, pop, cr, trend) in enumerate(rows, 1):
            report_lines.append(f"| {i} | {kw} | {pop:.0f} | {cr:.1%} | {trend or '-'} |")
        report_lines.append("")

    # 行业大盘摘要
    c.execute("""SELECT category, AVG(transaction_index), AVG(avg_price), COUNT(*)
                 FROM market_overview GROUP BY category""")
    rows = c.fetchall()
    if rows:
        report_lines.append("## 📊 行业大盘摘要")
        report_lines.append("")
        for cat, avg_tx, avg_price, cnt in rows:
            report_lines.append(f"- **{cat}**: 平均交易指数 {avg_tx:.0f}, 客单价 ¥{avg_price:.0f}, 数据点 {cnt}")
        report_lines.append("")

    # 蓝海机会（高转化 + 低竞争）
    c.execute("""SELECT keyword, search_popularity, payment_conversion_rate, online_product_count, click_rate, trend
                 FROM search_keywords
                 WHERE payment_conversion_rate > 0.10 AND online_product_count < 10000 AND search_popularity > 5000
                 ORDER BY payment_conversion_rate DESC LIMIT 5""")
    rows = c.fetchall()
    if rows:
        report_lines.append("## 💎 蓝海机会词（高转化 + 低竞争）")
        report_lines.append("")
        report_lines.append("| 关键词 | 搜索人气 | 转化率 | 在线商品数 | 点击率 | 趋势 |")
        report_lines.append("|--------|---------|--------|-----------|--------|------|")
        for kw, pop, cvr, count, cr, trend in rows:
            report_lines.append(f"| {kw} | {pop:.0f} | {cvr:.1%} | {count or '-'} | {cr:.1%} | {trend or '-'} |")
        report_lines.append("")

    # 竞品概览
    c.execute("SELECT shop_name, product_name, price, sales_index FROM competitors ORDER BY sales_index DESC LIMIT 5")
    rows = c.fetchall()
    if rows:
        report_lines.append("## 🏪 竞品 Top 5（按销量指数）")
        report_lines.append("")
        for shop, prod, price, sales in rows:
            report_lines.append(f"- **{shop}** | {prod} | ¥{price:.0f} | 销量指数 {sales:.0f}")
        report_lines.append("")

    report = "\n".join(report_lines)

    # 写入文件
    os.makedirs(str(OUTPUT_DIR), exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = OUTPUT_DIR / f"report_{ts}.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    return str(report_path), report


# ============================================================
# MAIN — Pipeline入口
# ============================================================
def process_files(input_dir):
    """处理指定目录下所有JSON文件"""
    input_path = Path(input_dir).expanduser()
    if not input_path.exists():
        print(f"❌ 目录不存在: {input_path}")
        return None

    json_files = sorted(input_path.glob("*.json"))
    if not json_files:
        print(f"📭 无新文件: {input_path}")
        return None

    print(f"🔍 发现 {len(json_files)} 个文件")

    # 确保目录存在
    for d in [RAW_DIR, CLEANED_DIR, ARCHIVE_DIR, OUTPUT_DIR]:
        os.makedirs(str(d), exist_ok=True)

    conn = init_db()
    start_time = datetime.now()
    total_inserted = 0
    total_errors = 0
    files_processed = 0

    for fp in json_files:
        data_type = detect_type(fp.name)
        if not data_type:
            print(f"  ⏭️ 跳过(未知类型): {fp.name}")
            continue

        print(f"\n📄 处理: {fp.name} (类型: {data_type})")

        # 读取
        with open(fp, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"  📥 读取 {len(data)} 行")

        # 备份原始文件
        raw_copy = RAW_DIR / fp.name
        with open(raw_copy, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # REFINER 清洗
        cleaned, errors = refine(data, data_type)
        print(f"  🧹 REFINER: {len(cleaned)} 行通过, {len(errors)} 行错误")
        total_errors += len(errors)

        if errors:
            for e in errors[:5]:
                print(f"    ⚠️ {e}")

        # 保存清洗后数据
        cleaned_path = CLEANED_DIR / fp.name
        with open(cleaned_path, "w", encoding="utf-8") as f:
            json.dump(cleaned, f, ensure_ascii=False, indent=2)

        # WAREHOUSE 入库
        table = TYPE_MAP[data_type]
        inserted = insert_rows(conn, table, cleaned)
        print(f"  💾 WAREHOUSE: {inserted} 行入库")
        total_inserted += inserted
        files_processed += 1

        # 归档原文件（从导出目录移走）
        archive_dest = ARCHIVE_DIR / fp.name
        fp.rename(archive_dest)
        print(f"  📦 已归档: {archive_dest.name}")

    # SENTINEL 校验
    print(f"\n🛡️ SENTINEL 校验中...")
    issues = validate(conn)
    if issues:
        print(f"  发现 {len(issues)} 个问题:")
        for iss in issues:
            print(f"    {iss}")
        # 写入INCIDENTS
        with open(INCIDENTS_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            for iss in issues:
                f.write(f"- {iss}\n")
    else:
        print("  ✅ 数据质量检查通过")

    # 记录运行日志
    duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
    conn.execute("INSERT INTO pipeline_runs (run_at, files_processed, rows_inserted, errors, duration_ms) VALUES (?,?,?,?,?)",
                 (datetime.now().isoformat(), files_processed, total_inserted, total_errors, duration_ms))
    conn.commit()

    # ANALYST 报告
    run_stats = {"files": files_processed, "inserted": total_inserted, "errors": total_errors}
    report_path, report_text = generate_report(conn, run_stats)
    print(f"\n📊 ANALYST 报告: {report_path}")

    conn.close()

    return {
        "files": files_processed,
        "inserted": total_inserted,
        "errors": total_errors,
        "duration_ms": duration_ms,
        "report_path": report_path,
        "report": report_text,
        "issues": issues,
    }


if __name__ == "__main__":
    input_dir = sys.argv[1] if len(sys.argv) > 1 else "~/Downloads/sycm-data"
    result = process_files(input_dir)
    if result:
        print(f"\n{'='*50}")
        print(f"✅ Pipeline完成: {result['files']}文件, {result['inserted']}行入库, {result['errors']}错误, {result['duration_ms']}ms")
    else:
        print("Pipeline: 无数据处理")
