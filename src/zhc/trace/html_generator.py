# -*- coding: utf-8 -*-
"""
HTML 可视化生成器

生成 trace.html 用于可视化执行轨迹。

作者：远
日期：2026-04-13
"""

from pathlib import Path
from typing import Optional

from .schema import TraceRecord, TraceEvent, TraceEventType


class HTMLGenerator:
    """HTML 可视化生成器"""

    def __init__(self, title: str = "ZhC 执行追踪"):
        self.title = title

    def generate(self, record: TraceRecord, source_code: Optional[str] = None) -> str:
        """
        生成 HTML 内容

        Args:
            record: 追踪记录
            source_code: 源代码（可选）

        Returns:
            HTML 字符串
        """
        html_parts = [
            self._html_header(),
            self._html_body_start(),
        ]

        if source_code:
            html_parts.append(self._html_source_section(source_code, record))

        html_parts.append(self._html_trace_section(record))
        html_parts.append(self._html_stats_section(record))
        html_parts.append(self._html_body_end())

        return "\n".join(html_parts)

    def save(
        self, record: TraceRecord, output_path: Path, source_code: Optional[str] = None
    ) -> Path:
        """
        保存 HTML 文件

        Args:
            record: 追踪记录
            output_path: 输出路径
            source_code: 源代码

        Returns:
            保存的文件路径
        """
        html_content = self.generate(record, source_code)
        output_path.write_text(html_content, encoding="utf-8")
        return output_path

    def _html_header(self) -> str:
        """HTML 头部"""
        return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZhC 执行追踪</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: "PingFang SC", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e8e8e8;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 {
            text-align: center;
            color: #00d4ff;
            margin-bottom: 30px;
            text-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
        }
        h2 {
            color: #ffd700;
            margin: 20px 0 15px 0;
            padding-bottom: 8px;
            border-bottom: 2px solid #ffd700;
        }
        .section {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .source-code {
            background: #0d1117;
            border-radius: 8px;
            padding: 15px;
            overflow-x: auto;
            font-family: "JetBrains Mono", "Fira Code", monospace;
            font-size: 14px;
            line-height: 1.6;
        }
        .source-line {
            display: flex;
            padding: 2px 0;
        }
        .source-line.executed {
            background: rgba(0, 255, 100, 0.15);
        }
        .source-line.current {
            background: rgba(255, 215, 0, 0.3);
            border-left: 3px solid #ffd700;
        }
        .line-num {
            color: #6e7681;
            width: 50px;
            text-align: right;
            padding-right: 15px;
            user-select: none;
        }
        .line-content { flex: 1; white-space: pre; }
        .trace-container {
            background: #0d1117;
            border-radius: 8px;
            overflow: hidden;
        }
        .trace-event {
            display: flex;
            align-items: center;
            padding: 8px 15px;
            border-bottom: 1px solid #21262d;
            font-family: "JetBrains Mono", "Fira Code", monospace;
            font-size: 13px;
            cursor: pointer;
            transition: background 0.2s;
        }
        .trace-event:hover {
            background: rgba(255, 255, 255, 0.1);
        }
        .trace-event.func-enter {
            background: rgba(0, 212, 255, 0.1);
        }
        .trace-event.func-exit {
            background: rgba(255, 107, 107, 0.1);
        }
        .trace-event.var-assign {
            background: rgba(0, 255, 100, 0.1);
        }
        .trace-event.branch {
            background: rgba(255, 215, 0, 0.1);
        }
        .trace-event.loop {
            background: rgba(156, 89, 255, 0.1);
        }
        .event-depth {
            color: #6e7681;
            width: 40px;
            text-align: center;
        }
        .event-type {
            width: 100px;
            text-align: center;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            margin-right: 15px;
        }
        .event-type.func-enter { background: #00d4ff; color: #000; }
        .event-type.func-exit { background: #ff6b6b; color: #000; }
        .event-type.var-assign { background: #00ff64; color: #000; }
        .event-type.branch { background: #ffd700; color: #000; }
        .event-type.loop { background: #9c59ff; color: #000; }
        .event-name {
            color: #79c0ff;
            flex: 1;
            margin-right: 15px;
        }
        .event-value {
            color: #ffa657;
            background: rgba(255, 166, 87, 0.2);
            padding: 2px 8px;
            border-radius: 4px;
        }
        .event-location {
            color: #6e7681;
            font-size: 11px;
            margin-left: 15px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }
        .stat-card {
            background: rgba(0, 212, 255, 0.1);
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }
        .stat-value {
            font-size: 28px;
            font-weight: bold;
            color: #00d4ff;
        }
        .stat-label {
            color: #8b949e;
            font-size: 12px;
            margin-top: 5px;
        }
        .controls {
            position: sticky;
            top: 0;
            background: rgba(26, 26, 46, 0.95);
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: flex;
            gap: 15px;
            align-items: center;
            z-index: 100;
        }
        .btn {
            background: #00d4ff;
            color: #000;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.2s;
        }
        .btn:hover {
            background: #00a8cc;
            transform: translateY(-2px);
        }
        .search-box {
            flex: 1;
            background: #21262d;
            border: 1px solid #30363d;
            color: #e8e8e8;
            padding: 8px 15px;
            border-radius: 6px;
            font-size: 14px;
        }
        .search-box:focus {
            outline: none;
            border-color: #00d4ff;
        }
        .filter-chip {
            background: #30363d;
            color: #8b949e;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .filter-chip.active {
            background: #00d4ff;
            color: #000;
        }
        .highlight { background: #ff6b6b; color: #000; padding: 0 4px; border-radius: 2px; }
    </style>
</head>"""

    def _html_body_start(self) -> str:
        """HTML body 开始"""
        return f"""<body>
    <div class="container">
        <h1>🔧 {self.title}</h1>
        <div class="controls">
            <button class="btn" onclick="expandAll()">展开全部</button>
            <button class="btn" onclick="collapseAll()">折叠全部</button>
            <input type="text" class="search-box" id="searchBox" placeholder="搜索..." oninput="filterEvents()">
            <span class="filter-chip active" onclick="toggleFilter('all')">全部</span>
            <span class="filter-chip" onclick="toggleFilter('func')">函数</span>
            <span class="filter-chip" onclick="toggleFilter('var')">变量</span>
            <span class="filter-chip" onclick="toggleFilter('branch')">分支</span>
            <span class="filter-chip" onclick="toggleFilter('loop')">循环</span>
        </div>
"""

    def _html_source_section(self, source_code: str, record: TraceRecord) -> str:
        """源代码区域"""
        lines = source_code.split("\n")
        executed_lines = set()

        # 收集执行过的行号
        for event in record.events:
            if event.location:
                executed_lines.add(event.location.line)

        source_html = [
            '        <div class="section">',
            "            <h2>📄 源代码</h2>",
            '            <div class="source-code">',
        ]

        for i, line in enumerate(lines, 1):
            executed_class = "executed" if i in executed_lines else ""
            source_html.append(
                f'                <div class="source-line {executed_class}" data-line="{i}">'
            )
            source_html.append(f'                    <span class="line-num">{i}</span>')
            source_html.append(
                f'                    <span class="line-content">{self._escape_html(line)}</span>'
            )
            source_html.append("                </div>")

        source_html.extend(["            </div>", "        </div>"])
        return "\n".join(source_html)

    def _html_trace_section(self, record: TraceRecord) -> str:
        """追踪事件区域"""
        trace_html = [
            '        <div class="section">',
            "            <h2>📊 执行轨迹</h2>",
            '            <div class="trace-container" id="traceContainer">',
        ]

        for event in record.events:
            event_html = self._format_event(event)
            trace_html.append(f"                {event_html}")

        trace_html.extend(["            </div>", "        </div>"])
        return "\n".join(trace_html)

    def _format_event(self, event: TraceEvent) -> str:
        """格式化单个事件"""
        # 确定事件类型样式类
        type_class = event.type.value.replace("_", "-")
        if event.type in (TraceEventType.FUNC_ENTER, TraceEventType.CALL_ENTER):
            type_class = "func-enter"
        elif event.type in (TraceEventType.FUNC_EXIT, TraceEventType.CALL_EXIT):
            type_class = "func-exit"
        elif event.type == TraceEventType.VAR_ASSIGN:
            type_class = "var-assign"
        elif event.type in (TraceEventType.BRANCH_TAKEN, TraceEventType.BRANCH_SKIPPED):
            type_class = "branch"
        elif event.type in (
            TraceEventType.LOOP_ENTER,
            TraceEventType.LOOP_EXIT,
            TraceEventType.LOOP_ITER,
        ):
            type_class = "loop"

        # 缩进
        indent = "　" * event.call_depth

        # 类型标签
        type_label = {
            TraceEventType.FUNC_ENTER: "进入",
            TraceEventType.FUNC_EXIT: "退出",
            TraceEventType.FUNC_RETURN: "返回",
            TraceEventType.VAR_DECL: "声明",
            TraceEventType.VAR_ASSIGN: "赋值",
            TraceEventType.VAR_READ: "读取",
            TraceEventType.BRANCH_TAKEN: "执行",
            TraceEventType.BRANCH_SKIPPED: "跳过",
            TraceEventType.LOOP_ENTER: "入循环",
            TraceEventType.LOOP_EXIT: "出循环",
            TraceEventType.LOOP_ITER: "迭代",
            TraceEventType.EXPR_EVAL: "求值",
            TraceEventType.CALL_ENTER: "调用",
            TraceEventType.CALL_EXIT: "返回",
            TraceEventType.ERROR: "错误",
        }.get(event.type, event.type.value)

        # 位置信息
        location = ""
        if event.location:
            location = f"行{event.location.line}"

        # 值信息
        value = ""
        if event.value is not None:
            value = f'<span class="event-value">{self._escape_html(str(event.value))}</span>'

        return f"""<div class="trace-event {type_class}" data-type="{type_class}">
                <span class="event-depth">{indent}</span>
                <span class="event-type {type_class}">{type_label}</span>
                <span class="event-name">{self._escape_html(event.name or "")}</span>
                {value}
                <span class="event-location">{location}</span>
            </div>"""

    def _html_stats_section(self, record: TraceRecord) -> str:
        """统计信息区域"""
        record.compute_stats()
        stats = record.stats

        return f"""        <div class="section">
            <h2>📈 统计信息</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{stats.get("total_events", 0)}</div>
                    <div class="stat-label">总事件数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{stats.get("func_calls", 0)}</div>
                    <div class="stat-label">函数调用</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{stats.get("var_assigns", 0)}</div>
                    <div class="stat-label">变量赋值</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{stats.get("branches", 0)}</div>
                    <div class="stat-label">分支判断</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{stats.get("loops", 0)}</div>
                    <div class="stat-label">循环次数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{stats.get("max_call_depth", 0)}</div>
                    <div class="stat-label">最大调用深度</div>
                </div>
            </div>
        </div>"""

    def _html_body_end(self) -> str:
        """HTML body 结尾"""
        return """        <script>
        function expandAll() {
            document.querySelectorAll('.trace-event').forEach(e => e.style.display = 'flex');
        }
        function collapseAll() {
            document.querySelectorAll('.trace-event').forEach(e => e.style.display = 'none');
        }
        function filterEvents() {
            const query = document.getElementById('searchBox').value.toLowerCase();
            document.querySelectorAll('.trace-event').forEach(e => {
                const text = e.textContent.toLowerCase();
                e.style.display = text.includes(query) ? 'flex' : 'none';
            });
        }
        function toggleFilter(type) {
            document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
            event.target.classList.add('active');
            if (type === 'all') {
                document.querySelectorAll('.trace-event').forEach(e => e.style.display = 'flex');
            } else {
                document.querySelectorAll('.trace-event').forEach(e => {
                    e.style.display = e.dataset.type.includes(type) ? 'flex' : 'none';
                });
            }
        }
        </script>
    </div>
</body>
</html>"""

    @staticmethod
    def _escape_html(text: str) -> str:
        """转义 HTML 特殊字符"""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )
