#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
C代码生成器 - 将 AST 转换为 C 代码

基于 ASTVisitor 模式，遍历 AST 生成等价的 C 代码。
Phase 4 核心组件。

作者: 阿福
日期: 2026-04-03
"""

from typing import Optional

from zhc.parser.ast_nodes import (
    ASTNode, ASTVisitor, ASTNodeType,
    ProgramNode, ModuleDeclNode, ImportDeclNode,
    FunctionDeclNode, StructDeclNode, EnumDeclNode, UnionDeclNode,
    TypedefDeclNode, VariableDeclNode, ParamDeclNode,
    BlockStmtNode, IfStmtNode, WhileStmtNode, ForStmtNode,
    DoWhileStmtNode, SwitchStmtNode, CaseStmtNode, DefaultStmtNode,
    BreakStmtNode, ContinueStmtNode, ReturnStmtNode, ExprStmtNode,
    GotoStmtNode, LabelStmtNode,
    BinaryExprNode, UnaryExprNode, AssignExprNode, CallExprNode,
    MemberExprNode, ArrayExprNode, IdentifierExprNode,
    IntLiteralNode, FloatLiteralNode, StringLiteralNode, CharLiteralNode,
    BoolLiteralNode, NullLiteralNode,
    TernaryExprNode, SizeofExprNode, CastExprNode,
    ArrayInitNode, StructInitNode,
    PrimitiveTypeNode, PointerTypeNode, ArrayTypeNode,
    FunctionTypeNode, StructTypeNode,
)

# 映射表从 ir/mappings.py 导入（Phase 7 M3.0）
from zhc.ir.mappings import (
    TYPE_MAP,
    MODIFIER_MAP,
    FUNCTION_NAME_MAP,
    INCLUDE_MAP,
    STDLIB_FUNC_MAP,
    resolve_type,
    resolve_function_name,
)

class CCodeGenerator(ASTVisitor):
    """AST -> C 代码生成器

    遍历 AST，将中文 C 语法转换为标准 C 代码。

    使用方式：
        generator = CCodeGenerator()
        c_code = generator.generate(ast)
    """

    def __init__(self, indent_str: str = "    "):
        self.indent = 0
        self.indent_str = indent_str
        self.output_lines: list = []
        self._expr_buffer: list = []  # 用于表达式求值
        
        # 泛型代码生成器
        self._generic_generator = None

    def generate(self, ast: ProgramNode) -> str:
        """生成完整的 C 代码

        Args:
            ast: 程序AST根节点

        Returns:
            生成的 C 代码字符串
        """
        self.output_lines = []
        self.indent = 0
        ast.accept(self)
        
        # 生成泛型实例化代码
        if self._generic_generator:
            generic_code = self._generate_generic_code()
            if generic_code:
                # 在输出开头插入泛型定义
                self.output_lines.insert(0, generic_code)
        
        return "\n".join(self.output_lines)
    
    def set_generic_generator(self, generator):
        """设置泛型代码生成器
        
        Args:
            generator: GenericCodeGenerator 实例
        """
        self._generic_generator = generator
    
    def _generate_generic_code(self) -> str:
        """生成泛型实例化代码
        
        Returns:
            泛型代码字符串
        """
        if not self._generic_generator:
            return ""
        
        lines = [
            "/* ==================== 泛型实例化代码 ==================== */",
            ""
        ]
        
        # 生成类型定义
        for gen_type in self._generic_generator.get_generated_types():
            lines.append(f"/* 类型: {gen_type.original_generic}<{', '.join(gen_type.type_args)}> */")
            lines.append(gen_type.code)
            lines.append("")
        
        # 生成函数定义
        for gen_func in self._generic_generator.get_generated_functions():
            lines.append(f"/* 函数: {gen_func.original_generic}<{', '.join(gen_func.type_args)}> */")
            lines.append(gen_func.code)
            lines.append("")
        
        lines.append("/* ==================== 泛型实例化代码结束 ==================== */")
        lines.append("")
        
        return "\n".join(lines)

    def _emit(self, line: str = ""):
        """输出一行代码（带缩进）"""
        self.output_lines.append(self.indent_str * self.indent + line)

    def _emit_type(self, type_node: ASTNode) -> str:
        """将类型节点转换为 C 类型字符串

        Args:
            type_node: 类型节点

        Returns:
            C 类型字符串（如 "int", "int*", "char[]"）
        """
        if isinstance(type_node, PrimitiveTypeNode):
            return self._resolve_type_name(type_node.name)
        elif isinstance(type_node, PointerTypeNode):
            # 函数指针: PointerTypeNode(FunctionTypeNode) 已包含 (*)
            if isinstance(type_node.base_type, FunctionTypeNode):
                return self._emit_type(type_node.base_type)
            base = self._emit_type(type_node.base_type)
            return base + "*"
        elif isinstance(type_node, ArrayTypeNode):
            elem = self._emit_type(type_node.element_type)
            if type_node.size is not None:
                size_str = self._expr_to_string(type_node.size)
                return f"{elem}[{size_str}]"
            return f"{elem}[]"
        elif isinstance(type_node, StructTypeNode):
            return f"struct {type_node.name}"
        elif isinstance(type_node, FunctionTypeNode):
            ret = self._emit_type(type_node.return_type)
            params = ", ".join(self._emit_type(p) for p in type_node.param_types)
            return f"{ret} (*)({params})"
        else:
            # 回退：尝试作为表达式求值
            return self._expr_to_string(type_node)

    def _resolve_type_name(self, name: str) -> str:
        """解析中文类型名为 C 类型名"""
        return TYPE_MAP.get(name, name)

    def _resolve_function_name(self, name: str) -> str:
        """解析中文函数名为 C 函数名"""
        return FUNCTION_NAME_MAP.get(name, STDLIB_FUNC_MAP.get(name, name))

    def _expr_to_string(self, node: Optional[ASTNode]) -> str:
        """将表达式节点转换为 C 表达式字符串（不 emit 行）

        使用临时缓冲区收集输出，返回拼接后的字符串。
        """
        if node is None:
            return ""

        old_lines = self.output_lines
        self.output_lines = []
        node.accept(self)
        result = " ".join(self.output_lines).strip()
        self.output_lines = old_lines
        return result

    # ========== 程序结构 ==========

    def visit_program(self, node: ProgramNode):
        for decl in node.declarations:
            decl.accept(self)
            self._emit("")  # 声明之间空行

    def visit_module_decl(self, node: ModuleDeclNode):
        # 模块声明 -> #include 指令
        include = INCLUDE_MAP.get(node.name)
        if include:
            self._emit(include)
        else:
            self._emit(f"// 模块: {node.name}")
        # 导入声明
        for imp in node.imports:
            inc = INCLUDE_MAP.get(imp)
            if inc:
                self._emit(inc)
            else:
                self._emit(f"#include \"{imp}.h\"")
        # 导出
        for exp in node.exports:
            self._emit(f"// 公开: {exp}")
        # 主体
        for item in node.body:
            item.accept(self)

    def visit_import_decl(self, node: ImportDeclNode):
        if node.symbols:
            # 具体符号导入（C没有模块系统，生成注释）
            self._emit(f"// 导入 {node.module_name}: {', '.join(node.symbols)}")
        else:
            include = INCLUDE_MAP.get(node.module_name)
            if include:
                self._emit(include)
            else:
                self._emit(f"#include \"{node.module_name}.h\"")

    # ========== 声明 ==========

    def visit_function_decl(self, node: FunctionDeclNode):
        name = self._resolve_function_name(node.name)
        ret_type = self._emit_type(node.return_type)

        # 参数列表
        if not node.params:
            params_str = "void"
        else:
            parts = []
            for p in node.params:
                # 函数指针参数: ret (*name)(params)
                if isinstance(p.param_type, PointerTypeNode) and isinstance(p.param_type.base_type, FunctionTypeNode):
                    func_type = p.param_type.base_type
                    ret_str = self._emit_type(func_type.return_type)
                    fp_params = ", ".join(self._emit_type(pt) for pt in func_type.param_types)
                    parts.append(f"{ret_str} (*{p.name})({fp_params})")
                else:
                    parts.append(self._emit_type(p.param_type) + " " + p.name)
            params_str = ", ".join(parts)

        # 函数签名
        self._emit(f"{ret_type} {name}({params_str}) {{")

        # 函数体
        if node.body:
            self.indent += 1
            node.body.accept(self)
            self.indent -= 1

        self._emit("}")

    def visit_struct_decl(self, node: StructDeclNode):
        self._emit(f"struct {node.name} {{")
        self.indent += 1
        for member in node.members:
            member.accept(self)
        self.indent -= 1
        self._emit("};")

    def visit_variable_decl(self, node: VariableDeclNode):
        const_str = "const " if node.is_const else ""

        if isinstance(node.var_type, ArrayTypeNode):
            # 数组: type name[size] = init;
            elem_type = self._emit_type(node.var_type.element_type)
            name_str = node.name
            if node.var_type.size:
                size_str = self._expr_to_string(node.var_type.size)
                name_str += f"[{size_str}]"
            if node.init:
                init_str = self._expr_to_string(node.init)
                self._emit(f"{const_str}{elem_type} {name_str} = {init_str};")
            else:
                self._emit(f"{const_str}{elem_type} {name_str};")
        elif isinstance(node.var_type, PointerTypeNode) and isinstance(node.var_type.base_type, FunctionTypeNode):
            # 函数指针: ret (*name)(params);
            func_type = node.var_type.base_type
            ret_str = self._emit_type(func_type.return_type)
            params = ", ".join(self._emit_type(p) for p in func_type.param_types)
            if node.init:
                init_str = self._expr_to_string(node.init)
                self._emit(f"{const_str}{ret_str} (*{node.name})({params}) = {init_str};")
            else:
                self._emit(f"{const_str}{ret_str} (*{node.name})({params});")
        else:
            type_str = self._emit_type(node.var_type)
            if node.init:
                init_str = self._expr_to_string(node.init)
                self._emit(f"{const_str}{type_str} {node.name} = {init_str};")
            else:
                self._emit(f"{const_str}{type_str} {node.name};")

    def visit_param_decl(self, node: ParamDeclNode):
        # 函数指针参数: ret (*name)(params)
        if isinstance(node.param_type, PointerTypeNode) and isinstance(node.param_type.base_type, FunctionTypeNode):
            func_type = node.param_type.base_type
            ret_str = self._emit_type(func_type.return_type)
            params = ", ".join(self._emit_type(p) for p in func_type.param_types)
            self._emit(f"{ret_str} (*{node.name})({params})")
        else:
            # 参数声明通常在 visit_function_decl 中内联处理
            # 这里作为独立声明处理（用于调试或其他场景）
            type_str = self._emit_type(node.param_type)
            if node.default_value:
                default_str = self._expr_to_string(node.default_value)
                self._emit(f"{type_str} {node.name} = {default_str}")
            else:
                self._emit(f"{type_str} {node.name}")

    def visit_enum_decl(self, node: EnumDeclNode):
        if node.name:
            self._emit(f"enum {node.name} {{")
        else:
            self._emit("enum {")

        self.indent += 1
        for i, (name, value) in enumerate(node.values):
            if value is not None:
                val_str = self._expr_to_string(value)
                comma = "," if i < len(node.values) - 1 else ","
                self._emit(f"{name} = {val_str}{comma}")
            else:
                comma = "," if i < len(node.values) - 1 else ","
                self._emit(f"{name}{comma}")
        self.indent -= 1
        self._emit("};")

    def visit_union_decl(self, node: UnionDeclNode):
        self._emit(f"union {node.name} {{")
        self.indent += 1
        for member in node.members:
            member.accept(self)
        self.indent -= 1
        self._emit("};")

    def visit_typedef_decl(self, node: TypedefDeclNode):
        type_str = self._emit_type(node.old_type)
        self._emit(f"typedef {type_str} {node.new_name};")

    # ========== 语句 ==========

    def visit_block_stmt(self, node: BlockStmtNode):
        for stmt in node.statements:
            stmt.accept(self)

    def visit_if_stmt(self, node: IfStmtNode):
        cond_str = self._expr_to_string(node.condition)
        # 如果条件已经有括号包裹，不重复
        if cond_str.startswith("(") and cond_str.endswith(")"):
            self._emit(f"if {cond_str} {{")
        else:
            self._emit(f"if ({cond_str}) {{")

        self.indent += 1
        node.then_branch.accept(self)
        self.indent -= 1

        if node.else_branch:
            if isinstance(node.else_branch, IfStmtNode):
                # else if 链
                else_cond = self._expr_to_string(node.else_branch.condition)
                self._emit(f"}} else if ({else_cond}) {{")
                self.indent += 1
                node.else_branch.then_branch.accept(self)
                self.indent -= 1
                # 处理后续的 else if
                if node.else_branch.else_branch:
                    if isinstance(node.else_branch.else_branch, IfStmtNode):
                        # 递归处理 else if 链
                        self._handle_else_if_chain(node.else_branch.else_branch)
                    else:
                        self._emit("} else {")
                        self.indent += 1
                        node.else_branch.else_branch.accept(self)
                        self.indent -= 1
                        self._emit("}")
            else:
                self._emit("} else {")
                self.indent += 1
                node.else_branch.accept(self)
                self.indent -= 1
                self._emit("}")
        else:
            self._emit("}")

    def _handle_else_if_chain(self, node: IfStmtNode):
        """处理 else if 链"""
        cond_str = self._expr_to_string(node.condition)
        self._emit(f"}} else if ({cond_str}) {{")
        self.indent += 1
        node.then_branch.accept(self)
        self.indent -= 1

        if node.else_branch:
            if isinstance(node.else_branch, IfStmtNode):
                self._handle_else_if_chain(node.else_branch)
            else:
                self._emit("} else {")
                self.indent += 1
                node.else_branch.accept(self)
                self.indent -= 1
                self._emit("}")
        else:
            self._emit("}")

    def visit_while_stmt(self, node: WhileStmtNode):
        cond_str = self._expr_to_string(node.condition)
        if cond_str.startswith("(") and cond_str.endswith(")"):
            self._emit(f"while {cond_str} {{")
        else:
            self._emit(f"while ({cond_str}) {{")
        self.indent += 1
        node.body.accept(self)
        self.indent -= 1
        self._emit("}")

    def visit_for_stmt(self, node: ForStmtNode):
        init_str = self._expr_to_string(node.init) if node.init else ""
        cond_str = self._expr_to_string(node.condition) if node.condition else ""
        update_str = self._expr_to_string(node.update) if node.update else ""

        # 如果 init 是变量声明，需要特殊处理（去掉末尾分号）
        if init_str.endswith(";"):
            init_str = init_str[:-1]

        self._emit(f"for ({init_str}; {cond_str}; {update_str}) {{")
        self.indent += 1
        node.body.accept(self)
        self.indent -= 1
        self._emit("}")

    def visit_do_while_stmt(self, node: DoWhileStmtNode):
        self._emit("do {")
        self.indent += 1
        node.body.accept(self)
        self.indent -= 1
        cond_str = self._expr_to_string(node.condition)
        self._emit(f"}} while ({cond_str});")

    def visit_switch_stmt(self, node: SwitchStmtNode):
        expr_str = self._expr_to_string(node.expr)
        self._emit(f"switch ({expr_str}) {{")
        self.indent += 1
        for case in node.cases:
            case.accept(self)
        self.indent -= 1
        self._emit("}")

    def visit_case_stmt(self, node: CaseStmtNode):
        if node.value is not None:
            val_str = self._expr_to_string(node.value)
            self._emit(f"case {val_str}:")
        # 如果 value 是 None 且是 CaseStmtNode，由 DefaultStmtNode 处理
        self.indent += 1
        for stmt in node.statements:
            stmt.accept(self)
        self.indent -= 1

    def visit_default_stmt(self, node: DefaultStmtNode):
        self._emit("default:")
        self.indent += 1
        for stmt in node.statements:
            stmt.accept(self)
        self.indent -= 1

    def visit_break_stmt(self, node: BreakStmtNode):
        self._emit("break;")

    def visit_continue_stmt(self, node: ContinueStmtNode):
        self._emit("continue;")

    def visit_return_stmt(self, node: ReturnStmtNode):
        if node.value:
            val_str = self._expr_to_string(node.value)
            self._emit(f"return {val_str};")
        else:
            self._emit("return;")

    def visit_expr_stmt(self, node: ExprStmtNode):
        expr_str = self._expr_to_string(node.expr)
        self._emit(f"{expr_str};")

    def visit_goto_stmt(self, node: GotoStmtNode):
        self._emit(f"goto {node.label};")

    def visit_label_stmt(self, node: LabelStmtNode):
        self._emit(f"{node.name}:")
        if node.statement:
            node.statement.accept(self)

    # ========== 表达式 ==========

    def visit_binary_expr(self, node: BinaryExprNode):
        left_str = self._expr_to_string(node.left)
        right_str = self._expr_to_string(node.right)
        self._emit(f"({left_str} {node.operator} {right_str})")

    def visit_unary_expr(self, node: UnaryExprNode):
        operand_str = self._expr_to_string(node.operand)
        if node.is_prefix:
            self._emit(f"{node.operator}{operand_str}")
        else:
            self._emit(f"{operand_str}{node.operator}")

    def visit_assign_expr(self, node: AssignExprNode):
        target_str = self._expr_to_string(node.target)
        value_str = self._expr_to_string(node.value)
        self._emit(f"{target_str} {node.operator} {value_str}")

    def visit_call_expr(self, node: CallExprNode):
        # 函数名
        if isinstance(node.callee, IdentifierExprNode):
            callee_str = self._resolve_function_name(node.callee.name)
        else:
            callee_str = self._expr_to_string(node.callee)

        # 参数
        args = [self._expr_to_string(arg) for arg in node.args]
        self._emit(f"{callee_str}({', '.join(args)})")

    def visit_member_expr(self, node: MemberExprNode):
        obj_str = self._expr_to_string(node.obj)
        self._emit(f"{obj_str}.{node.member}")

    def visit_array_expr(self, node: ArrayExprNode):
        array_str = self._expr_to_string(node.array)
        index_str = self._expr_to_string(node.index)
        self._emit(f"{array_str}[{index_str}]")

    def visit_identifier_expr(self, node: IdentifierExprNode):
        self._emit(node.name)

    def visit_int_literal(self, node: IntLiteralNode):
        self._emit(str(node.value))

    def visit_float_literal(self, node: FloatLiteralNode):
        self._emit(str(node.value))

    def visit_string_literal(self, node: StringLiteralNode):
        # 需要正确转义 C 字符串
        escaped = node.value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")
        self._emit(f'"{escaped}"')

    def visit_char_literal(self, node: CharLiteralNode):
        # 字符字面量
        escaped = node.value
        if len(node.value) == 1:
            escaped = node.value.replace("\\", "\\\\").replace("'", "\\'")
        self._emit(f"'{escaped}'")

    def visit_bool_literal(self, node: BoolLiteralNode):
        self._emit("1" if node.value else "0")

    def visit_null_literal(self, node: NullLiteralNode):
        self._emit("NULL")

    def visit_ternary_expr(self, node: TernaryExprNode):
        cond_str = self._expr_to_string(node.condition)
        then_str = self._expr_to_string(node.then_expr)
        else_str = self._expr_to_string(node.else_expr)
        self._emit(f"({cond_str} ? {then_str} : {else_str})")

    def visit_sizeof_expr(self, node: SizeofExprNode):
        target_str = self._expr_to_string(node.target)
        self._emit(f"sizeof({target_str})")

    def visit_cast_expr(self, node: CastExprNode):
        type_str = self._emit_type(node.cast_type)
        expr_str = self._expr_to_string(node.expr)
        self._emit(f"({type_str}){expr_str}")

    def visit_array_init(self, node: ArrayInitNode):
        elements = [self._expr_to_string(elem) for elem in node.elements]
        self._emit(f"{{{', '.join(elements)}}}")

    def visit_struct_init(self, node: StructInitNode):
        if node.field_names:
            parts = []
            for name, val in zip(node.field_names, node.values):
                val_str = self._expr_to_string(val)
                parts.append(f".{name} = {val_str}")
            self._emit(f"{{{', '.join(parts)}}}")
        else:
            values = [self._expr_to_string(val) for val in node.values]
            self._emit(f"{{{', '.join(values)}}}")

    # ========== 类型 ==========

    def visit_primitive_type(self, node: PrimitiveTypeNode):
        self._emit(self._resolve_type_name(node.name))

    def visit_pointer_type(self, node: PointerTypeNode):
        base_str = self._expr_to_string(node.base_type)
        self._emit(f"{base_str}*")

    def visit_array_type(self, node: ArrayTypeNode):
        elem_str = self._expr_to_string(node.element_type)
        if node.size:
            size_str = self._expr_to_string(node.size)
            self._emit(f"{elem_str}[{size_str}]")
        else:
            self._emit(f"{elem_str}[]")

    def visit_function_type(self, node: FunctionTypeNode):
        ret_str = self._expr_to_string(node.return_type)
        params = [self._expr_to_string(p) for p in node.param_types]
        self._emit(f"{ret_str} (*)({', '.join(params)})")

    def visit_struct_type(self, node: StructTypeNode):
        self._emit(f"struct {node.name}")
