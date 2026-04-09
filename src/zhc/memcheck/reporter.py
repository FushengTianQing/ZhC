"""
内存使用报告生成器
"""

import json
from abc import ABC, abstractmethod

from .tracker import MemTracker


class MemReporter(ABC):
    """报告生成器基类"""

    @abstractmethod
    def generate(self, tracker: MemTracker) -> str:
        """生成报告

        Args:
            tracker: 追踪器实例

        Returns:
            报告字符串
        """
        pass


class TextReporter(MemReporter):
    """纯文本报告生成器"""

    def generate(self, tracker: MemTracker) -> str:
        lines = []
        stats = tracker.get_stats()
        blocks = tracker.get_all_blocks()

        # 头部
        lines.append("")
        lines.append(
            "╔══════════════════════════════════════════════════════════════════════════════════╗"
        )
        lines.append(
            "║                              内存使用报告                                        ║"
        )
        lines.append(
            "╚══════════════════════════════════════════════════════════════════════════════════╝"
        )
        lines.append("")

        # 统计摘要
        lines.append("【统计摘要】")
        lines.append(f"  总分配:       {stats.total_alloc}")
        lines.append(f"  总释放:       {stats.total_free}")
        lines.append(f"  当前使用:     {stats.current_used}")
        lines.append(f"  峰值使用:     {stats.peak_used}")
        lines.append("")
        lines.append(f"  分配次数:     {stats.alloc_count:,}")
        lines.append(f"  释放次数:     {stats.free_count:,}")
        lines.append(f"  无效释放:     {stats.invalid_free_count}")
        lines.append("")

        # 泄漏信息
        if blocks:
            lines.append("═══ 内存泄漏 ═══")
            lines.append("")
            lines.append(f"发现 {len(blocks)} 处泄漏，共 {stats.leak_bytes} 字节")
            lines.append("")

            for block in sorted(blocks, key=lambda b: b.size, reverse=True)[:20]:
                lines.append(f"  泄漏 #{block.alloc_id}:")
                lines.append(f"    地址:   {block.ptr_address}")
                lines.append(f"    大小:   {block.size} B")
                lines.append(f"    位置:   {block.file}:{block.line} ({block.func})")
                lines.append("")

            if len(blocks) > 20:
                lines.append(f"  ... 还有 {len(blocks) - 20} 处泄漏")
                lines.append("")
        else:
            lines.append("✓ 未检测到内存泄漏")
            lines.append("")

        # 分配源统计
        alloc_sites = tracker.get_alloc_sites()
        if alloc_sites:
            lines.append("【分配源统计】（按当前使用排序）")
            lines.append("")
            lines.append(f"{'位置':<40} {'次数':>8} {'总大小':>12} {'当前':>12}")
            lines.append("─" * 80)

            sorted_sites = sorted(
                alloc_sites, key=lambda s: s.current_bytes, reverse=True
            )[:15]

            for site in sorted_sites:
                location = f"{site.file}:{site.line}"
                if len(location) > 38:
                    location = "..." + location[-38:]
                lines.append(
                    f"{location:<40} {site.alloc_count:>8} "
                    f"{site.total:>12} {site.current:>12}"
                )

            lines.append("")

        return "\n".join(lines)


class JsonReporter(MemReporter):
    """JSON 报告生成器"""

    def generate(self, tracker: MemTracker) -> str:
        stats = tracker.get_stats()
        blocks = tracker.get_all_blocks()
        alloc_sites = tracker.get_alloc_sites()

        data = {
            "stats": stats.to_dict(),
            "leaks": [b.to_dict() for b in blocks],
            "alloc_sites": [s.to_dict() for s in alloc_sites],
        }

        return json.dumps(data, indent=2, ensure_ascii=False)


class HtmlReporter(MemReporter):
    """HTML 报告生成器"""

    def generate(self, tracker: MemTracker) -> str:
        stats = tracker.get_stats()
        blocks = tracker.get_all_blocks()
        alloc_sites = tracker.get_alloc_sites()

        lines = [
            "<!DOCTYPE html>",
            '<html lang="zh-CN">',
            "<head>",
            '    <meta charset="UTF-8">',
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
            "    <title>内存使用报告</title>",
            "    <style>",
            "        * { box-sizing: border-box; margin: 0; padding: 0; }",
            "        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;",
            "               background: #f5f5f5; padding: 20px; }",
            "        .container { max-width: 1200px; margin: 0 auto; }",
            "        h1 { color: #333; margin-bottom: 20px; }",
            "        .card { background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px;",
            "               box-shadow: 0 2px 4px rgba(0,0,0,0.1); }",
            "        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));",
            "                 gap: 15px; margin-bottom: 20px; }",
            "        .stat { background: #f8f9fa; padding: 15px; border-radius: 4px; }",
            "        .stat-label { color: #666; font-size: 14px; }",
            "        .stat-value { font-size: 24px; font-weight: bold; color: #333; }",
            "        .leak { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px;",
            "                margin-bottom: 10px; border-radius: 4px; }",
            "        .leak-addr { font-family: monospace; color: #666; }",
            "        .leak-size { font-weight: bold; color: #856404; }",
            "        .leak-loc { font-family: monospace; font-size: 12px; color: #666; margin-top: 5px; }",
            "        .ok { color: #28a745; font-size: 18px; }",
            "        table { width: 100%; border-collapse: collapse; }",
            "        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }",
            "        th { background: #f8f9fa; font-weight: 600; }",
            "        tr:hover { background: #f8f9fa; }",
            "        .mono { font-family: monospace; }",
            "    </style>",
            "</head>",
            "<body>",
            '    <div class="container">',
            "        <h1>📊 内存使用报告</h1>",
            "",
            '        <div class="stats">',
            f'            <div class="stat"><div class="stat-label">当前使用</div>',
            f'                <div class="stat-value">{stats.current_used}</div></div>',
            f'            <div class="stat"><div class="stat-label">峰值使用</div>',
            f'                <div class="stat-value">{stats.peak_used}</div></div>',
            f'            <div class="stat"><div class="stat-label">总分配</div>',
            f'                <div class="stat-value">{stats.total_alloc}</div></div>',
            f'            <div class="stat"><div class="stat-label">分配次数</div>',
            f'                <div class="stat-value">{stats.alloc_count:,}</div></div>',
            "        </div>",
            "",
            '        <div class="card">',
            "            <h2>泄漏检测</h2>",
        ]

        if blocks:
            lines.append(
                f'            <p style="color: #856404;">发现 {len(blocks)} 处内存泄漏，共 {stats.leak_bytes} 字节</p>'
            )
            lines.append("")

            for block in sorted(blocks, key=lambda b: b.size, reverse=True)[:20]:
                lines.append(f'            <div class="leak">')
                lines.append(
                    f'                <div class="leak-addr">{block.ptr_address}</div>'
                )
                lines.append(
                    f'                <div class="leak-size">{block.size} B</div>'
                )
                lines.append(
                    f'                <div class="leak-loc">{block.file}:{block.line} ({block.func})</div>'
                )
                lines.append(f"            </div>")
        else:
            lines.append('            <p class="ok">✓ 未检测到内存泄漏</p>')

        lines.extend(
            [
                "        </div>",
                "",
                '        <div class="card">',
                "            <h2>分配源统计</h2>",
                "            <table>",
                "                <thead>",
                "                    <tr>",
                "                        <th>位置</th>",
                "                        <th>函数</th>",
                "                        <th>分配次数</th>",
                "                        <th>总大小</th>",
                "                        <th>当前大小</th>",
                "                    </tr>",
                "                </thead>",
                "                <tbody>",
            ]
        )

        sorted_sites = sorted(alloc_sites, key=lambda s: s.current_bytes, reverse=True)[
            :20
        ]
        for site in sorted_sites:
            lines.append("                    <tr>")
            lines.append(
                f'                        <td class="mono">{site.file}:{site.line}</td>'
            )
            lines.append(f'                        <td class="mono">{site.func}</td>')
            lines.append(f"                        <td>{site.alloc_count}</td>")
            lines.append(f"                        <td>{site.total}</td>")
            lines.append(f"                        <td>{site.current}</td>")
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


# 便捷函数
def get_reporter(format: str = "text") -> MemReporter:
    """获取报告生成器

    Args:
        format: 报告格式 (text, json, html)

    Returns:
        报告生成器实例
    """
    reporters = {
        "text": TextReporter,
        "json": JsonReporter,
        "html": HtmlReporter,
    }

    reporter_class = reporters.get(format.lower())
    if not reporter_class:
        raise ValueError(f"不支持的报告格式: {format}")

    return reporter_class()


def generate_report(
    tracker: MemTracker,
    format: str = "text",
) -> str:
    """生成内存使用报告

    Args:
        tracker: 追踪器实例
        format: 报告格式 (text, json, html)

    Returns:
        报告字符串
    """
    reporter = get_reporter(format)
    return reporter.generate(tracker)
