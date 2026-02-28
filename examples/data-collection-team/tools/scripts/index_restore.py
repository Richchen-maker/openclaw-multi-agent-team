#!/usr/bin/env python3
"""
生意参谋指数还原脚本
生意参谋显示的搜索人气、交易指数等是加密指数值，非真实值。
本脚本提供近似还原方法。

用法:
  python3 index_restore.py --value 150           # 还原单个值
  python3 index_restore.py --input data.csv --fields search_popularity,click_rate --output restored.csv

注意：还原公式是近似值，实际精度取决于校准数据。
"""

import sys
import csv
import json
import math
import os


def restore_index(index_value, field_type="popularity"):
    """
    生意参谋指数还原（近似算法）
    
    生意参谋的指数体系说明：
    - 搜索人气：反映搜索该关键词的人数（去重UV）
    - 点击率/转化率：显示的是百分比范围区间，非指数
    - 交易指数：反映成交金额
    
    指数与真实值的关系（近似）：
    - 指数范围 0-100: 真实值 ≈ 指数 × 1
    - 指数范围 100-1000: 真实值 ≈ 指数 × 5-10
    - 指数范围 1000-10000: 真实值 ≈ 指数 × 10-50
    - 指数范围 10000+: 真实值 ≈ 指数 × 50-100
    
    ⚠️ 这是粗略估算，不同类目、不同时期的系数不同。
    精确还原需要用已知数据点（如生意参谋专业版的真实值）做校准。
    """
    if index_value is None or index_value == "":
        return None
    
    try:
        val = float(index_value)
    except (ValueError, TypeError):
        return None
    
    if val <= 0:
        return 0
    
    if field_type == "popularity":
        # 搜索人气还原
        if val <= 100:
            return round(val * 1.0, 1)
        elif val <= 1000:
            return round(val * 7.5, 1)
        elif val <= 10000:
            return round(val * 25, 1)
        else:
            return round(val * 75, 1)
    
    elif field_type == "transaction":
        # 交易指数还原（金额，系数更大）
        if val <= 100:
            return round(val * 10, 1)
        elif val <= 1000:
            return round(val * 50, 1)
        elif val <= 10000:
            return round(val * 200, 1)
        else:
            return round(val * 500, 1)
    
    elif field_type in ("rate", "click_rate", "conversion_rate"):
        # 比率类：生意参谋通常直接显示百分比范围
        # 如 "20% ~ 25%"，取中位值
        return val  # 不需要还原，原值就是百分比
    
    else:
        # 通用还原
        if val <= 100:
            return round(val * 1.0, 1)
        elif val <= 1000:
            return round(val * 5, 1)
        else:
            return round(val * 20, 1)


def restore_csv(input_path, fields, output_path=None):
    """批量还原CSV文件中的指数字段"""
    if not os.path.exists(input_path):
        print(f"错误: 文件不存在 {input_path}")
        return
    
    with open(input_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames
    
    if not rows:
        print("错误: 文件为空")
        return
    
    # 添加还原后的字段
    new_fieldnames = list(fieldnames)
    for field in fields:
        est_field = f"{field}_estimated"
        if est_field not in new_fieldnames:
            new_fieldnames.append(est_field)
    
    # 还原
    for row in rows:
        for field in fields:
            val = row.get(field, "")
            field_type = "popularity"
            if "transaction" in field or "volume" in field:
                field_type = "transaction"
            elif "rate" in field:
                field_type = "rate"
            
            restored = restore_index(val, field_type)
            row[f"{field}_estimated"] = restored if restored is not None else ""
    
    # 输出
    if output_path is None:
        output_path = input_path.replace(".csv", "_restored.csv")
    
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=new_fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(json.dumps({
        "input": input_path,
        "output": output_path,
        "fields_restored": fields,
        "rows_processed": len(rows),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if "--value" in sys.argv:
        idx = sys.argv.index("--value")
        val = float(sys.argv[idx + 1])
        field_type = "popularity"
        if "--type" in sys.argv:
            field_type = sys.argv[sys.argv.index("--type") + 1]
        result = restore_index(val, field_type)
        print(f"指数值: {val} → 估算真实值: {result} (类型: {field_type})")
    
    elif "--input" in sys.argv:
        input_path = sys.argv[sys.argv.index("--input") + 1]
        fields = sys.argv[sys.argv.index("--fields") + 1].split(",") if "--fields" in sys.argv else ["search_popularity"]
        output_path = sys.argv[sys.argv.index("--output") + 1] if "--output" in sys.argv else None
        restore_csv(input_path, fields, output_path)
    
    else:
        print("用法:")
        print("  python3 index_restore.py --value 150 [--type popularity|transaction|rate]")
        print("  python3 index_restore.py --input data.csv --fields search_popularity,click_rate [--output restored.csv]")
