#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
结果报告器

生成测试结果的多种格式报告
"""

import json
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.dom import minidom

from .result import TestSummary, TestStatus


class Reporter:
    """报告器基类"""

    def generate(self, summary: TestSummary) -> str:
        """生成报告"""
        raise NotImplementedError


class TextReporter(Reporter):
    """文本报告器"""

    def generate(self, summary: TestSummary) -> str:
        """生成文本报告"""
        lines = []
        lines.append("=" * 60)
        lines.append("测试结果报告")
        lines.append("=" * 60)
        lines.append("")

        # 汇总信息
        lines.append(f"总测试数: {summary.total_count}")
        lines.append(f"通过: {summary.passed_count}")
        lines.append(f"失败: {summary.failed_count}")
        lines.append(f"错误: {summary.error_count}")
        lines.append(f"跳过: {summary.skipped_count}")
        lines.append(f"成功率: {summary.success_rate:.1f}%")
        lines.append(f"执行时间: {summary.duration:.3f}s")
        lines.append("")

        # 模块详情
        for module in summary.modules:
            lines.append(f"模块: {module.name}")
            lines.append("-" * 40)

            for suite in module.suites:
                lines.append(f"  套件: {suite.name}")
                for test_case in suite.test_cases:
                    status_icon = self._get_status_icon(test_case.status)
                    lines.append(
                        f"    {status_icon} {test_case.name} ({test_case.duration:.3f}s)"
                    )

                    # 显示失败的断言
                    if test_case.failed or test_case.error:
                        for assertion in test_case.assertions:
                            if not assertion.passed:
                                lines.append(
                                    f"        ❌ {assertion.name}: {assertion.message}"
                                )
                                if assertion.file_path:
                                    lines.append(
                                        f"           at {assertion.file_path}:{assertion.line_number}"
                                    )

                        if test_case.error_message:
                            lines.append(f"        错误: {test_case.error_message}")

                lines.append("")

        # 失败汇总
        failed_tests = summary.get_failed_tests()
        if failed_tests:
            lines.append("")
            lines.append("=" * 60)
            lines.append("失败测试详情")
            lines.append("=" * 60)
            for test_case in failed_tests:
                lines.append(f"❌ {test_case.suite_name}::{test_case.name}")
                if test_case.error_message:
                    lines.append(f"   错误: {test_case.error_message}")
                if test_case.stack_trace:
                    lines.append(f"   堆栈: {test_case.stack_trace}")
                lines.append("")

        lines.append("=" * 60)
        status = "✅ 全部通过" if summary.is_success else "❌ 存在失败"
        lines.append(f"结果: {status}")
        lines.append("=" * 60)

        return "\n".join(lines)

    def _get_status_icon(self, status: TestStatus) -> str:
        """获取状态图标"""
        icons = {
            TestStatus.PASSED: "✅",
            TestStatus.FAILED: "❌",
            TestStatus.ERROR: "💥",
            TestStatus.SKIPPED: "⏭️",
            TestStatus.NOT_RUN: "⏳",
        }
        return icons.get(status, "❓")


class JsonReporter(Reporter):
    """JSON 报告器"""

    def generate(self, summary: TestSummary) -> str:
        """生成 JSON 报告"""
        data = {
            "summary": {
                "total": summary.total_count,
                "passed": summary.passed_count,
                "failed": summary.failed_count,
                "errors": summary.error_count,
                "skipped": summary.skipped_count,
                "success_rate": round(summary.success_rate, 2),
                "duration": round(summary.duration, 3),
                "is_success": summary.is_success,
            },
            "modules": [],
        }

        for module in summary.modules:
            module_data = {
                "name": module.name,
                "duration": round(module.duration, 3),
                "suites": [],
            }

            for suite in module.suites:
                suite_data = {
                    "name": suite.name,
                    "duration": round(suite.duration, 3),
                    "test_cases": [],
                }

                for test_case in suite.test_cases:
                    test_data = {
                        "name": test_case.name,
                        "status": test_case.status.value,
                        "duration": round(test_case.duration, 3),
                        "assertions": {
                            "total": len(test_case.assertions),
                            "passed": test_case.passed_assertions,
                            "failed": test_case.failed_assertions,
                        },
                    }

                    if test_case.error_message:
                        test_data["error_message"] = test_case.error_message

                    if test_case.assertions:
                        test_data["assertion_details"] = [
                            {
                                "name": a.name,
                                "passed": a.passed,
                                "message": a.message,
                                "expected": a.expected,
                                "actual": a.actual,
                            }
                            for a in test_case.assertions
                        ]

                    suite_data["test_cases"].append(test_data)

                module_data["suites"].append(suite_data)

            data["modules"].append(module_data)

        return json.dumps(data, indent=2, ensure_ascii=False)


class JUnitReporter(Reporter):
    """JUnit XML 报告器"""

    def generate(self, summary: TestSummary) -> str:
        """生成 JUnit XML 报告"""
        testsuites = ET.Element("testsuites")
        testsuites.set("tests", str(summary.total_count))
        testsuites.set("failures", str(summary.failed_count))
        testsuites.set("errors", str(summary.error_count))
        testsuites.set("skipped", str(summary.skipped_count))
        testsuites.set("time", f"{summary.duration:.3f}")

        for module in summary.modules:
            for suite in module.suites:
                testsuite = ET.SubElement(testsuites, "testsuite")
                testsuite.set("name", f"{module.name}.{suite.name}")
                testsuite.set("tests", str(suite.total_count))
                testsuite.set("failures", str(suite.failed_count))
                testsuite.set("errors", str(suite.error_count))
                testsuite.set("skipped", str(suite.skipped_count))
                testsuite.set("time", f"{suite.duration:.3f}")

                for test_case in suite.test_cases:
                    testcase = ET.SubElement(testsuite, "testcase")
                    testcase.set("name", test_case.name)
                    testcase.set("classname", f"{module.name}.{suite.name}")
                    testcase.set("time", f"{test_case.duration:.3f}")

                    if test_case.status == TestStatus.SKIPPED:
                        ET.SubElement(testcase, "skipped")
                    elif test_case.status == TestStatus.FAILED:
                        failure = ET.SubElement(testcase, "failure")
                        failure.set("message", test_case.error_message or "测试失败")
                        failure.text = test_case.stack_trace or ""
                    elif test_case.status == TestStatus.ERROR:
                        error = ET.SubElement(testcase, "error")
                        error.set("message", test_case.error_message or "测试错误")
                        error.text = test_case.stack_trace or ""

        # 格式化 XML
        xml_str = ET.tostring(testsuites, encoding="unicode")
        dom = minidom.parseString(xml_str)
        return dom.toprettyxml(indent="  ")


class HtmlReporter(Reporter):
    """HTML 报告器"""

    def generate(self, summary: TestSummary) -> str:
        """生成 HTML 报告"""
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>测试报告</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .summary {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary h1 {{
            margin: 0 0 20px 0;
            color: #333;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }}
        .stat {{
            text-align: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
        }}
        .stat-label {{
            color: #666;
            font-size: 0.9em;
        }}
        .passed {{ color: #28a745; }}
        .failed {{ color: #dc3545; }}
        .error {{ color: #fd7e14; }}
        .skipped {{ color: #6c757d; }}
        .module {{
            background: white;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .module-header {{
            background: #f8f9fa;
            padding: 15px 20px;
            border-bottom: 1px solid #e9ecef;
            cursor: pointer;
        }}
        .module-header h2 {{
            margin: 0;
            font-size: 1.2em;
        }}
        .suite {{
            padding: 15px 20px;
            border-bottom: 1px solid #e9ecef;
        }}
        .suite h3 {{
            margin: 0 0 10px 0;
            font-size: 1em;
            color: #555;
        }}
        .test-case {{
            display: flex;
            align-items: center;
            padding: 8px 0;
        }}
        .test-case .icon {{
            margin-right: 10px;
            font-size: 1.2em;
        }}
        .test-case .name {{
            flex: 1;
        }}
        .test-case .duration {{
            color: #666;
            font-size: 0.9em;
        }}
        .assertion {{
            margin-left: 30px;
            padding: 5px 10px;
            background: #fff3cd;
            border-radius: 4px;
            margin-top: 5px;
            font-size: 0.9em;
        }}
        .success {{ background: #d4edda; color: #155724; }}
        .failure {{ background: #f8d7da; color: #721c24; }}
    </style>
</head>
<body>
    <div class="summary">
        <h1>测试报告</h1>
        <div class="stats">
            <div class="stat">
                <div class="stat-value">{summary.total_count}</div>
                <div class="stat-label">总测试数</div>
            </div>
            <div class="stat">
                <div class="stat-value passed">{summary.passed_count}</div>
                <div class="stat-label">通过</div>
            </div>
            <div class="stat">
                <div class="stat-value failed">{summary.failed_count}</div>
                <div class="stat-label">失败</div>
            </div>
            <div class="stat">
                <div class="stat-value error">{summary.error_count}</div>
                <div class="stat-label">错误</div>
            </div>
            <div class="stat">
                <div class="stat-value skipped">{summary.skipped_count}</div>
                <div class="stat-label">跳过</div>
            </div>
            <div class="stat">
                <div class="stat-value">{summary.success_rate:.1f}%</div>
                <div class="stat-label">成功率</div>
            </div>
        </div>
    </div>
"""

        for module in summary.modules:
            html += f"""
    <div class="module">
        <div class="module-header">
            <h2>{module.name} ({module.passed_count}/{module.total_count})</h2>
        </div>
"""
            for suite in module.suites:
                html += f"""
        <div class="suite">
            <h3>{suite.name}</h3>
"""
                for test_case in suite.test_cases:
                    icon = self._get_status_icon(test_case.status)
                    html += f"""
            <div class="test-case">
                <span class="icon">{icon}</span>
                <span class="name">{test_case.name}</span>
                <span class="duration">{test_case.duration:.3f}s</span>
            </div>
"""
                    if test_case.failed or test_case.error:
                        for assertion in test_case.assertions:
                            if not assertion.passed:
                                html += f"""
            <div class="assertion failure">
                ❌ {assertion.name}: {assertion.message}
            </div>
"""

                html += "        </div>\n"
            html += "    </div>\n"

        html += """
</body>
</html>
"""
        return html

    def _get_status_icon(self, status: TestStatus) -> str:
        """获取状态图标"""
        icons = {
            TestStatus.PASSED: "✅",
            TestStatus.FAILED: "❌",
            TestStatus.ERROR: "💥",
            TestStatus.SKIPPED: "⏭️",
            TestStatus.NOT_RUN: "⏳",
        }
        return icons.get(status, "❓")


class MarkdownReporter(Reporter):
    """Markdown 报告器"""

    def generate(self, summary: TestSummary) -> str:
        """生成 Markdown 报告"""
        lines = []
        lines.append("# 测试报告")
        lines.append("")
        lines.append("## 汇总")
        lines.append("")
        lines.append(f"| 指标 | 值 |")
        lines.append(f"|------|-----|")
        lines.append(f"| 总测试数 | {summary.total_count} |")
        lines.append(f"| 通过 | {summary.passed_count} |")
        lines.append(f"| 失败 | {summary.failed_count} |")
        lines.append(f"| 错误 | {summary.error_count} |")
        lines.append(f"| 跳过 | {summary.skipped_count} |")
        lines.append(f"| 成功率 | {summary.success_rate:.1f}% |")
        lines.append(f"| 执行时间 | {summary.duration:.3f}s |")
        lines.append("")

        for module in summary.modules:
            lines.append(f"## 模块: {module.name}")
            lines.append("")

            for suite in module.suites:
                lines.append(f"### 套件: {suite.name}")
                lines.append("")
                lines.append("| 测试用例 | 状态 | 时间 |")
                lines.append("|----------|------|------|")

                for test_case in suite.test_cases:
                    icon = self._get_status_icon(test_case.status)
                    lines.append(
                        f"| {test_case.name} | {icon} | {test_case.duration:.3f}s |"
                    )

                lines.append("")

        return "\n".join(lines)

    def _get_status_icon(self, status: TestStatus) -> str:
        """获取状态图标"""
        icons = {
            TestStatus.PASSED: "✅ 通过",
            TestStatus.FAILED: "❌ 失败",
            TestStatus.ERROR: "💥 错误",
            TestStatus.SKIPPED: "⏭️ 跳过",
            TestStatus.NOT_RUN: "⏳ 未运行",
        }
        return icons.get(status, "❓")


def generate_report(summary: TestSummary, format: str = "text") -> str:
    """
    生成测试报告

    Args:
        summary: 测试汇总结果
        format: 报告格式 (text, json, junit, html, markdown)

    Returns:
        报告内容字符串
    """
    reporters = {
        "text": TextReporter(),
        "json": JsonReporter(),
        "junit": JUnitReporter(),
        "html": HtmlReporter(),
        "markdown": MarkdownReporter(),
    }

    reporter = reporters.get(format, TextReporter())
    return reporter.generate(summary)


def save_report(summary: TestSummary, path: str, format: str = "text") -> None:
    """
    保存测试报告到文件

    Args:
        summary: 测试汇总结果
        path: 文件路径
        format: 报告格式
    """
    report = generate_report(summary, format)
    Path(path).write_text(report, encoding="utf-8")
