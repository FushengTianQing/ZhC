"""
热点分析器 - 识别性能瓶颈和优化建议
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum

from .tracker import ProfilerTracker


class OptimizationLevel(Enum):
    """优化级别"""

    CRITICAL = "critical"  # 关键优化
    HIGH = "high"  # 高优先级
    MEDIUM = "medium"  # 中优先级
    LOW = "low"  # 低优先级


@dataclass
class OptimizationHint:
    """优化建议"""

    level: OptimizationLevel
    category: str
    message: str
    current_value: Optional[Any] = None
    suggested_value: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level.value,
            "category": self.category,
            "message": self.message,
            "current_value": str(self.current_value) if self.current_value else None,
            "suggested_value": str(self.suggested_value)
            if self.suggested_value
            else None,
        }


@dataclass
class Hotspot:
    """热点函数"""

    function_name: str
    total_time_ns: int
    percentage: float
    call_count: int
    avg_time_ns: float
    min_time_ns: int
    max_time_ns: int
    call_depth: int
    hints: List[OptimizationHint] = field(default_factory=list)

    @property
    def total_time_ms(self) -> float:
        return self.total_time_ns / 1_000_000

    @property
    def avg_time_ms(self) -> float:
        return self.avg_time_ns / 1_000_000

    def to_dict(self) -> Dict[str, Any]:
        return {
            "function_name": self.function_name,
            "total_time_ns": self.total_time_ns,
            "total_time_ms": self.total_time_ms,
            "percentage": self.percentage,
            "call_count": self.call_count,
            "avg_time_ns": self.avg_time_ns,
            "avg_time_ms": self.avg_time_ms,
            "min_time_ns": self.min_time_ns,
            "max_time_ns": self.max_time_ns,
            "call_depth": self.call_depth,
            "hints": [h.to_dict() for h in self.hints],
        }


class HotspotAnalyzer:
    """热点分析器

    用法示例：

    ```python
    from zhc.profiler import HotspotAnalyzer, ProfilerTracker

    tracker = ProfilerTracker()
    tracker.start()
    # ... 执行代码 ...
    tracker.stop()

    # 分析热点
    analyzer = HotspotAnalyzer(tracker)
    hotspots = analyzer.analyze(threshold=5.0)  # 5% 阈值

    for hotspot in hotspots:
        print(f"{hotspot.function_name}: {hotspot.percentage:.2f}%")
        for hint in hotspot.hints:
            print(f"  [{hint.level.value}] {hint.message}")

    # 生成报告
    print(analyzer.generate_report())
    ```
    """

    def __init__(
        self,
        tracker: ProfilerTracker,
        *,
        time_threshold_ms: float = 1.0,
        percentage_threshold: float = 1.0,
    ):
        """初始化热点分析器

        Args:
            tracker: 追踪器实例
            time_threshold_ms: 时间阈值（毫秒），超过此阈值的函数会被标记
            percentage_threshold: 百分比阈值，超过此比例的函数会被标记
        """
        self.tracker = tracker
        self.time_threshold_ms = time_threshold_ms
        self.percentage_threshold = percentage_threshold
        self.hotspots: List[Hotspot] = []
        self.total_time_ns = 0

    def analyze(self, threshold: float = 1.0) -> List[Hotspot]:
        """分析热点函数

        Args:
            threshold: 时间占比阈值（百分比）

        Returns:
            热点函数列表
        """
        stats = self.tracker.get_stats()
        self.total_time_ns = stats.total_time_ns

        if self.total_time_ns == 0:
            return []

        # 获取所有函数
        funcs = self.tracker.get_all_functions()

        self.hotspots = []
        for func in funcs:
            percentage = (func.total_time_ns / self.total_time_ns) * 100

            if percentage >= threshold:
                hotspot = Hotspot(
                    function_name=func.name,
                    total_time_ns=func.total_time_ns,
                    percentage=percentage,
                    call_count=func.call_count,
                    avg_time_ns=func.avg_time_ns,
                    min_time_ns=func.min_time_ns
                    if func.min_time_ns != 0xFFFFFFFFFFFFFFFF
                    else 0,
                    max_time_ns=func.max_time_ns,
                    call_depth=func.call_depth,
                    hints=[],
                )

                # 生成优化建议
                hotspot.hints = self._generate_hints(hotspot)

                self.hotspots.append(hotspot)

        # 按时间占比排序
        self.hotspots.sort(key=lambda h: h.percentage, reverse=True)

        return self.hotspots

    def _generate_hints(self, hotspot: Hotspot) -> List[OptimizationHint]:
        """生成优化建议"""
        hints = []

        # 1. 检查执行时间占比
        if hotspot.percentage >= 50:
            hints.append(
                OptimizationHint(
                    level=OptimizationLevel.CRITICAL,
                    category="time",
                    message=f"该函数占总执行时间的 {hotspot.percentage:.1f}%，是主要的性能瓶颈",
                    current_value=f"{hotspot.percentage:.1f}%",
                    suggested_value="< 30%",
                )
            )
        elif hotspot.percentage >= 20:
            hints.append(
                OptimizationHint(
                    level=OptimizationLevel.HIGH,
                    category="time",
                    message=f"该函数占总执行时间的 {hotspot.percentage:.1f}%，可以考虑优化",
                    current_value=f"{hotspot.percentage:.1f}%",
                )
            )

        # 2. 检查调用次数
        if hotspot.call_count >= 10000:
            hints.append(
                OptimizationHint(
                    level=OptimizationLevel.HIGH,
                    category="call_count",
                    message="调用次数过多，考虑使用缓存或减少调用频率",
                    current_value=hotspot.call_count,
                )
            )
        elif hotspot.call_count >= 1000:
            hints.append(
                OptimizationHint(
                    level=OptimizationLevel.MEDIUM,
                    category="call_count",
                    message="调用次数较高，可以评估是否必要",
                    current_value=hotspot.call_count,
                )
            )

        # 3. 检查平均执行时间
        if hotspot.avg_time_ms >= 10:
            hints.append(
                OptimizationHint(
                    level=OptimizationLevel.CRITICAL,
                    category="avg_time",
                    message="单次执行时间过长（>10ms），需要优化算法",
                    current_value=f"{hotspot.avg_time_ms:.2f} ms",
                    suggested_value="< 1 ms",
                )
            )
        elif hotspot.avg_time_ms >= 1:
            hints.append(
                OptimizationHint(
                    level=OptimizationLevel.HIGH,
                    category="avg_time",
                    message="单次执行时间较长，可以考虑优化",
                    current_value=f"{hotspot.avg_time_ms:.2f} ms",
                )
            )

        # 4. 检查时间方差（max/min 比率）
        if hotspot.min_time_ns > 0:
            variance_ratio = hotspot.max_time_ns / hotspot.min_time_ns
            if variance_ratio >= 100:
                hints.append(
                    OptimizationHint(
                        level=OptimizationLevel.MEDIUM,
                        category="variance",
                        message=f"执行时间波动较大（最大/最小 = {variance_ratio:.0f}x），可能存在缓存或条件分支问题",
                        current_value=f"{variance_ratio:.0f}x",
                    )
                )

        # 5. 检查调用深度
        if hotspot.call_depth >= 5:
            hints.append(
                OptimizationHint(
                    level=OptimizationLevel.LOW,
                    category="call_depth",
                    message=f"调用深度较深（{hotspot.call_depth}层），考虑内联或重构",
                    current_value=hotspot.call_depth,
                )
            )

        # 6. 根据函数名生成特定建议
        hints.extend(self._generate_named_hints(hotspot))

        return hints

    def _generate_named_hints(self, hotspot: Hotspot) -> List[OptimizationHint]:
        """根据函数名生成特定建议"""
        hints = []
        name = hotspot.function_name.lower()

        # 循环相关
        if "loop" in name or "循环" in name:
            hints.append(
                OptimizationHint(
                    level=OptimizationLevel.MEDIUM,
                    category="loop",
                    message="考虑使用向量化或减少循环迭代次数",
                )
            )

        # 排序相关
        if "sort" in name or "排序" in name:
            hints.append(
                OptimizationHint(
                    level=OptimizationLevel.MEDIUM,
                    category="algorithm",
                    message="考虑使用更高效的排序算法或预排序",
                )
            )

        # 搜索相关
        if "search" in name or "find" in name or "搜索" in name:
            hints.append(
                OptimizationHint(
                    level=OptimizationLevel.MEDIUM,
                    category="algorithm",
                    message="考虑使用哈希表或二分搜索代替线性搜索",
                )
            )

        # 字符串相关
        if "string" in name or "str" in name or "字符串" in name:
            hints.append(
                OptimizationHint(
                    level=OptimizationLevel.LOW,
                    category="string",
                    message="考虑使用字符串池或避免频繁的字符串拼接",
                )
            )

        # 内存分配相关
        if "alloc" in name or "申请" in name or "分配" in name:
            hints.append(
                OptimizationHint(
                    level=OptimizationLevel.MEDIUM,
                    category="memory",
                    message="考虑使用对象池或预分配避免频繁的内存分配",
                )
            )

        return hints

    def generate_report(self) -> str:
        """生成分析报告"""
        if not self.hotspots:
            return "未发现性能热点"

        lines = []
        lines.append("")
        lines.append(
            "╔══════════════════════════════════════════════════════════════════════════════════╗"
        )
        lines.append(
            "║                              热点分析报告                                        ║"
        )
        lines.append(
            "╚══════════════════════════════════════════════════════════════════════════════════╝"
        )
        lines.append("")

        lines.append(f"分析阈值: > {self.percentage_threshold}% 执行时间")
        lines.append(f"发现热点: {len(self.hotspots)} 个")
        lines.append("")

        for i, hotspot in enumerate(self.hotspots, 1):
            lines.append(f"{'─' * 80}")
            lines.append(f"#{i} {hotspot.function_name}")
            lines.append(f"   时间占比: {hotspot.percentage:.2f}%")
            lines.append(f"   总时间:   {hotspot.total_time_ms:.2f} ms")
            lines.append(f"   调用次数: {hotspot.call_count:,}")
            lines.append(f"   平均时间: {hotspot.avg_time_ms:.4f} ms")
            lines.append(f"   最大时间: {hotspot.max_time_ns / 1_000_000:.2f} ms")
            lines.append(f"   调用深度: {hotspot.call_depth}")

            if hotspot.hints:
                lines.append("")
                lines.append("   优化建议:")
                for hint in hotspot.hints:
                    level_icon = {
                        OptimizationLevel.CRITICAL: "🔴",
                        OptimizationLevel.HIGH: "🟠",
                        OptimizationLevel.MEDIUM: "🟡",
                        OptimizationLevel.LOW: "🟢",
                    }.get(hint.level, "⚪")
                    lines.append(
                        f"   {level_icon} [{hint.level.value.upper()}] {hint.message}"
                    )

            lines.append("")

        # 总结
        lines.append("─" * 80)
        lines.append("")
        lines.append("【优化优先级】")

        critical = [
            h
            for h in self.hotspots
            if any(x.level == OptimizationLevel.CRITICAL for x in h.hints)
        ]
        high = [
            h
            for h in self.hotspots
            if any(x.level == OptimizationLevel.HIGH for x in h.hints)
        ]

        if critical:
            lines.append(
                f"  🔴 关键优化: {', '.join(h.function_name for h in critical)}"
            )
        if high:
            lines.append(f"  🟠 高优先级: {', '.join(h.function_name for h in high)}")

        lines.append("")
        return "\n".join(lines)

    def get_json_report(self) -> Dict[str, Any]:
        """获取 JSON 格式报告"""
        return {
            "summary": {
                "total_hotspots": len(self.hotspots),
                "total_time_ns": self.total_time_ns,
                "threshold_percent": self.percentage_threshold,
            },
            "hotspots": [h.to_dict() for h in self.hotspots],
        }

    def get_critical_functions(self) -> List[str]:
        """获取关键优化函数列表"""
        return [
            h.function_name
            for h in self.hotspots
            if any(x.level == OptimizationLevel.CRITICAL for x in h.hints)
        ]
