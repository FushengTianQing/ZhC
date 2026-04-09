"""
性能剖析报告生成器
"""

import json
from abc import ABC, abstractmethod
from typing import List, Dict

from .data import FunctionProfile
from .tracker import ProfilerTracker


class ProfilerReporter(ABC):
    """报告生成器基类"""

    @abstractmethod
    def generate(
        self,
        tracker: ProfilerTracker,
        top_n: int = 20,
    ) -> str:
        """生成报告

        Args:
            tracker: 追踪器实例
            top_n: 显示的函数数量

        Returns:
            报告字符串
        """
        pass

    def _get_sorted_functions(
        self,
        tracker: ProfilerTracker,
        top_n: int = 20,
    ) -> List[FunctionProfile]:
        """获取排序后的函数列表"""
        funcs = tracker.get_all_functions()
        total_time = sum(f.total_time_ns for f in funcs)

        # 计算占比并排序
        for func in funcs:
            if total_time > 0:
                func._percentage = func.total_time_ns / total_time * 100
            else:
                func._percentage = 0

        return sorted(funcs, key=lambda f: f.total_time_ns, reverse=True)[:top_n]


class TextReporter(ProfilerReporter):
    """纯文本报告生成器"""

    def generate(
        self,
        tracker: ProfilerTracker,
        top_n: int = 20,
    ) -> str:
        lines = []
        stats = tracker.get_stats()

        # 头部
        lines.append("")
        lines.append(
            "╔══════════════════════════════════════════════════════════════════════════════════╗"
        )
        lines.append(
            "║                              性能剖析报告                                        ║"
        )
        lines.append(
            "╚══════════════════════════════════════════════════════════════════════════════════╝"
        )
        lines.append("")

        # 统计摘要
        lines.append("【统计摘要】")
        lines.append(f"  总调用次数:     {stats.total_calls:,}")
        lines.append(f"  总执行时间:     {self._format_time(stats.total_time_ns)}")
        lines.append(f"  记录函数数:     {stats.function_count:,}")
        lines.append(f"  最大调用深度:   {stats.max_depth}")
        lines.append(f"  剖析耗时:       {self._format_time(stats.elapsed_ns)}")
        lines.append("")

        # 函数排名
        lines.append("【函数执行排名】（按总时间排序）")
        lines.append("")
        lines.append(
            f"{'排名':<4} {'函数名':<30} {'调用次数':>10} {'总时间':>15} {'平均时间':>12} {'最大时间':>12} {'占比':>8}"
        )
        lines.append("─" * 110)

        funcs = self._get_sorted_functions(tracker, top_n)
        total_time = stats.total_time_ns

        for i, func in enumerate(funcs, 1):
            avg_time = (
                func.total_time_ns / func.call_count if func.call_count > 0 else 0
            )
            percentage = (
                (func.total_time_ns / total_time * 100) if total_time > 0 else 0
            )

            lines.append(
                f"{i:<4} "
                f"{func.name:<30} "
                f"{func.call_count:>10,} "
                f"{self._format_time(func.total_time_ns):>15} "
                f"{self._format_time(int(avg_time)):>12} "
                f"{self._format_time(func.max_time_ns):>12} "
                f"{percentage:>7.2f}%"
            )

        lines.append("")

        # 调用关系
        if tracker.config.track_call_graph:
            relations = tracker.get_call_relations()
            if relations:
                lines.append("【调用关系】（按调用次数排序）")
                lines.append("")
                lines.append(
                    f"{'调用者':<20} → {'被调用者':<20} {'调用次数':>10} {'总时间':>15}"
                )
                lines.append("─" * 70)

                sorted_relations = sorted(
                    relations, key=lambda r: r.call_count, reverse=True
                )[:20]

                for rel in sorted_relations:
                    lines.append(
                        f"{rel.caller:<20} → {rel.callee:<20} "
                        f"{rel.call_count:>10,} {self._format_time(rel.total_time_ns):>15}"
                    )

                lines.append("")

        return "\n".join(lines)

    def _format_time(self, ns: int) -> str:
        """格式化时间"""
        if ns < 1000:
            return f"{ns} ns"
        elif ns < 1_000_000:
            return f"{ns / 1000:.2f} us"
        elif ns < 1_000_000_000:
            return f"{ns / 1_000_000:.2f} ms"
        else:
            return f"{ns / 1_000_000_000:.3f} s"


class JsonReporter(ProfilerReporter):
    """JSON 报告生成器"""

    def generate(
        self,
        tracker: ProfilerTracker,
        top_n: int = 20,
    ) -> str:
        stats = tracker.get_stats()
        funcs = self._get_sorted_functions(tracker, top_n)
        relations = tracker.get_call_relations()

        data = {
            "stats": {
                "total_calls": stats.total_calls,
                "total_time_ns": stats.total_time_ns,
                "total_time_ms": stats.total_time_ns / 1_000_000,
                "total_time_s": stats.total_time_ns / 1_000_000_000,
                "function_count": stats.function_count,
                "max_depth": stats.max_depth,
                "elapsed_ns": stats.elapsed_ns,
            },
            "functions": [
                {
                    "name": f.name,
                    "call_count": f.call_count,
                    "total_time_ns": f.total_time_ns,
                    "total_time_ms": f.total_time_ns / 1_000_000,
                    "min_time_ns": f.min_time_ns,
                    "max_time_ns": f.max_time_ns,
                    "avg_time_ns": int(f.avg_time_ns),
                    "children": f.children,
                }
                for f in funcs
            ],
            "relations": [
                {
                    "caller": r.caller,
                    "callee": r.callee,
                    "call_count": r.call_count,
                    "total_time_ns": r.total_time_ns,
                }
                for r in relations
            ],
        }

        return json.dumps(data, indent=2, ensure_ascii=False)


class HtmlReporter(ProfilerReporter):
    """HTML 报告生成器"""

    def generate(
        self,
        tracker: ProfilerTracker,
        top_n: int = 20,
    ) -> str:
        stats = tracker.get_stats()
        funcs = self._get_sorted_functions(tracker, top_n)
        total_time = stats.total_time_ns

        lines = [
            "<!DOCTYPE html>",
            '<html lang="zh-CN">',
            "<head>",
            '    <meta charset="UTF-8">',
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
            "    <title>性能剖析报告</title>",
            "    <style>",
            "        * { box-sizing: border-box; margin: 0; padding: 0; }",
            "        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;",
            "               background: #f5f5f5; padding: 20px; }",
            "        .container { max-width: 1200px; margin: 0 auto; }",
            "        h1 { color: #333; margin-bottom: 20px; }",
            "        .card { background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px;",
            "               box-shadow: 0 2px 4px rgba(0,0,0,0.1); }",
            "        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));",
            "                 gap: 15px; margin-bottom: 20px; }",
            "        .stat { background: #f8f9fa; padding: 15px; border-radius: 4px; }",
            "        .stat-label { color: #666; font-size: 14px; }",
            "        .stat-value { font-size: 24px; font-weight: bold; color: #333; }",
            "        table { width: 100%; border-collapse: collapse; }",
            "        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }",
            "        th { background: #f8f9fa; font-weight: 600; }",
            "        tr:hover { background: #f8f9fa; }",
            "        .time { font-family: monospace; }",
            "        .percentage { color: #666; }",
            "        .bar { height: 8px; background: linear-gradient(90deg, #4CAF50, #81C784);",
            "               border-radius: 4px; margin-top: 5px; }",
            "        .mono { font-family: monospace; }",
            "    </style>",
            "</head>",
            "<body>",
            '    <div class="container">',
            "        <h1>⚡ 性能剖析报告</h1>",
            "",
            '        <div class="stats">',
            f'            <div class="stat"><div class="stat-label">总调用次数</div>',
            f'                <div class="stat-value">{stats.total_calls:,}</div></div>',
            f'            <div class="stat"><div class="stat-label">总执行时间</div>',
            f'                <div class="stat-value">{self._format_time(stats.total_time_ns)}</div></div>',
            f'            <div class="stat"><div class="stat-label">记录函数数</div>',
            f'                <div class="stat-value">{stats.function_count:,}</div></div>',
            f'            <div class="stat"><div class="stat-label">最大调用深度</div>',
            f'                <div class="stat-value">{stats.max_depth}</div></div>',
            "        </div>",
            "",
            '        <div class="card">',
            "            <h2>📊 函数执行排名</h2>",
            "            <table>",
            "                <thead>",
            "                    <tr>",
            "                        <th>#</th>",
            "                        <th>函数名</th>",
            "                        <th>调用次数</th>",
            "                        <th>总时间</th>",
            "                        <th>平均时间</th>",
            "                        <th>最大时间</th>",
            "                        <th>占比</th>",
            "                    </tr>",
            "                </thead>",
            "                <tbody>",
        ]

        for i, func in enumerate(funcs, 1):
            avg_time = (
                func.total_time_ns / func.call_count if func.call_count > 0 else 0
            )
            percentage = (
                (func.total_time_ns / total_time * 100) if total_time > 0 else 0
            )

            lines.append("                    <tr>")
            lines.append(f"                        <td>{i}</td>")
            lines.append(f'                        <td class="mono">{func.name}</td>')
            lines.append(f"                        <td>{func.call_count:,}</td>")
            lines.append(
                f'                        <td class="time">{self._format_time(func.total_time_ns)}</td>'
            )
            lines.append(
                f'                        <td class="time">{self._format_time(int(avg_time))}</td>'
            )
            lines.append(
                f'                        <td class="time">{self._format_time(func.max_time_ns)}</td>'
            )
            lines.append(
                f'                        <td>{percentage:.2f}%<div class="bar" style="width: {percentage}%"></div></td>'
            )
            lines.append("                    </tr>")

        lines.extend(
            [
                "                </tbody>",
                "            </table>",
                "        </div>",
                "    </div>",
                "</body>",
                "</html>",
            ]
        )

        return "\n".join(lines)

    def _format_time(self, ns: int) -> str:
        """格式化时间"""
        if ns < 1000:
            return f"{ns} ns"
        elif ns < 1_000_000:
            return f"{ns / 1000:.2f} us"
        elif ns < 1_000_000_000:
            return f"{ns / 1_000_000:.2f} ms"
        else:
            return f"{ns / 1_000_000_000:.3f} s"


class FlameGraphReporter(ProfilerReporter):
    """火焰图数据生成器"""

    def generate(
        self,
        tracker: ProfilerTracker,
        top_n: int = 100,
    ) -> str:
        """生成火焰图格式的数据

        输出格式：frame_name calls time
        """
        lines = []

        # 获取事件流
        events = tracker.get_events()

        # 按调用栈聚合
        stack_times: Dict[str, int] = {}
        stack_calls: Dict[str, int] = {}

        for event in events:
            if event.event_type.value == "enter":
                # 构建调用栈字符串
                # 简化处理：只记录叶子函数
                if len(tracker.call_stack) == 0:
                    key = f";{event.function_name}"
                else:
                    stack_names = [f.function_name for f in tracker.call_stack]
                    stack_names.append(event.function_name)
                    key = ";" + ";".join(stack_names)

                stack_times[key] = stack_times.get(key, 0)
                stack_calls[key] = stack_calls.get(key, 0) + 1

        # 输出
        for key in sorted(
            stack_times.keys(), key=lambda k: stack_times[k], reverse=True
        )[:top_n]:
            calls = stack_calls.get(key, 0)
            time_us = stack_times[key] / 1000
            lines.append(f"{key} {calls} {time_us:.2f}")

        return "\n".join(lines)


# 便捷函数
def get_reporter(format: str = "text") -> ProfilerReporter:
    """获取报告生成器

    Args:
        format: 报告格式 (text, json, html, flamegraph)

    Returns:
        报告生成器实例
    """
    reporters = {
        "text": TextReporter,
        "json": JsonReporter,
        "html": HtmlReporter,
        "flamegraph": FlameGraphReporter,
    }

    reporter_class = reporters.get(format.lower())
    if not reporter_class:
        raise ValueError(f"不支持的报告格式: {format}")

    return reporter_class()


def generate_report(
    tracker: ProfilerTracker,
    format: str = "text",
    top_n: int = 20,
) -> str:
    """生成性能报告

    Args:
        tracker: 追踪器实例
        format: 报告格式 (text, json, html, flamegraph)
        top_n: 显示的函数数量

    Returns:
        报告字符串
    """
    reporter = get_reporter(format)
    return reporter.generate(tracker, top_n)
