#!/usr/bin/env python3
"""
数据校验脚本 — 检查CSV文件的字段完整性、空值率、值域
用法: python3 validator.py <csv_file> [--schema <schema_type>]
schema_type: search_keywords | market_overview | competitor
"""

import csv
import sys
import json
import os
from collections import defaultdict

# 字段定义
SCHEMAS = {
    "search_keywords": {
        "required": ["keyword", "search_popularity", "click_rate", "payment_conversion_rate", "category", "platform", "collected_date"],
        "numeric": ["search_popularity", "click_rate", "payment_conversion_rate", "online_product_count", "rank"],
        "range": {
            "click_rate": (0, 1),
            "payment_conversion_rate": (0, 1),
            "search_popularity": (0, None),
            "rank": (1, None),
        }
    },
    "market_overview": {
        "required": ["category", "date", "transaction_index", "platform", "collected_date"],
        "numeric": ["transaction_index", "volume_index", "avg_price", "buyer_count_index"],
        "range": {
            "transaction_index": (0, None),
            "avg_price": (0, None),
        }
    },
    "competitor": {
        "required": ["shop_name", "category", "platform", "collected_date"],
        "numeric": ["price", "sales_index"],
        "range": {
            "price": (0, None),
        }
    }
}


def validate(filepath, schema_type=None):
    if not os.path.exists(filepath):
        print(json.dumps({"valid": False, "error": f"文件不存在: {filepath}"}))
        return False

    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print(json.dumps({"valid": False, "error": "文件为空（0行数据）"}))
        return False

    fields = list(rows[0].keys())
    total = len(rows)
    report = {
        "valid": True,
        "file": filepath,
        "total_rows": total,
        "fields": fields,
        "field_count": len(fields),
        "issues": [],
        "null_rates": {},
        "range_violations": {},
    }

    # 空值统计
    null_counts = defaultdict(int)
    for row in rows:
        for field in fields:
            val = row.get(field, "")
            if val is None or str(val).strip() == "":
                null_counts[field] += 1

    for field in fields:
        rate = null_counts[field] / total if total > 0 else 0
        report["null_rates"][field] = round(rate, 4)
        if rate > 0.5:
            report["issues"].append(f"⚠️ 字段 '{field}' 空值率 {rate:.1%} 超过50%")

    # Schema校验
    if schema_type and schema_type in SCHEMAS:
        schema = SCHEMAS[schema_type]

        # 必填字段检查
        for req in schema["required"]:
            if req not in fields:
                report["issues"].append(f"❌ 缺少必填字段: {req}")
                report["valid"] = False

        # 值域检查
        range_violations = defaultdict(int)
        for row in rows:
            for field, (lo, hi) in schema.get("range", {}).items():
                val = row.get(field, "")
                if val is None or str(val).strip() == "":
                    continue
                try:
                    num = float(val)
                    if lo is not None and num < lo:
                        range_violations[field] += 1
                    if hi is not None and num > hi:
                        range_violations[field] += 1
                except ValueError:
                    range_violations[field] += 1

        for field, count in range_violations.items():
            report["range_violations"][field] = count
            if count > 0:
                report["issues"].append(f"⚠️ 字段 '{field}' 有 {count} 行值域异常")

    if not report["issues"]:
        report["issues"] = ["✅ 全部检查通过"]

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report["valid"]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 validator.py <csv_file> [--schema search_keywords|market_overview|competitor]")
        sys.exit(1)

    filepath = sys.argv[1]
    schema_type = None
    if "--schema" in sys.argv:
        idx = sys.argv.index("--schema")
        if idx + 1 < len(sys.argv):
            schema_type = sys.argv[idx + 1]

    valid = validate(filepath, schema_type)
    sys.exit(0 if valid else 1)
