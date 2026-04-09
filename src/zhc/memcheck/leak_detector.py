"""
内存泄漏检测器
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

from .tracker import MemTracker
from .data import MemBlock


class LeakType(Enum):
    """泄漏类型"""

    NORMAL = "normal"  # 常规泄漏
    ARRAY = "array"  # 数组泄漏
    MEMORY_LEAK = "memory_leak"  # 内存泄漏
    RESOURCE_LEAK = "resource_leak"  # 资源泄漏


@dataclass
class LeakReport:
    """泄漏报告"""

    leak_type: LeakType
    block: MemBlock
    severity: str  # critical, high, medium, low
    description: str
    suggested_fix: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "leak_type": self.leak_type.value,
            "block": self.block.to_dict(),
            "severity": self.severity,
            "description": self.description,
            "suggested_fix": self.suggested_fix,
        }


class LeakDetector:
    """内存泄漏检测器

    用法示例：

    ```python
    from zhc.memcheck import LeakDetector, MemTracker

    tracker = MemTracker()
    tracker.start()
    # ... 执行代码 ...
    tracker.stop()

    # 检测泄漏
    detector = LeakDetector(tracker)
    leaks = detector.detect()

    for leak in leaks:
        print(f"{leak.severity}: {leak.description}")
        print(f"  Fix: {leak.suggested_fix}")

    # 生成报告
    print(detector.generate_report())
    ```
    """

    def __init__(self, tracker: MemTracker):
        """初始化泄漏检测器

        Args:
            tracker: 内存追踪器
        """
        self.tracker = tracker
        self.leaks: List[LeakReport] = []

    def detect(self) -> List[LeakReport]:
        """检测内存泄漏

        Returns:
            泄漏报告列表
        """
        self.leaks = []
        blocks = self.tracker.get_all_blocks()

        for block in blocks:
            report = self._analyze_block(block)
            if report:
                self.leaks.append(report)

        # 按严重程度排序
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        self.leaks.sort(
            key=lambda x: (severity_order.get(x.severity, 4), -x.block.size)
        )

        return self.leaks

    def _analyze_block(self, block: MemBlock) -> Optional[LeakReport]:
        """分析单个内存块

        Args:
            block: 内存块

        Returns:
            泄漏报告，如果无泄漏返回 None
        """
        # 根据大小分类
        if block.size >= 1024 * 1024:  # >= 1MB
            return LeakReport(
                leak_type=LeakType.MEMORY_LEAK,
                block=block,
                severity="critical",
                description=f"大内存泄漏: {block.size} bytes ({block.file}:{block.line})",
                suggested_fix="确保在适当的时机释放大内存块，考虑使用智能指针或对象池",
            )

        elif block.size >= 100 * 1024:  # >= 100KB
            return LeakReport(
                leak_type=LeakType.MEMORY_LEAK,
                block=block,
                severity="high",
                description=f"中等内存泄漏: {block.size} bytes ({block.file}:{block.line})",
                suggested_fix="检查是否所有代码路径都能正确释放内存",
            )

        elif block.size >= 10 * 1024:  # >= 10KB
            return LeakReport(
                leak_type=LeakType.NORMAL,
                block=block,
                severity="medium",
                description=f"小内存泄漏: {block.size} bytes ({block.file}:{block.line})",
                suggested_fix="确认所有分配的内存都有对应的释放代码",
            )

        else:
            return LeakReport(
                leak_type=LeakType.NORMAL,
                block=block,
                severity="low",
                description=f"微量内存泄漏: {block.size} bytes ({block.file}:{block.line})",
                suggested_fix="检查是否有遗漏的释放代码",
            )

    def get_summary(self) -> Dict[str, Any]:
        """获取泄漏摘要"""
        stats = self.tracker.get_stats()

        return {
            "total_leaks": len(self.leaks),
            "total_leak_bytes": stats.leak_bytes,
            "by_severity": {
                "critical": len(
                    [leak for leak in self.leaks if leak.severity == "critical"]
                ),
                "high": len([leak for leak in self.leaks if leak.severity == "high"]),
                "medium": len(
                    [leak for leak in self.leaks if leak.severity == "medium"]
                ),
                "low": len([leak for leak in self.leaks if leak.severity == "low"]),
            },
            "by_type": {
                "memory_leak": len(
                    [
                        leak
                        for leak in self.leaks
                        if leak.leak_type == LeakType.MEMORY_LEAK
                    ]
                ),
                "normal": len(
                    [leak for leak in self.leaks if leak.leak_type == LeakType.NORMAL]
                ),
                "array": len(
                    [leak for leak in self.leaks if leak.leak_type == LeakType.ARRAY]
                ),
                "resource_leak": len(
                    [
                        leak
                        for leak in self.leaks
                        if leak.leak_type == LeakType.RESOURCE_LEAK
                    ]
                ),
            },
        }

    def generate_report(self) -> str:
        """生成泄漏报告"""
        lines = []

        lines.append("")
        lines.append(
            "╔══════════════════════════════════════════════════════════════════════════════════╗"
        )
        lines.append(
            "║                              内存泄漏检测报告                                   ║"
        )
        lines.append(
            "╚══════════════════════════════════════════════════════════════════════════════════╝"
        )
        lines.append("")

        summary = self.get_summary()

        if len(self.leaks) == 0:
            lines.append("✓ 未检测到内存泄漏")
            lines.append("")
            return "\n".join(lines)

        lines.append(f"发现 {summary['total_leaks']} 处内存泄漏")
        lines.append(f"泄漏总量: {summary['total_leak_bytes']} bytes")
        lines.append("")

        # 按严重程度分组
        severity_groups = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
        }

        for leak in self.leaks:
            severity_groups[leak.severity].append(leak)

        for severity in ["critical", "high", "medium", "low"]:
            group = severity_groups[severity]
            if not group:
                continue

            icon = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢",
            }[severity]

            lines.append(f"{icon} {severity.upper()} ({len(group)} 处)")
            lines.append("─" * 80)

            for leak in group[:10]:  # 最多显示 10 个
                lines.append(f"  {leak.description}")
                lines.append(f"    地址: {leak.block.ptr_address}")
                lines.append(f"    大小: {leak.block.size} B")
                lines.append(f"    修复: {leak.suggested_fix}")
                lines.append("")

            if len(group) > 10:
                lines.append(f"  ... 还有 {len(group) - 10} 处")
                lines.append("")

        # 优化建议
        lines.append("【整体优化建议】")
        lines.append("")

        if summary["by_severity"]["critical"] > 0:
            lines.append("1. 优先修复 CRITICAL 级别的泄漏，这些通常是最大的内存问题")
        if summary["by_severity"]["high"] > 0:
            lines.append("2. 检查 HIGH 级别的泄漏，确保所有大内存块被正确释放")
        if summary["total_leaks"] > 10:
            lines.append("3. 泄漏数量较多，考虑重构内存管理策略")
            lines.append("   - 使用RAII模式管理资源")
            lines.append("   - 使用智能指针")
            lines.append("   - 建立对象池复用内存")

        lines.append("")
        return "\n".join(lines)

    def get_json_report(self) -> Dict[str, Any]:
        """获取 JSON 格式报告"""
        return {
            "summary": self.get_summary(),
            "leaks": [leak.to_dict() for leak in self.leaks],
        }
