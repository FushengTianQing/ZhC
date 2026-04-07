#!/usr/bin/env python3
"""
ZHC 代码质量评分器
==================
对代码库进行多维度质量评分，输出可读性强的报告。

用法:
    python3 scripts/quality-score.py          # 全量评分
    python3 scripts/quality-score.py src/ir/  # 指定目录
    python3 scripts/quality-score.py --json   # JSON 格式输出

评分维度 (总分 100):
    - 测试覆盖率     (20 分) - 当前覆盖率 vs 目标 60%
    - 圈复杂度       (15 分) - 平均复杂度，目标 < 8
    - Lint 质量      (15 分) - Ruff 错误数
    - 类型注解       (10 分) - MyPy 错误率
    - 函数长度       (10 分) - 平均函数行数，目标 < 30 行
    - 文档完整性     (10 分) - 公共 API 的 docstring 覆盖
    - 安全扫描       (10 分) - Bandit 高危问题
    - 重复代码       (10 分) - 代码重复率

创建日期: 2026-04-08
维护者: ZHC 开发团队
"""

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# =============================================================================
# 数据结构
# =============================================================================

@dataclass
class DimensionScore:
    """单个维度的评分结果"""
    name: str                    # 维度名称
    score: float                 # 得分 (0-维度满分)
    max_score: float             # 该维度满分
    detail: str                  # 详细说明
    status: str = "info"         # info / warn / fail / pass


@dataclass
class QualityReport:
    """完整质量报告"""
    dimensions: List[DimensionScore] = field(default_factory=list)
    total_score: float = 0.0
    total_max: float = 100.0
    grade: str = "N/A"
    summary: str = ""
    timestamp: str = ""

    def to_dict(self) -> dict:
        return {
            "total_score": self.total_score,
            "total_max": self.total_max,
            "grade": self.grade,
            "summary": self.summary,
            "dimensions": [
                {"name": d.name, "score": d.score, "max": d.max_score,
                 "detail": d.detail, "status": d.status}
                for d in self.dimensions
            ]
        }


# =============================================================================
# 工具函数
# =============================================================================

def run_command(cmd: List[str], cwd=None, timeout=30) -> Tuple[int, str]:
    """运行命令并返回退出码和输出"""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout
        )
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return -1, "命令超时"
    except FileNotFoundError:
        return -1, f"未找到命令: {cmd[0]}"


def find_python_files(root: Path) -> List[Path]:
    """递归查找所有 Python 文件（排除 __pycache__ 等）"""
    files = []
    for pattern in ["**/*.py"]:
        for f in root.glob(pattern):
            # 排除缓存和虚拟环境
            parts = f.parts
            if any(skip in parts for skip in ["__pycache__", ".git", ".venv",
                                                "venv", ".tox", "build", "dist"]):
                continue
            files.append(f)
    return sorted(files)


def count_lines(filepath: Path) -> int:
    """统计文件行数"""
    try:
        with open(filepath, encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


# =============================================================================
# 评分维度实现
# =============================================================================

def check_coverage(project_root: Path) -> DimensionScore:
    """维度1: 测试覆盖率 (20分)"""
    max_score = 20.0

    code, output = run_command([
        sys.executable, "-m", "pytest", "tests/",
        "--cov=src", "--cov-report=json:-",
        "--no-header", "-q"
    ], cwd=project_root, timeout=120)

    coverage_pct = None
    if code == 0 or os.path.exists(project_root / "coverage.json"):
        try:
            with open(project_root / "coverage.json") as f:
                cov_data = json.load(f)
                coverage_pct = cov_data.get("totals", {}).get("percent_covered", 0)
        except Exception:
            pass

    # 如果 JSON 方式失败，尝试解析文本
    if coverage_pct is None and output:
        match = re.search(r'TOTAL\s+\d+\s+\d+\s+([\d.]+)%', output)
        if match:
            coverage_pct = float(match.group(1))

    if coverage_pct is None:
        return DimensionScore(
            name="测试覆盖率", score=0, max_score=max_score,
            detail="无法获取覆盖率数据（可能 pytest-cov 未安装或测试失败）",
            status="warn"
        )

    # 评分逻辑: >=60% 得满分，>=40% 得 70%，>=25% 得 50%，<15% 得 20%
    if coverage_pct >= 60:
        score = max_score
        status = "pass"
    elif coverage_pct >= 40:
        score = max_score * 0.7
        status = "warn"
    elif coverage_pct >= 25:
        score = max_score * 0.5
        status = "warn"
    else:
        score = max_score * 0.2
        status = "fail"

    detail = f"当前 {coverage_pct:.1f}% (目标 ≥60%)"

    return DimensionScore(
        name="测试覆盖率", score=round(score, 1), max_score=max_score,
        detail=detail, status=status
    )


def check_complexity(project_root: Path, target_dir: Optional[str]) -> DimensionScore:
    """维度2: 圈复杂度 (15分)"""
    max_score = 15.0

    src_path = project_root / (target_dir if target_dir else "src")
    code, output = run_command(["radon", "cc", str(src_path), "-a", "-s", "-j"],
                               cwd=project_root, timeout=30)

    all_items = []
    avg_complexity = 0.0
    high_count = 0
    total_funcs = 0

    try:
        if output.strip():
            data = json.loads(output)
            for filepath, items in data.items():
                for item in items:
                    all_items.append(item.get("complexity", 0))
    except (json.JSONDecodeError, TypeError):
        # 回退到文本解析
        if output:
            for line in output.split("\n"):
                match = re.search(r'\((\w+)\)', line)
                if match:
                    try:
                        all_items.append(int(match.group(1)))
                    except ValueError:
                        pass

    if all_items:
        total_funcs = len(all_items)
        avg_complexity = sum(all_items) / total_funcs
        high_count = sum(1 for c in all_items if c > 15)

    # 评分: 平均 <6 得满分, <8 得 80%, <12 得 60%, >15 得 30%
    if avg_complexity <= 6:
        score = max_score
        status = "pass"
    elif avg_complexity <= 8:
        score = max_score * 0.8
        status = "pass"
    elif avg_complexity <= 12:
        score = max_score * 0.6
        status = "warn"
    else:
        score = max_score * 0.3
        status = "fail"

    detail = f"平均 {avg_complexity:.1f} ({total_funcs} 个函数, {high_count} 个 >15)"

    return DimensionScore(
        name="圈复杂度", score=round(score, 1), max_score=max_score,
        detail=detail, status=status
    )


def check_lint_quality(project_root: Path, target_dir: Optional[str]) -> DimensionScore:
    """维度3: Lint 质量 (15分)"""
    max_score = 15.0

    src_path = project_root / (target_dir if target_dir else "src")
    code, output = run_command(
        ["ruff", "check", str(src_path), "--output-format=json"],
        cwd=project_root, timeout=30
    )

    errors = []
    warnings = []
    try:
        if output.strip():
            items = json.loads(output)
            for item in items:
                code_str = item.get("code", "")
                if code_str.startswith(("E", "F")):
                    errors.append(code_str)
                else:
                    warnings.append(code_str)
    except (json.JSONDecodeError, TypeError):
        # 回退：从文本中估算
        error_count = output.count("\n") if output else 0
        errors = [None] * min(error_count, 50)

    error_count = len(errors)
    warning_count = len(warnings)

    # 评分: 0 错误得满分, 1-5 得 90%, 6-20 得 70%, 21-50 得 40%, >50 得 10%
    if error_count == 0:
        score = max_score
        status = "pass"
    elif error_count <= 5:
        score = max_score * 0.9
        status = "pass"
    elif error_count <= 20:
        score = max_score * 0.7
        status = "warn"
    elif error_count <= 50:
        score = max_score * 0.4
        status = "fail"
    else:
        score = max_score * 0.1
        status = "fail"

    detail = f"{error_count} 错误, {warning_count} 警告"
    if error_count > 0:
        detail += " | 运行 ruff check --fix 修复部分问题"

    return DimensionScore(
        name="Lint 质量", score=round(score, 1), max_score=max_score,
        detail=detail, status=status
    )


def check_type_annotations(project_root: Path) -> DimensionScore:
    """维度4: 类型注解完整性 (10分)"""
    max_score = 10.0

    code, output = run_command(
        ["mypy", "src/", "--ignore-missing-imports", "--no-error-summary"],
        cwd=project_root, timeout=60
    )

    type_errors = 0
    if output:
        type_errors = len(re.findall(r"^src/.*error:", output, re.MULTILINE))

    # 评分: 0 错误得满分, 1-10 得 80%, 11-50 得 50%, >50 得 20%
    if type_errors == 0:
        score = max_score
        status = "pass"
    elif type_errors <= 10:
        score = max_score * 0.8
        status = "warn"
    elif type_errors <= 50:
        score = max_score * 0.5
        status = "warn"
    else:
        score = max_score * 0.2
        status = "fail"

    detail = f"{type_errors} 个类型错误"

    return DimensionScore(
        name="类型注解", score=round(score, 1), max_score=max_score,
        detail=detail, status=status
    )


def check_function_length(project_root: Path, target_dir: Optional[str]) -> DimensionScore:
    """维度5: 函数长度 (10分)"""
    max_score = 10.0

    src_path = project_root / (target_dir if target_dir else "src")
    files = find_python_files(src_path)

    func_lengths = []
    func_pattern = re.compile(r'^\s*def\s+(\w+)\s*\(', re.MULTILINE)

    for filepath in files:
        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
            lines = content.split("\n")

            for match in func_pattern.finditer(content):
                start_line = content[:match.start()].count("\n") + 1
                # 简单估计：找下一个 def 或 class 在同一缩进级别
                func_body = content[match.start():]
                # 计算函数体行数（到下一个同级别定义或文件末尾）
                indent_level = len(match.group(0)) - len(match.group(0).lstrip())
                body_lines = 0
                for line in func_body.split("\n")[1:]:
                    if line.strip() == "" or line.startswith("#"):
                        body_lines += 1
                        continue
                    current_indent = len(line) - len(line.lstrip())
                    if current_indent <= indent_level and line.strip():
                        break
                    body_lines += 1

                if body_lines > 0:
                    func_lengths.append(body_lines)
        except Exception:
            continue

    if not func_lengths:
        return DimensionScore(
            name="函数长度", score=max_score, max_score=max_score,
            detail="未找到可分析的函数", status="info"
        )

    avg_length = sum(func_lengths) / len(func_lengths)
    long_funcs = sum(1 for l in func_lengths if l > 40)
    very_long = sum(1 for l in func_lengths if l > 80)

    # 评分: 平均 <20 得满分, <30 得 80%, <45 得 55%, >60 得 20%
    if avg_length <= 20:
        score = max_score
        status = "pass"
    elif avg_length <= 30:
        score = max_score * 0.8
        status = "pass"
    elif avg_length <= 45:
        score = max_score * 0.55
        status = "warn"
    else:
        score = max_score * 0.2
        status = "fail"

    detail = f"平均 {avg_length:.0f} 行 ({len(func_lengths)} 个函数, {long_funcs} 个 >40行, {very_long} 个 >80行)"

    return DimensionScore(
        name="函数长度", score=round(score, 1), max_score=max_score,
        detail=detail, status=status
    )


def check_docstrings(project_root: Path, target_dir: Optional[str]) -> DimensionScore:
    """维度6: 文档完整性 (10分)"""
    max_score = 10.0

    src_path = project_root / (target_dir if target_dir else "src")
    files = find_python_files(src_path)

    public_funcs_with_doc = 0
    public_funcs_total = 0
    classes_with_doc = 0
    classes_total = 0

    func_re = re.compile(r'^def\s+(\w[^\s_]*)\s*\(', re.MULTILINE)
    class_re = re.compile(r'^class\s+(\w+)', re.MULTILINE)

    for filepath in files:
        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
            lines = content.split("\n")

            # 检查公共函数的 docstring
            for match in func_re.finditer(content):
                func_name = match.group(1)
                # 以 _ 开头的是私有方法
                if func_name.startswith("_"):
                    continue

                public_funcs_total += 1
                start_pos = match.end()
                # 查看函数后的内容是否有 docstring
                rest = content[start_pos:start_pos + 200].lstrip()
                if rest.startswith(('"""', "'''")):
                    public_funcs_with_doc += 1

            # 检查类的 docstring
            for match in class_re.finditer(content):
                classes_total += 1
                rest = content[match.end():match.end() + 200].lstrip()
                if rest.startswith(('"""', "'''")):
                    classes_with_doc += 1
        except Exception:
            continue

    if public_funcs_total == 0:
        return DimensionScore(
            name="文档完整性", score=max_score, max_score=max_score,
            detail="未找到公共 API 函数", status="info"
        )

    ratio = public_funcs_with_doc / public_funcs_total * 100

    # 评分: >=80% 得满分, >=60% 得 75%, >=40% 得 50%, <20% 得 15%
    if ratio >= 80:
        score = max_score
        status = "pass"
    elif ratio >= 60:
        score = max_score * 0.75
        status = "pass"
    elif ratio >= 40:
        score = max_score * 0.5
        status = "warn"
    else:
        score = max_score * 0.15
        status = "fail"

    class_ratio = f"{classes_with_doc}/{classes_total}" if classes_total else "N/A"
    detail = f"公共函数 {public_funcs_with_doc}/{public_funcs_total} ({ratio:.0f}%), 类文档 {class_ratio}"

    return DimensionScore(
        name="文档完整性", score=round(score, 1), max_score=max_score,
        detail=detail, status=status
    )


def check_security(project_root: Path) -> DimensionScore:
    """维度7: 安全扫描 (10分)"""
    max_score = 10.0

    code, output = run_command(
        ["bandit", "-r", "src/", "-f", "json", "-ll", "--skip", "B101"],
        cwd=project_root, timeout=30
    )

    high_count = 0
    medium_count = 0
    low_count = 0

    try:
        if output.strip():
            data = json.loads(output)
            for result in data.get("results", []):
                severity = result.get("issue_severity", "")
                if severity == "HIGH":
                    high_count += 1
                elif severity == "MEDIUM":
                    medium_count += 1
                else:
                    low_count += 1
    except (json.JSONDecodeError, TypeError):
        pass

    # 有 HIGH 直接低分
    if high_count > 0:
        score = max_score * 0.1
        status = "fail"
    elif medium_count > 5:
        score = max_score * 0.5
        status = "warn"
    elif medium_count > 0:
        score = max_score * 0.7
        status = "warn"
    else:
        score = max_score
        status = "pass"

    detail = f"H:{high_count} M:{medium_count} L:{low_count}"
    if high_count > 0:
        detail += " | 🔴 存在高危安全问题!"

    return DimensionScore(
        name="安全扫描", score=round(score, 1), max_score=max_score,
        detail=detail, status=status
    )


def check_code_duplication(project_root: Path, target_dir: Optional[str]) -> DimensionScore:
    """维度8: 代码重复检测 (简化版) (10分)"""
    max_score = 10.0
    # 这是一个简化版本 — 完整检测需要 jscpd 或 similar 工具
    # 这里用基本的启发式方法：检查是否有大量相似的 import 块或重复的模式

    src_path = project_root / (target_dir if target_dir else "src")
    files = find_python_files(src_path)

    # 收集所有 import 行
    import_patterns = {}
    for filepath in files:
        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
            imports = re.findall(r'^(?:from|import)\s+.+', content, re.MULTILINE)
            for imp in imports:
                import_patterns[imp] = import_patterns.get(imp, 0) + 1
        except Exception:
            continue

    # 统计完全相同的 import 块出现次数
    duplicate_imports = sum(1 for count in import_patterns.values() if count > 3)

    # 简化的重复评估
    file_count = len(files)

    # 评分: 少量重复正常, 过多则扣分
    if duplicate_imports <= file_count * 0.5:
        score = max_score
        status = "pass"
    elif duplicate_imports <= file_count:
        score = max_score * 0.75
        status = "pass"
    else:
        score = max_score * 0.5
        status = "warn"

    detail = f"{file_count} 个文件, {duplicate_imports} 处常见导入模式重复"

    return DimensionScore(
        name="代码重复", score=round(score, 1), max_score=max_score,
        detail=detail, status=status
    )


# =============================================================================
# 报告生成与展示
# =============================================================================

def compute_grade(total: float, max_score: float) -> str:
    """根据分数计算等级"""
    pct = total / max_score * 100
    if pct >= 90:
        return "A+ 🏆"
    elif pct >= 80:
        return "A ✨"
    elif pct >= 70:
        return "B+ 👍"
    elif pct >= 60:
        return "B 👌"
    elif pct >= 50:
        return "C ⚠️"
    elif pct >= 35:
        return "D 🔶"
    else:
        return "F 🔴"


def generate_summary(report: QualityReport) -> str:
    """生成摘要文字"""
    fails = [d for d in report.dimensions if d.status == "fail"]
    warns = [d for d in report.dimensions if d.status == "warn"]

    parts = []
    if fails:
        names = ", ".join(d.name for d in fails)
        parts.append(f"需要紧急处理: {names}")
    if warns:
        names = ", ".join(d.name for d in warns)
        parts.append(f"建议改进: {names}")

    if not parts:
        parts.append("各项指标健康")

    return "; ".join(parts)


def print_report(report: QualityReport) -> None:
    """打印美观的质量报告"""

    print()
    print("=" * 58)
    print("       🔍 ZHC 代码质量评分报告")
    print("=" * 58)
    print()

    # 表头
    print(f"{'维度':<14} {'得分':>8} {'满分':>6} {'状态':>6}")
    print("-" * 56)

    for dim in report.dimensions:
        bar_width = int(dim.score / dim.max_score * 16)
        bar = "█" * bar_width + "░" * (16 - bar_width)
        status_icon = {
            "pass": "✅",
            "warn": "⚠️ ",
            "fail": "❌",
            "info": "ℹ️ "
        }.get(dim.status, "?")

        print(f"{dim.name:<12} {dim.score:>7.1f}/{dim.max_score:<5.0f} [{bar}] {status_icon}")

    print("-" * 56)
    print()

    # 总分条
    total_bar_width = int(report.total_score / report.total_max * 48)
    total_bar = "█" * total_bar_width + "░" * (48 - total_bar_width)

    print(f"╔══════════════════════════════════════════════════╗")
    print(f"║                                                    ║")
    print(f"║   总分: {report.total_score:>5.1f}/{report.total_max:.0f}  等级: {report.grade:<12}       ║")
    print(f"║   {total_bar}   ║")
    print(f"║                                                    ║")
    print(f"╚══════════════════════════════════════════════════╝")
    print()

    # 各维度详情
    print("📋 详情:")
    for dim in report.dimensions:
        icon = {"pass": "✅", "warn": "⚠️ ", "fail": "❌", "info": "ℹ️ "}.get(dim.status, "?")
        print(f"  {icon} {dim.name}: {dim.detail}")

    print()
    print(f"💬 {report.summary}")
    print()


# =============================================================================
# 主流程
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="ZHC 代码质量评分器")
    parser.add_argument("path", nargs="?", default=None,
                        help="要评分的路径（默认: src/）")
    parser.add_argument("--json", action="store_true",
                        help="以 JSON 格式输出结果")
    args = parser.parse_args()

    # 确定项目根目录
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent  # scripts/ -> 项目根目

    if not (project_root / "pyproject.toml").exists():
        # 尝试向上查找
        for parent in script_path.parents:
            if (parent / "pyproject.toml").exists():
                project_root = parent
                break
        else:
            print("❌ 无法找到 ZHC 项目根目录（缺少 pyproject.toml）")
            sys.exit(1)

    target_dir = args.path

    # 运行各维度评分
    report = QualityReport(timestamp="2026-04-08")

    # 按顺序执行评分
    checkers = [
        ("测试覆盖率", lambda: check_coverage(project_root)),
        ("圈复杂度", lambda: check_complexity(project_root, target_dir)),
        ("Lint 质量", lambda: check_lint_quality(project_root, target_dir)),
        ("类型注解", lambda: check_type_annotations(project_root)),
        ("函数长度", lambda: check_function_length(project_root, target_dir)),
        ("文档完整性", lambda: check_docstrings(project_root, target_dir)),
        ("安全扫描", lambda: check_security(project_root)),
        ("代码重复", lambda: check_code_duplication(project_root, target_dir)),
    ]

    for checker_name, checker_fn in checkers:
        print(f"  ⏳ 正在分析 {checker_name}...", end="\r")
        try:
            result = checker_fn()
            report.dimensions.append(result)
        except Exception as e:
            report.dimensions.append(DimensionScore(
                name=checker_name, score=0, max_score=result.max_score if 'result' in dir() else 10,
                detail=f"分析出错: {e}", status="fail"
            ))

    # 清除进度行
    print(" " * 50, end="\r")

    # 计算总分
    report.total_score = round(sum(d.score for d in report.dimensions), 1)
    report.total_max = sum(d.max_score for d in report.dimensions)
    report.grade = compute_grade(report.total_score, report.total_max)
    report.summary = generate_summary(report)

    # 输出
    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        print_report(report)

    # 清理临时文件
    temp_files = ["coverage.json"]
    for f in temp_files:
        path = project_root / f
        if path.exists():
            path.unlink()

    # 返回码: < 60 分返回非零
    if report.total_score / report.total_max * 100 < 60:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
