"""
分析报告生成器

生成多种格式的静态分析报告。

Phase 4 - Stage 3 - Task 14.3
"""

from typing import Dict, List
from datetime import datetime
import json

from zhc.analysis.base_analyzer import AnalysisResult, Severity
from zhc.analysis.analyzer_scheduler import AnalysisStats


class ReportGenerator:
    """
    分析报告生成器

    支持多种输出格式：文本、Markdown、JSON、HTML。
    """

    def __init__(self, results: Dict[str, List[AnalysisResult]], stats: AnalysisStats):
        """
        初始化报告生成器

        Args:
            results: 分析结果字典
            stats: 分析统计信息
        """
        self.results = results
        self.stats = stats

    def generate_text(self) -> str:
        """生成文本格式报告"""
        lines = []
        lines.append("=" * 60)
        lines.append("静态分析报告")
        lines.append("=" * 60)
        lines.append("")

        # 统计摘要
        lines.append("【统计摘要】")
        lines.append(f"  总问题数: {self.stats.total_issues}")
        lines.append(f"  错误: {self.stats.errors}")
        lines.append(f"  警告: {self.stats.warnings}")
        lines.append(f"  信息: {self.stats.infos}")
        lines.append(f"  提示: {self.stats.hints}")
        lines.append(f"  执行时间: {self.stats.execution_time:.2f}s")
        lines.append("")

        # 按严重程度分组
        for severity in [
            Severity.ERROR,
            Severity.WARNING,
            Severity.INFO,
            Severity.HINT,
        ]:
            severity_results = self._filter_by_severity(severity)
            if severity_results:
                lines.append(
                    f"【{severity.value.upper()}】({len(severity_results)} 个)"
                )
                for result in severity_results:
                    lines.append(f"  - {result.message}")
                    lines.append(f"    位置: {result.location}")
                    if result.suggestion:
                        lines.append(f"    建议: {result.suggestion}")
                lines.append("")

        return "\n".join(lines)

    def generate_markdown(self) -> str:
        """生成 Markdown 格式报告"""
        lines = []
        lines.append("# 静态分析报告")
        lines.append("")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # 统计摘要
        lines.append("## 统计摘要")
        lines.append("")
        lines.append(f"- **总问题数**: {self.stats.total_issues}")
        lines.append(f"- **错误**: {self.stats.errors}")
        lines.append(f"- **警告**: {self.stats.warnings}")
        lines.append(f"- **信息**: {self.stats.infos}")
        lines.append(f"- **提示**: {self.stats.hints}")
        lines.append(f"- **执行时间**: {self.stats.execution_time:.2f}s")
        lines.append("")

        # 按分析器分组
        lines.append("## 分析结果")
        lines.append("")

        for analyzer_name, results in self.results.items():
            if results:
                lines.append(f"### {analyzer_name}")
                lines.append("")

                for result in results:
                    severity_emoji = {
                        Severity.ERROR: "❌",
                        Severity.WARNING: "⚠️",
                        Severity.INFO: "ℹ️",
                        Severity.HINT: "💡",
                    }.get(result.severity, "")

                    lines.append(f"#### {severity_emoji} {result.message}")
                    lines.append("")
                    lines.append(f"- **位置**: `{result.location}`")
                    if result.suggestion:
                        lines.append(f"- **建议**: {result.suggestion}")
                    lines.append("")

        return "\n".join(lines)

    def generate_json(self) -> str:
        """生成 JSON 格式报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "stats": self.stats.to_dict(),
            "results": {},
        }

        for analyzer_name, results in self.results.items():
            report["results"][analyzer_name] = [r.to_dict() for r in results]

        return json.dumps(report, indent=2, ensure_ascii=False)

    def generate_html(self) -> str:
        """生成 HTML 格式报告"""
        html = (
            """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>静态分析报告</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .stat-label {
            color: #666;
        }
        .error { color: #e74c3c; }
        .warning { color: #f39c12; }
        .info { color: #3498db; }
        .hint { color: #2ecc71; }
        .result-card {
            background: white;
            margin: 15px 0;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #ddd;
        }
        .result-card.error { border-left-color: #e74c3c; }
        .result-card.warning { border-left-color: #f39c12; }
        .result-card.info { border-left-color: #3498db; }
        .result-card.hint { border-left-color: #2ecc71; }
        .result-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .result-message {
            font-weight: 500;
            font-size: 1.1em;
        }
        .result-location {
            font-family: 'Courier New', monospace;
            background: #f8f9fa;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 0.9em;
        }
        .result-suggestion {
            margin-top: 10px;
            padding: 10px;
            background: #fff3cd;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>静态分析报告</h1>
        <p>生成时间: """
            + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            + """</p>
    </div>

    <div class="stats">
        <div class="stat-card">
            <div class="stat-value">"""
            + str(self.stats.total_issues)
            + """</div>
            <div class="stat-label">总问题数</div>
        </div>
        <div class="stat-card">
            <div class="stat-value error">"""
            + str(self.stats.errors)
            + """</div>
            <div class="stat-label">错误</div>
        </div>
        <div class="stat-card">
            <div class="stat-value warning">"""
            + str(self.stats.warnings)
            + """</div>
            <div class="stat-label">警告</div>
        </div>
        <div class="stat-card">
            <div class="stat-value info">"""
            + str(self.stats.infos)
            + """</div>
            <div class="stat-label">信息</div>
        </div>
        <div class="stat-card">
            <div class="stat-value hint">"""
            + str(self.stats.hints)
            + """</div>
            <div class="stat-label">提示</div>
        </div>
    </div>

    <h2>分析结果</h2>
"""
        )

        for analyzer_name, results in self.results.items():
            if results:
                html += f"    <h3>{analyzer_name}</h3>\n"

                for result in results:
                    severity_class = result.severity.value
                    html += f"""
    <div class="result-card {severity_class}">
        <div class="result-header">
            <span class="result-message">{result.message}</span>
            <span class="result-location">{result.location}</span>
        </div>
"""
                    if result.suggestion:
                        html += f"""
        <div class="result-suggestion">
            <strong>建议:</strong> {result.suggestion}
        </div>
"""
                    html += "    </div>\n"

        html += """
</body>
</html>
"""
        return html

    def _filter_by_severity(self, severity: Severity) -> List[AnalysisResult]:
        """按严重程度过滤结果"""
        filtered = []
        for results in self.results.values():
            filtered.extend([r for r in results if r.severity == severity])
        return filtered

    def save_to_file(self, filepath: str, format: str = "text") -> None:
        """
        保存报告到文件

        Args:
            filepath: 文件路径
            format: 输出格式（text, markdown, json, html）
        """
        content = {
            "text": self.generate_text,
            "markdown": self.generate_markdown,
            "json": self.generate_json,
            "html": self.generate_html,
        }.get(format, self.generate_text)()

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
