#!/usr/bin/env python3
"""
数据资产目录生成器
扫描 warehouse/ 目录，自动生成 INDEX.md

用法: python3 index_generator.py
"""

import os
import csv
import json
from datetime import datetime
from collections import defaultdict

WAREHOUSE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "warehouse")
INDEX_PATH = os.path.join(WAREHOUSE_DIR, "INDEX.md")


def scan_warehouse():
    """扫描warehouse目录，收集数据集信息"""
    datasets = []

    cleaned_dir = os.path.join(WAREHOUSE_DIR, "cleaned")
    if not os.path.exists(cleaned_dir):
        return datasets

    for platform in os.listdir(cleaned_dir):
        platform_dir = os.path.join(cleaned_dir, platform)
        if not os.path.isdir(platform_dir):
            continue

        for date_dir_name in sorted(os.listdir(platform_dir), reverse=True):
            date_dir = os.path.join(platform_dir, date_dir_name)
            if not os.path.isdir(date_dir):
                continue

            for filename in os.listdir(date_dir):
                if not filename.endswith(".csv"):
                    continue
                if filename.endswith("_report.json"):
                    continue

                filepath = os.path.join(date_dir, filename)
                task_id = filename.replace(".csv", "")

                # 读取行数和字段
                row_count = 0
                fields = []
                try:
                    with open(filepath, 'r', encoding='utf-8-sig') as f:
                        reader = csv.DictReader(f)
                        fields = reader.fieldnames or []
                        for _ in reader:
                            row_count += 1
                except Exception:
                    pass

                # 读取清洗报告（如有）
                report_path = filepath.replace(".csv", "_report.json")
                report = {}
                if os.path.exists(report_path):
                    try:
                        with open(report_path, 'r') as f:
                            report = json.load(f)
                    except Exception:
                        pass

                # 文件大小
                size_bytes = os.path.getsize(filepath)
                size_kb = round(size_bytes / 1024, 1)

                datasets.append({
                    "task_id": task_id,
                    "platform": platform,
                    "date": date_dir_name,
                    "row_count": row_count,
                    "field_count": len(fields),
                    "size_kb": size_kb,
                    "path": os.path.relpath(filepath, WAREHOUSE_DIR),
                    "report": report,
                })

    return datasets


def generate_index(datasets):
    """生成INDEX.md"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        "# 数据资产目录",
        f"> 自动生成于 {now}",
        "",
    ]

    if not datasets:
        lines.append("暂无数据。运行数据采集团队开始采集。")
        return "\n".join(lines)

    # 总览
    total_rows = sum(d["row_count"] for d in datasets)
    total_size = sum(d["size_kb"] for d in datasets)
    lines.append(f"## 总览")
    lines.append(f"- 数据集数量: {len(datasets)}")
    lines.append(f"- 总数据行数: {total_rows:,}")
    lines.append(f"- 总存储大小: {total_size:.1f} KB")
    lines.append("")

    # 最近更新
    lines.append("## 最近更新")
    lines.append("| 数据集ID | 平台 | 日期 | 行数 | 大小 | 路径 |")
    lines.append("|----------|------|------|------|------|------|")
    for d in datasets[:20]:  # 最近20条
        lines.append(f"| {d['task_id']} | {d['platform']} | {d['date']} | {d['row_count']} | {d['size_kb']}KB | `{d['path']}` |")
    lines.append("")

    # 按平台汇总
    by_platform = defaultdict(lambda: {"count": 0, "rows": 0, "latest": ""})
    for d in datasets:
        p = by_platform[d["platform"]]
        p["count"] += 1
        p["rows"] += d["row_count"]
        if d["date"] > p["latest"]:
            p["latest"] = d["date"]

    lines.append("## 按平台汇总")
    for platform, info in sorted(by_platform.items()):
        lines.append(f"- **{platform}**: {info['count']}个数据集, {info['rows']:,}行, 最近更新 {info['latest']}")
    lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    datasets = scan_warehouse()
    content = generate_index(datasets)

    with open(INDEX_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"INDEX.md 已更新: {INDEX_PATH}")
    print(f"数据集: {len(datasets)}, 总行数: {sum(d['row_count'] for d in datasets):,}")
