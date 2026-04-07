#!/bin/bash
# =============================================================================
# ZHC 本地预检脚本 - 提交前必须通过
# =============================================================================
# 用途: 在 git commit/push 前运行，确保代码符合质量标准
# 用法: bash scripts/pre-commit-check.sh
#       或: chmod +x scripts/pre-commit-check.sh && ./scripts/pre-commit-check.sh
#
# 对应 CI 的 P0 检查项，本地先过一遍，避免 CI 失败浪费时间
# =============================================================================
set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# 计数器
PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

# 工具函数
pass_msg() { echo -e "  ${GREEN}✅ $1${NC}"; PASS_COUNT=$((PASS_COUNT + 1)); }
fail_msg() { echo -e "  ${RED}❌ $1${NC}"; FAIL_COUNT=$((FAIL_COUNT + 1)); }
warn_msg() { echo -e "  ${YELLOW}⚠️  $1${NC}"; WARN_COUNT=$((WARN_COUNT + 1)); }
section() { echo -e "\n${BLUE}${BOLD}━━━ $1 ━━━${NC}\n"; }

echo ""
echo -e "${BOLD}${BLUE}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${BLUE}║     🔍 ZHC 质量门禁 - 本地预检 (Level 0)        ║${NC}"
echo -e "${BOLD}${BLUE}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# 确保在项目根目录
if [ ! -f "pyproject.toml" ]; then
    echo "❌ 请在 ZHC 项目根目录下运行此脚本"
    exit 1
fi

PROJECT_ROOT=$(pwd)
cd "$PROJECT_ROOT"

# ============================================================================
section "1/5 ⬛ Black 格式化检查"
# ============================================================================
if command -v black &>/dev/null; then
    if black --check src/ tests/ scripts/ --diff 2>&1; then
        pass_msg "格式化检查通过 ✨"
    else
        fail_msg "格式化未通过！请运行: black src/ tests/ scripts/"
    fi
else
    warn_msg "Black 未安装，跳过。安装: pip install black"
fi

# ============================================================================
section "2/5 🧹 Ruff Lint 检查"
# ============================================================================
if command -v ruff &>/dev/null; then
    RUFF_OUTPUT=$(ruff check src/ tests/ scripts/ 2>&1 || true)
    ERROR_COUNT=$(ruff check src/ tests/ scripts/ --output-format=json 2>/dev/null | python3 -c "
import json, sys
try:
    errors = json.load(sys.stdin)
    # 统计 E(错误) 和 F(严重错误)
    count = sum(1 for e in errors if e.get('code','').startswith(('E', 'F')))
    print(count)
except: print(0)
" 2>/dev/null || echo "0")

    if [ "$ERROR_COUNT" -eq 0 ]; then
        pass_msg "Lint 检查通过，0 个错误"
    else
        fail_msg "发现 ${ERROR_COUNT} 个 Lint 错误！请运行: ruff check --fix src/ tests/ scripts/"
        echo -e "  ${YELLOW}详情:${NC}"
        echo "$RUFF_OUTPUT" | head -15 | sed 's/^/    /'
    fi
else
    warn_msg "Ruff 未安装，跳过。安装: pip install ruff"
fi

# ============================================================================
section "3/5 🔎 MyPy 类型检查"
# ============================================================================
if command -v mypy &>/dev/null; then
    MYPY_OUTPUT=$(mypy src/ --ignore-missing-imports --no-error-summary 2>&1 || true)
    TYPE_ERRORS=$(echo "$MYPY_OUTPUT" | grep -c "^src/" 2>/dev/null || echo "0")

    if [ "$TYPE_ERRORS" -eq 0 ]; then
        pass_msg "类型检查通过，0 个类型错误"
    else
        fail_msg "发现 ${TYPE_ERRORS} 个类型错误！"
        echo -e "  ${YELLOW}前 10 个错误:${NC}"
        echo "$MYPY_OUTPUT" | head -10 | sed 's/^/    /'
    fi
else
    warn_msg "MyPy 未安装，跳过。安装: pip install mypy"
fi

# ============================================================================
section "4/5 🧪 单元测试"
# ============================================================================
if command -v pytest &>/dev/null; then
    echo "  运行测试中..."
    TEST_OUTPUT=$(python3 -m pytest tests/ -x -q --tb=short 2>&1) || true

    # 解析结果
    PASSED=$(echo "$TEST_OUTPUT" | grep -o "[0-9]* passed" | grep -o "[0-9]*" || echo "0")
    FAILED=$(echo "$TEST_OUTPUT" | grep -o "[0-9]* failed" | grep -o "[0-9]*" || echo "0")
    ERRORS=$(echo "$TEST_OUTPUT" | grep -o "[0-9]* error" | grep -o "[0-9]*" || echo "0")

    TOTAL_FAIL=$((FAILED + ERRORS))
    if [ "$TOTAL_FAIL" -eq 0 ]; then
        pass_msg "测试全部通过 (${PASSED} passed)"
    else
        fail_msg "测试失败: ${PASSED} passed, ${FAILED} failed, ${ERRORS} error(s)"
    fi
else
    warn_msg "Pytest 未安装，跳过。安装: pip install pytest"
fi

# ============================================================================
section "5/5 📊 覆盖率快照（仅供参考）"
# ============================================================================
if command -v pytest &>/dev/null; then
    COV_OUTPUT=$(python3 -m pytest tests/ --cov=src --cov-report=term-missing -q --no-header 2>&1 || true)
    COV_LINE=$(echo "$COV_OUTPUT" | grep "TOTAL" | tail -1)

    if [ -n "$COV_LINE" ]; then
        COV_PCT=$(echo "$COV_LINE" | awk '{print $NF}' | tr -d '%')
        THRESHOLD=15

        echo "  当前覆盖率: ${COV_PCT}% | 门禁: ${THRESHOLD}% | 目标: 60%"

        # 可视化进度条
        FILLED=$((COV_PCT * 4 / 100))
        EMPTY=$((40 - FILLED))
        BAR=""
        for i in $(seq 1 $FILLED 2>/dev/null); do BAR="${BAR}█"; done
        for i in $(seq 1 $EMPTY 2>/dev/null); do BAR="${BAR}░"; done
        echo -e "  ${BLUE}${BAR}${NC} ${COV_PCT}%"

        # 进度提示
        if [ "$COV_PCT" -lt "$THRESHOLD" ]; then
            warn_msg "覆盖率低于门槛 (${THRESHOLD}%)，但当前仅作为参考不阻断"
        else
            pass_msg "覆盖率 ${COV_PCT}% 达到门槛 (${THRESHOLD}%)"
        fi

        echo -e "  ${YELLOW}> 路线图: 15% → 25%(W1) → 38%(W2) → 50%(W3) → 60%+${NC}"
    else
        warn_msg "无法获取覆盖率数据"
    fi
else
    warn_msg "Pytest 未安装，跳过覆盖率检查"
fi

# ============================================================================
# 最终汇总
# ============================================================================
TOTAL=$((PASS_COUNT + FAIL_COUNT))

echo ""
echo -e "${BOLD}${BLUE}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${BLUE}║               🏁 预检结果汇总                   ║${NC}"
echo -e "${BOLD}${BLUE}╠══════════════════════════════════════════════════╣${NC}"

printf "${BOLD}${BLUE}║${NC}   通过: ${GREEN}%-8s${NC}${BOLD}${BLUE}  失败: %-8s${BOLD}${BLUE} 警告: %-6s${BOLD}${BLUE}   ║\n" \
    "${PASS_COUNT}" "${FAIL_COUNT}" "${WARN_COUNT}"

echo -e "${BOLD}${BLUE}╚══════════════════════════════════════════════════╝${NC}"
echo ""

if [ "$FAIL_COUNT" -eq 0 ]; then
    echo -e "${GREEN}${BOLD}🎉 全部通过！可以安全提交。${NC}"
    exit 0
elif [ "$FAIL_COUNT" -le 2 ]; then
    echo -e "${YELLOW}${BOLD}⚠️  有 ${FAIL_COUNT} 项未通过，建议修复后再提交。${NC}"
    exit 1
else
    echo -e "${RED}${BOLD}❌ 有 ${FAIL_COUNT} 项未通过，必须修复后才能提交！${NC}"
    exit 1
fi
