#!/bin/bash
# CI 安全扫描脚本 - Bandit 检查
# 用途: 在 GitHub Actions 中运行 Bandit 安全扫描并生成报告

set -o pipefail

echo "## 🔒 安全扫描 (Bandit)" >> $GITHUB_STEP_SUMMARY
echo '' >> $GITHUB_STEP_SUMMARY

# 运行 bandit 并输出 JSON
bandit -r src/ -f json -ll --skip B101 > bandit_result.json 2>/dev/null || true

# 解析结果（使用 Python 避免复杂的 shell 解析）
python3 << 'PYEOF'
import json

try:
    with open("bandit_result.json") as f:
        data = json.load(f)
    results = data.get("results", [])
except (json.JSONDecodeError, FileNotFoundError):
    results = []

high = sum(1 for r in results if r.get("issue_severity") == "HIGH")
medium = sum(1 for r in results if r.get("issue_severity") == "MEDIUM")
low = sum(1 for r in results if r.get("issue_severity") == "LOW")

with open("/tmp/security_metrics.env", "w") as f:
    f.write(f"high_count={high}\n")
    f.write(f"medium_count={medium}\n")
    f.write(f"low_count={low}\n")

print(f"| 级别 | 数量 |")
print(f"|------|------|")
print(f"| 🔴 HIGH | {high} |")
print(f"| 🟡 MEDIUM | {medium} |")
print(f"| 🟢 LOW | {low} |")
PYEOF

# 将表格写入 summary
python3 -c "
with open('/tmp/security_metrics.env') as f:
    for line in f:
        print(line.strip())
" >> $GITHUB_STEP_SUMMARY

echo '' >> $GITHUB_STEP_SUMMARY

# 读取高危数量
HIGH=$(grep "^high_count=" /tmp/security_metrics.env | cut -d= -f2)

if [ "$HIGH" -gt 0 ]; then
    echo "❌ **存在 ${HIGH} 个高危安全问题**" >> $GITHUB_STEP_SUMMARY
    echo '```' >> $GITHUB_STEP_SUMMARY
    bandit -r src/ -ll --skip B101 2>&1 | head -20 >> $GITHUB_STEP_SUMMARY || true
    echo '```' >> $GITHUB_STEP_SUMMARY
    echo "status=fail" >> $GITHUB_OUTPUT
    echo "high_count=${HIGH}" >> $GITHUB_OUTPUT
    exit 1
else
    echo "✅ **无高危安全问题**" >> $GITHUB_STEP_SUMMARY
    echo "status=pass" >> $GITHUB_OUTPUT
    echo "high_count=0" >> $GITHUB_OUTPUT
fi
