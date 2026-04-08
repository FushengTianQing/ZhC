# -*- coding: utf-8 -*-
"""
ConcurrentCompiler: 并发编译器

提供多线程/多进程并发编译和流水线并行编译支持。
"""

import threading
import queue
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Any, Callable, Optional


class ConcurrentCompiler:
    """并发编译器"""

    def __init__(self, max_workers: Optional[int] = None, use_processes: bool = False):
        """
        初始化并发编译器

        Args:
            max_workers: 最大工作线程/进程数
            use_processes: 是否使用进程（而不是线程）
        """
        self.max_workers = max_workers or multiprocessing.cpu_count()
        self.use_processes = use_processes
        self.executor_class = (
            ProcessPoolExecutor if use_processes else ThreadPoolExecutor
        )

    def compile_files_concurrently(
        self, files: List[Path], compile_func: Callable
    ) -> Dict[Path, Any]:
        """
        并发编译多个文件

        Args:
            files: 文件列表
            compile_func: 编译函数，接受文件路径返回编译结果

        Returns:
            编译结果字典
        """
        results = {}

        with self.executor_class(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_file = {
                executor.submit(compile_func, file): file for file in files
            }

            # 收集结果
            for future in concurrent.futures.as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    results[file] = future.result()
                except Exception as e:
                    results[file] = {"error": str(e)}

        return results

    def pipeline_parallel_compile(self, stages: List[Callable], data: Any) -> Any:
        """
        流水线并行编译

        Args:
            stages: 编译阶段函数列表
            data: 输入数据

        Returns:
            处理后的数据
        """
        if not stages:
            return data

        # 创建阶段队列
        stage_queues: List[Any] = [queue.Queue() for _ in range(len(stages) + 1)]
        stage_queues[0].put(data)

        # 创建线程执行每个阶段
        threads = []
        for i, stage_func in enumerate(stages):

            def stage_worker(stage_idx, input_queue, output_queue, is_last_stage=False):
                while True:
                    try:
                        item = input_queue.get(timeout=1)
                        if item is None:  # 终止信号
                            output_queue.put(None)
                            break

                        result = stage_func(item)
                        output_queue.put(result)
                        if is_last_stage:
                            output_queue.put(None)
                            break
                    except queue.Empty:
                        continue

            is_last = i == len(stages) - 1
            thread = threading.Thread(
                target=stage_worker,
                args=(i, stage_queues[i], stage_queues[i + 1], is_last),
            )
            threads.append(thread)
            thread.start()

        # 等待所有阶段完成
        for thread in threads:
            thread.join()

        # 获取最终结果
        final_result = stage_queues[-1].get()
        return final_result
