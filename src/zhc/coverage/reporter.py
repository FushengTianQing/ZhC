#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
覆盖率报告器

生成各种格式的覆盖率报告
"""

from abc import ABC, abstractmethod
from pathlib import Path
from .data import ProjectCoverage


class CoverageReporter(ABC):
    """覆盖率报告器基类"""

    @abstractmethod
    def generate(self, coverage: ProjectCoverage) -> str:
        """生成报告"""
        pass

    def save(self, coverage: ProjectCoverage, output_path: str) -> None:
        """保存报告"""
        report = self.generate(coverage)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)


class TextReporter(CoverageReporter):
    """文本报告器"""

    def generate(self, coverage: ProjectCoverage) -> str:
        """生成文本报告"""
        lines = []
        lines.append("=" * 60)
        lines.append("覆盖率报告")
        lines.append("=" * 60)
        lines.append("")

        # 汇总
        lines.append("汇总:")
        lines.append(
            f"  行覆盖率:   {coverage.line_coverage_rate:.1%} ({coverage.covered_lines}/{coverage.total_lines})"
        )
        lines.append(
            f"  分支覆盖率: {coverage.branch_coverage_rate:.1%} ({coverage.covered_branches}/{coverage.total_branches})"
        )
        lines.append(
            f"  函数覆盖率: {coverage.function_coverage_rate:.1%} ({coverage.covered_functions}/{coverage.total_functions})"
        )
        lines.append("")

        # 每个文件
        lines.append("文件详情:")
        lines.append("-" * 60)

        for file_path, file_cov in sorted(coverage.files.items()):
            lines.append(f"\n文件: {file_path}")
            lines.append(
                f"  行覆盖率:   {file_cov.line_coverage_rate:.1%} ({file_cov.covered_lines}/{file_cov.total_lines})"
            )
            lines.append(
                f"  分支覆盖率: {file_cov.branch_coverage_rate:.1%} ({file_cov.covered_branches}/{file_cov.total_branches})"
            )
            lines.append(
                f"  函数覆盖率: {file_cov.function_coverage_rate:.1%} ({file_cov.covered_functions}/{file_cov.total_functions})"
            )

            # 未覆盖的行
            uncovered = [
                line.line_number
                for line in file_cov.lines.values()
                if line.is_executable and not line.is_covered
            ]
            if uncovered:
                lines.append(
                    f"  未覆盖行: {uncovered[:10]}{'...' if len(uncovered) > 10 else ''}"
                )

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)


class JsonReporter(CoverageReporter):
    """JSON 报告器"""

    def generate(self, coverage: ProjectCoverage) -> str:
        """生成 JSON 报告"""
        return coverage.to_json(indent=2)


class HtmlReporter(CoverageReporter):
    """HTML 报告器"""

    def generate(self, coverage: ProjectCoverage) -> str:
        """生成 HTML 报告"""
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>覆盖率报告</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
        }}
        .header h1 {{
            font-size: 24px;
            margin-bottom: 10px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .summary-card h3 {{
            font-size: 14px;
            color: #666;
            margin-bottom: 10px;
        }}
        .summary-card .rate {{
            font-size: 32px;
            font-weight: bold;
        }}
        .summary-card .count {{
            font-size: 12px;
            color: #999;
            margin-top: 5px;
        }}
        .rate.excellent {{ color: #28a745; }}
        .rate.good {{ color: #ffc107; }}
        .rate.poor {{ color: #dc3545; }}
        .files {{
            padding: 30px;
        }}
        .files h2 {{
            font-size: 18px;
            margin-bottom: 20px;
            color: #333;
        }}
        .file-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .file-table th,
        .file-table td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        .file-table th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #666;
        }}
        .file-table tr:hover {{
            background: #f8f9fa;
        }}
        .progress-bar {{
            width: 100%;
            height: 8px;
            background: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
        }}
        .progress-bar .fill {{
            height: 100%;
            transition: width 0.3s ease;
        }}
        .progress-bar .fill.excellent {{ background: #28a745; }}
        .progress-bar .fill.good {{ background: #ffc107; }}
        .progress-bar .fill.poor {{ background: #dc3545; }}
        .footer {{
            padding: 20px 30px;
            background: #f8f9fa;
            text-align: center;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 覆盖率报告</h1>
            <p>生成时间: {self._get_timestamp()}</p>
        </div>

        <div class="summary">
            <div class="summary-card">
                <h3>行覆盖率</h3>
                <div class="rate {self._get_rate_class(coverage.line_coverage_rate)}">
                    {coverage.line_coverage_rate:.1%}
                </div>
                <div class="count">{coverage.covered_lines} / {coverage.total_lines} 行</div>
            </div>
            <div class="summary-card">
                <h3>分支覆盖率</h3>
                <div class="rate {self._get_rate_class(coverage.branch_coverage_rate)}">
                    {coverage.branch_coverage_rate:.1%}
                </div>
                <div class="count">{coverage.covered_branches} / {coverage.total_branches} 分支</div>
            </div>
            <div class="summary-card">
                <h3>函数覆盖率</h3>
                <div class="rate {self._get_rate_class(coverage.function_coverage_rate)}">
                    {coverage.function_coverage_rate:.1%}
                </div>
                <div class="count">{coverage.covered_functions} / {coverage.total_functions} 函数</div>
            </div>
        </div>

        <div class="files">
            <h2>📁 文件覆盖率</h2>
            <table class="file-table">
                <thead>
                    <tr>
                        <th>文件</th>
                        <th>行覆盖率</th>
                        <th>进度</th>
                        <th>分支</th>
                        <th>函数</th>
                    </tr>
                </thead>
                <tbody>
"""

        for file_path, file_cov in sorted(coverage.files.items()):
            html += f"""                    <tr>
                        <td>{Path(file_path).name}</td>
                        <td>{file_cov.line_coverage_rate:.1%}</td>
                        <td>
                            <div class="progress-bar">
                                <div class="fill {self._get_rate_class(file_cov.line_coverage_rate)}"
                                     style="width: {file_cov.line_coverage_rate * 100}%"></div>
                            </div>
                        </td>
                        <td>{file_cov.branch_coverage_rate:.1%}</td>
                        <td>{file_cov.function_coverage_rate:.1%}</td>
                    </tr>
"""

        html += """                </tbody>
            </table>
        </div>

        <div class="footer">
            <p>由 ZhC 测试框架生成</p>
        </div>
    </div>
</body>
</html>"""
        return html

    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _get_rate_class(self, rate: float) -> str:
        """获取覆盖率等级"""
        if rate >= 0.9:
            return "excellent"
        elif rate >= 0.7:
            return "good"
        else:
            return "poor"


class MarkdownReporter(CoverageReporter):
    """Markdown 报告器"""

    def generate(self, coverage: ProjectCoverage) -> str:
        """生成 Markdown 报告"""
        lines = []
        lines.append("# 📊 覆盖率报告")
        lines.append("")

        # 汇总
        lines.append("## 汇总")
        lines.append("")
        lines.append("| 指标 | 覆盖率 | 数量 |")
        lines.append("|------|--------|------|")
        lines.append(
            f"| 行覆盖率 | {coverage.line_coverage_rate:.1%} | {coverage.covered_lines}/{coverage.total_lines} |"
        )
        lines.append(
            f"| 分支覆盖率 | {coverage.branch_coverage_rate:.1%} | {coverage.covered_branches}/{coverage.total_branches} |"
        )
        lines.append(
            f"| 函数覆盖率 | {coverage.function_coverage_rate:.1%} | {coverage.covered_functions}/{coverage.total_functions} |"
        )
        lines.append("")

        # 文件详情
        lines.append("## 文件详情")
        lines.append("")
        lines.append("| 文件 | 行覆盖率 | 分支覆盖率 | 函数覆盖率 |")
        lines.append("|------|----------|------------|------------|")

        for file_path, file_cov in sorted(coverage.files.items()):
            name = Path(file_path).name
            lines.append(
                f"| {name} | {file_cov.line_coverage_rate:.1%} | {file_cov.branch_coverage_rate:.1%} | {file_cov.function_coverage_rate:.1%} |"
            )

        lines.append("")
        lines.append("---")
        lines.append("*由 ZhC 测试框架生成*")

        return "\n".join(lines)


class LcovReporter(CoverageReporter):
    """LCOV 格式报告器"""

    def generate(self, coverage: ProjectCoverage) -> str:
        """生成 LCOV 格式报告"""
        lines = []

        for file_path, file_cov in coverage.files.items():
            lines.append(f"SF:{file_path}")

            # 函数信息
            for func in file_cov.functions.values():
                lines.append(f"FN:{func.start_line},{func.function_name}")

            for func in file_cov.functions.values():
                lines.append(f"FNDA:{func.hit_count},{func.function_name}")

            lines.append(f"FNF:{file_cov.total_functions}")
            lines.append(f"FNH:{file_cov.covered_functions}")

            # 行信息
            for line in sorted(file_cov.lines.values(), key=lambda x: x.line_number):
                if line.is_executable:
                    lines.append(f"DA:{line.line_number},{line.hit_count}")

            lines.append(f"LF:{file_cov.total_lines}")
            lines.append(f"LH:{file_cov.covered_lines}")

            # 分支信息
            for branch in file_cov.branches.values():
                lines.append(
                    f"BRDA:{branch.line_number},0,{branch.branch_id.split('_')[1]},{branch.true_hits if branch.true_hits > 0 else branch.false_hits}"
                )

            lines.append(f"BRF:{file_cov.total_branches}")
            lines.append(f"BRH:{file_cov.covered_branches}")

            lines.append("end_of_record")

        return "\n".join(lines)


def generate_report(coverage: ProjectCoverage, format: str = "text") -> str:
    """生成覆盖率报告"""
    reporters = {
        "text": TextReporter,
        "json": JsonReporter,
        "html": HtmlReporter,
        "markdown": MarkdownReporter,
        "md": MarkdownReporter,
        "lcov": LcovReporter,
    }

    reporter_class = reporters.get(format.lower())
    if reporter_class is None:
        raise ValueError(f"不支持的报告格式: {format}")

    return reporter_class().generate(coverage)


def save_report(
    coverage: ProjectCoverage, output_path: str, format: str = None
) -> None:
    """保存覆盖率报告"""
    if format is None:
        suffix = Path(output_path).suffix.lower()
        format_map = {
            ".txt": "text",
            ".json": "json",
            ".html": "html",
            ".md": "markdown",
            ".lcov": "lcov",
        }
        format = format_map.get(suffix, "text")

    reporters = {
        "text": TextReporter,
        "json": JsonReporter,
        "html": HtmlReporter,
        "markdown": MarkdownReporter,
        "lcov": LcovReporter,
    }

    reporter_class = reporters.get(format.lower())
    if reporter_class is None:
        raise ValueError(f"不支持的报告格式: {format}")

    reporter_class().save(coverage, output_path)
