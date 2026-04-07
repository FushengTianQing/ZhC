#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异步代码生成器 - Async Code Generator

将异步函数转换为 C 代码状态机实现：
1. Future/Promise 状态机结构
2. 异步函数状态机
3. Await 表达式
4. 回调函数

Phase 4 - Stage 2 - Task 11.3 - Day 3

作者：ZHC 开发团队
日期：2026-04-08
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum, auto


# ===== 异步状态机状态 =====

class AsyncState(Enum):
    """异步状态机状态"""
    INITIAL = auto()      # 初始状态
    RUNNING = auto()      # 运行中
    SUSPENDED = auto()    # 挂起（等待）
    COMPLETED = auto()    # 已完成
    FAILED = auto()       # 失败


# ===== 代码生成数据结构 =====

@dataclass
class AsyncFunctionContext:
    """异步函数上下文"""
    function_name: str
    return_type: str
    state_enum_name: str
    state_struct_name: str
    states: List[str] = field(default_factory=list)
    local_variables: List[str] = field(default_factory=list)
    await_points: List[int] = field(default_factory=list)


@dataclass
class GeneratedAsyncCode:
    """生成的异步代码"""
    state_enum: str = ""
    state_struct: str = ""
    state_functions: List[str] = field(default_factory=list)
    future_struct: str = ""
    promise_struct: str = ""
    helper_functions: List[str] = field(default_factory=list)


# ===== 异步代码生成器 =====

class AsyncCodeGenerator:
    """异步代码生成器
    
    将异步函数转换为状态机实现的 C 代码。
    
    使用方式：
        generator = AsyncCodeGenerator()
        code = generator.generate_async_function(async_func_node)
    """
    
    def __init__(self):
        self.contexts: Dict[str, AsyncFunctionContext] = {}
        self.generated_code: Dict[str, GeneratedAsyncCode] = {}
        self._current_context: Optional[AsyncFunctionContext] = None
    
    def generate_async_function(
        self,
        function_name: str,
        return_type: str,
        parameters: List[Dict[str, str]],
        body_statements: List[Any]
    ) -> GeneratedAsyncCode:
        """生成异步函数的 C 代码
        
        Args:
            function_name: 函数名
            return_type: 返回类型
            parameters: 参数列表 [{"name": "x", "type": "int"}, ...]
            body_statements: 函数体语句列表
        
        Returns:
            生成的异步代码
        """
        # 创建上下文
        context = AsyncFunctionContext(
            function_name=function_name,
            return_type=return_type,
            state_enum_name=f"{function_name}_state",
            state_struct_name=f"{function_name}_context"
        )
        
        self._current_context = context
        
        # 分析函数体，识别 await 点
        self._analyze_function_body(body_statements)
        
        # 生成代码
        generated = GeneratedAsyncCode()
        
        # 1. 生成状态枚举
        generated.state_enum = self._generate_state_enum(context)
        
        # 2. 生成状态结构体
        generated.state_struct = self._generate_state_struct(context, parameters)
        
        # 3. 生成状态机函数
        generated.state_functions = self._generate_state_functions(context, body_statements)
        
        # 4. 生成 Future 结构体
        generated.future_struct = self._generate_future_struct(context)
        
        # 5. 生成辅助函数
        generated.helper_functions = self._generate_helper_functions(context)
        
        # 保存生成的代码
        self.generated_code[function_name] = generated
        self.contexts[function_name] = context
        
        return generated
    
    def _analyze_function_body(self, statements: List[Any]):
        """分析函数体，识别 await 点和局部变量"""
        if not self._current_context:
            return
        
        state_counter = 0
        
        # 始终添加初始状态 STATE_0
        state_name = f"STATE_{state_counter}"
        self._current_context.states.append(state_name)
        state_counter += 1
        
        for stmt in statements:
            # 添加状态
            state_name = f"STATE_{state_counter}"
            self._current_context.states.append(state_name)
            
            # 检查是否是 await 语句
            if self._is_await_statement(stmt):
                self._current_context.await_points.append(state_counter)
            
            state_counter += 1
        
        # 添加最终状态
        self._current_context.states.append("STATE_COMPLETED")
    
    def _is_await_statement(self, stmt: Any) -> bool:
        """检查是否是 await 语句"""
        # 简化实现：检查语句类型
        return hasattr(stmt, 'is_await') and stmt.is_await
    
    def _generate_state_enum(self, context: AsyncFunctionContext) -> str:
        """生成状态枚举"""
        lines = [
            f"// 异步函数 {context.function_name} 的状态枚举",
            f"typedef enum {{"
        ]
        
        for state in context.states:
            lines.append(f"    {state},")
        
        lines.append(f"}} {context.state_enum_name};")
        lines.append("")
        
        return "\n".join(lines)
    
    def _generate_state_struct(
        self,
        context: AsyncFunctionContext,
        parameters: List[Dict[str, str]]
    ) -> str:
        """生成状态结构体"""
        lines = [
            f"// 异步函数 {context.function_name} 的上下文结构体",
            f"typedef struct {{"
        ]
        
        # 当前状态
        lines.append(f"    {context.state_enum_name} current_state;")
        
        # 参数
        for param in parameters:
            lines.append(f"    {param['type']} {param['name']};")
        
        # 局部变量
        for var in context.local_variables:
            lines.append(f"    {var};")
        
        # 返回值
        lines.append(f"    {context.return_type} result;")
        
        # Future 指针
        lines.append(f"    void* future;")
        
        lines.append(f"}} {context.state_struct_name};")
        lines.append("")
        
        return "\n".join(lines)
    
    def _generate_state_functions(
        self,
        context: AsyncFunctionContext,
        statements: List[Any]
    ) -> List[str]:
        """生成状态机函数"""
        functions = []
        
        # 生成状态机主函数
        main_func = self._generate_state_machine_function(context, statements)
        functions.append(main_func)
        
        # 生成初始化函数
        init_func = self._generate_init_function(context)
        functions.append(init_func)
        
        # 生成取消函数
        cancel_func = self._generate_cancel_function(context)
        functions.append(cancel_func)
        
        return functions
    
    def _generate_state_machine_function(
        self,
        context: AsyncFunctionContext,
        statements: List[Any]
    ) -> str:
        """生成状态机主函数"""
        lines = [
            f"// 状态机主函数",
            f"void {context.function_name}_resume({context.state_struct_name}* ctx) {{",
            f"    switch (ctx->current_state) {{"
        ]
        
        # 为每个状态生成 case
        for i, state in enumerate(context.states):
            lines.append(f"        case {state}:")
            lines.append(f"            // 状态 {i} 的代码")
            
            # 检查是否是 await 点
            if i in context.await_points:
                lines.append(f"            // Await 点：挂起执行")
                lines.append(f"            ctx->current_state = {context.states[i+1]};")
                lines.append(f"            return;  // 挂起")
            elif i == len(context.states) - 1:
                # 最终状态
                lines.append(f"            ctx->current_state = {state};")
                lines.append(f"            // 标记 Future 为完成")
                lines.append(f"            return;")
            else:
                lines.append(f"            ctx->current_state = {context.states[i+1]};")
            
            lines.append(f"            break;")
        
        lines.append(f"    }}")
        lines.append(f"}}")
        lines.append("")
        
        return "\n".join(lines)
    
    def _generate_init_function(self, context: AsyncFunctionContext) -> str:
        """生成初始化函数"""
        lines = [
            f"// 初始化异步函数上下文",
            f"{context.state_struct_name}* {context.function_name}_create(",
        ]
        
        # 参数列表
        # 简化实现
        lines.append(f") {{")
        lines.append(f"    {context.state_struct_name}* ctx = malloc(sizeof({context.state_struct_name}));")
        lines.append(f"    ctx->current_state = {context.states[0]};")
        lines.append(f"    return ctx;")
        lines.append(f"}}")
        lines.append("")
        
        return "\n".join(lines)
    
    def _generate_cancel_function(self, context: AsyncFunctionContext) -> str:
        """生成取消函数"""
        lines = [
            f"// 取消异步函数执行",
            f"void {context.function_name}_cancel({context.state_struct_name}* ctx) {{",
            f"    if (ctx) {{",
            f"        ctx->current_state = STATE_COMPLETED;",
            f"        free(ctx);",
            f"    }}",
            f"}}",
        ]
        lines.append("")
        
        return "\n".join(lines)
    
    def _generate_future_struct(self, context: AsyncFunctionContext) -> str:
        """生成 Future 结构体"""
        lines = [
            f"// Future 结构体",
            f"typedef struct {{",
            f"    {context.state_enum_name} state;",
            f"    {context.return_type} value;",
            f"    void (*callback)(void*);",
            f"    void* callback_data;",
            f"}} {context.function_name}_future;",
            f"",
        ]
        
        return "\n".join(lines)
    
    def _generate_helper_functions(self, context: AsyncFunctionContext) -> List[str]:
        """生成辅助函数"""
        functions = []
        
        # 生成 Future 创建函数
        create_future = [
            f"// 创建 Future",
            f"{context.function_name}_future* {context.function_name}_future_create() {{",
            f"    {context.function_name}_future* future = malloc(sizeof({context.function_name}_future));",
            f"    future->state = INITIAL;",
            f"    future->callback = NULL;",
            f"    future->callback_data = NULL;",
            f"    return future;",
            f"}}",
            f""
        ]
        functions.append("\n".join(create_future))
        
        # 生成 Future 完成函数
        complete_future = [
            f"// 完成 Future",
            f"void {context.function_name}_future_complete(",
            f"    {context.function_name}_future* future,",
            f"    {context.return_type} value",
            f") {{",
            f"    future->state = COMPLETED;",
            f"    future->value = value;",
            f"    if (future->callback) {{",
            f"        future->callback(future->callback_data);",
            f"    }}",
            f"}}",
            f""
        ]
        functions.append("\n".join(complete_future))
        
        # 生成 Await 函数
        await_func = [
            f"// Await 函数",
            f"{context.return_type} {context.function_name}_await(",
            f"    {context.function_name}_future* future",
            f") {{",
            f"    while (future->state != COMPLETED) {{",
            f"        // 等待 Future 完成",
            f"        // 在实际实现中，这里会挂起当前协程",
            f"    }}",
            f"    return future->value;",
            f"}}",
            f""
        ]
        functions.append("\n".join(await_func))
        
        return functions
    
    def generate_runtime_support(self) -> str:
        """生成运行时支持代码
        
        Returns:
            运行时支持代码（状态机框架、调度器等）
        """
        lines = [
            "// ===== 异步运行时支持 =====",
            "",
            "// 异步状态枚举",
            "typedef enum {",
            "    ASYNC_STATE_INITIAL,",
            "    ASYNC_STATE_RUNNING,",
            "    ASYNC_STATE_SUSPENDED,",
            "    ASYNC_STATE_COMPLETED,",
            "    ASYNC_STATE_FAILED",
            "} AsyncState;",
            "",
            "// Future 基类",
            "typedef struct {",
            "    AsyncState state;",
            "    void (*callback)(void*);",
            "    void* callback_data;",
            "} Future;",
            "",
            "// Promise 基类",
            "typedef struct {",
            "    Future* future;",
            "    void (*resolve)(void*, void*);",
            "    void (*reject)(void*, int);",
            "} Promise;",
            "",
            "// 调度器结构",
            "typedef struct {",
            "    void** ready_queue;",
            "    int queue_size;",
            "    int queue_capacity;",
            "} AsyncScheduler;",
            "",
            "// 调度器函数",
            "void async_scheduler_init(AsyncScheduler* scheduler) {",
            "    scheduler->queue_size = 0;",
            "    scheduler->queue_capacity = 16;",
            "    scheduler->ready_queue = malloc(sizeof(void*) * scheduler->queue_capacity);",
            "}",
            "",
            "void async_scheduler_run(AsyncScheduler* scheduler) {",
            "    while (scheduler->queue_size > 0) {",
            "        void* task = scheduler->ready_queue[--scheduler->queue_size];",
            "        // 执行任务",
            "    }",
            "}",
            "",
        ]
        
        return "\n".join(lines)
    
    def get_generated_code(self, function_name: str) -> Optional[GeneratedAsyncCode]:
        """获取已生成的代码
        
        Args:
            function_name: 函数名
        
        Returns:
            生成的代码，如果不存在则返回 None
        """
        return self.generated_code.get(function_name)


# ===== 便捷函数 =====

def generate_async_code(
    function_name: str,
    return_type: str,
    parameters: List[Dict[str, str]],
    body_statements: List[Any]
) -> GeneratedAsyncCode:
    """生成异步代码的便捷函数
    
    Args:
        function_name: 函数名
        return_type: 返回类型
        parameters: 参数列表
        body_statements: 函数体语句
    
    Returns:
        生成的异步代码
    """
    generator = AsyncCodeGenerator()
    return generator.generate_async_function(
        function_name,
        return_type,
        parameters,
        body_statements
    )


# ===== 示例用法 =====

if __name__ == "__main__":
    print("=" * 70)
    print("异步代码生成器测试")
    print("=" * 70)
    
    # 创建生成器
    generator = AsyncCodeGenerator()
    
    # 生成异步函数
    code = generator.generate_async_function(
        function_name="fetch_data",
        return_type="char*",
        parameters=[
            {"name": "url", "type": "char*"}
        ],
        body_statements=[]
    )
    
    # 打印生成的代码
    print("\n状态枚举:")
    print(code.state_enum)
    
    print("\n状态结构体:")
    print(code.state_struct)
    
    print("\nFuture 结构体:")
    print(code.future_struct)
    
    print("\n状态机函数:")
    for func in code.state_functions:
        print(func)
    
    print("\n辅助函数:")
    for func in code.helper_functions:
        print(func)
    
    print("\n运行时支持:")
    print(generator.generate_runtime_support())
