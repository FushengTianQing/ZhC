#!/usr/bin/env python3
"""
CI 复杂度分析脚本
解析 radon cc 的 JSON 输出，生成排名表格和统计信息。
"""

import json
import os
import sys


def main():
    data_path = "cc_data.json"
    env_path = "/tmp/cc_metrics.env"

    try:
        with open(data_path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        data = {}

    items = []
    for fp, funcs in data.items():
        for func in funcs:
            items.append({
                "complexity": func.get("complexity", 0),
                "name": func.get("name", "?"),
                "file": fp,
                "lineno": func.get("lineno", 0),
            })

    # 按复杂度降序排列
    items.sort(key=lambda x: x["complexity"], reverse=True)

    total = len(items)
    avg = sum(i["complexity"] for i in items) / total if total else 0
    hi = sum(1 for i in items if i["complexity"] > 15)
    vhi = sum(1 for i in items if i["complexity"] > 20)

    # 输出表格（写入 stdout，CI 会捕获）
    print("| 排名 | 函数 | 复杂度 | 文件 |")
    print("|------|------|--------|------|")

    for rank, item in enumerate(items[:20], 1):
        emoji = "🔴" if item["complexity"] > 20 else ("🟠" if item["complexity"] > 15 else "🟢")
        short_file = item["file"].replace("src/", "") if item["file"].startswith("src/") else item["file"]
        print(f"| {rank}. {emoji} | {item['name']} | **{item['complexity']}** | {short_file}:{item['lineno']} |")

    print()
    print(f"**总计**: {total} 个函数 | **平均复杂度**: {avg:.1f}")

    if vhi:
        print(f"> ⚠️ **{vhi} 个函数复杂度 > 20** (需优先重构)")
    elif hi:
        print(f"> ℹ️ **{hi} 个函数复杂度 > 15** (建议关注)")
    else:
        print("> ✅ 所有函数复杂度在合理范围")

    # 写入环境变量文件供后续 step 使用
    with open(env_path, "w") as f:
        f.write(f"total_functions={total}\n")
        f.write(f"avg_complexity={avg:.1f}\n")
        f.write(f"high_count={hi}\n")
        f.write(f"very_high_count={vhi}\n")


if __name__ == "__main__":
    main()
