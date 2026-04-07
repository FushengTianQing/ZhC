#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增量AST更新测试

测试内容：
1. 树编辑距离计算
2. AST差异计算
3. 增量更新应用
4. 节点哈希
5. 报告生成

基于统一AST体系（parser.ast_nodes）。

作者：远
日期：2026-04-03
更新：2026-04-03 适配统一AST
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from zhpp.parser.ast_nodes import (
    ASTNode, ASTNodeType,
    ProgramNode, FunctionDeclNode, VariableDeclNode, ParamDeclNode,
    PrimitiveTypeNode, BlockStmtNode, ReturnStmtNode,
    BinaryExprNode, IntLiteralNode, IdentifierExprNode,
)
from zhpp.analyzer.incremental_ast_updater import (
    IncrementalASTUpdater,
    TreeEditDistance,
    ASTDiff,
    DiffType,
)


class TestIncrementalAST:
    """增量AST更新测试"""
    
    def create_program(self, var_names: list) -> ProgramNode:
        """创建一个包含多个变量声明的程序节点"""
        declarations = []
        for name in var_names:
            var_type = PrimitiveTypeNode("整数型")
            init = IntLiteralNode(0)
            var_decl = VariableDeclNode(name, var_type, init)
            declarations.append(var_decl)
        return ProgramNode(declarations)
    
    def test_node_hash(self):
        """测试1: 节点哈希"""
        print("=" * 70)
        print("测试1: 节点哈希")
        print("=" * 70)
        
        # 相同结构的节点哈希应不同（因为 node_id 是 UUID）
        int_type1 = PrimitiveTypeNode("整数型")
        int_type2 = PrimitiveTypeNode("整数型")
        
        # PrimitiveTypeNode 重写了 get_hash，只看类型名不看 node_id
        hash1 = int_type1.get_hash()
        hash2 = int_type2.get_hash()
        
        print(f"相同类型: {hash1[:16]}... == {hash2[:16]}... = {hash1 == hash2}")
        assert hash1 == hash2, "相同类型的节点哈希应相等"
        print("✅ 相同类型节点哈希相等")
        
        # 不同类型
        float_type = PrimitiveTypeNode("浮点型")
        hash3 = float_type.get_hash()
        print(f"不同类型: {hash1[:16]}... != {hash3[:16]}... = {hash1 != hash3}")
        assert hash1 != hash3, "不同类型节点哈希应不等"
        print("✅ 不同类型节点哈希不等")
        
        # 不同值
        lit1 = IntLiteralNode(10)
        lit2 = IntLiteralNode(20)
        hash4 = lit1.get_hash()
        hash5 = lit2.get_hash()
        print(f"不同值: {hash4[:16]}... != {hash5[:16]}... = {hash4 != hash5}")
        assert hash4 != hash5, "不同值字面量哈希应不等"
        print("✅ 不同值字面量哈希不等")
        
        print("✅ 测试1通过")
        return True
    
    def test_parent_reference(self):
        """测试2: parent引用"""
        print()
        print("=" * 70)
        print("测试2: parent引用")
        print("=" * 70)
        
        # VariableDeclNode: var_type 和 init 应有 parent
        var_type = PrimitiveTypeNode("整数型")
        init = IntLiteralNode(42)
        var_decl = VariableDeclNode("计数", var_type, init)
        
        assert var_type.parent is var_decl, "var_type.parent 应指向 var_decl"
        assert init.parent is var_decl, "init.parent 应指向 var_decl"
        print(f"var_type.parent is var_decl: True")
        print(f"init.parent is var_decl: True")
        
        # ProgramNode: declarations 应有 parent
        program = ProgramNode([var_decl])
        assert var_decl.parent is program, "var_decl.parent 应指向 program"
        print(f"var_decl.parent is program: True")
        
        # get_path
        path = init.get_path()
        print(f"init.get_path(): {' -> '.join(path)} (长度={len(path)})")
        assert len(path) == 3, f"路径应有3层，实际{len(path)}"
        
        # get_children
        children = var_decl.get_children()
        child_types = [type(c).__name__ for c in children]
        print(f"var_decl.get_children(): {child_types}")
        assert len(children) == 2, f"VariableDeclNode应有2个子节点"
        
        print("✅ 测试2通过")
        return True
    
    def test_tree_edit_distance(self):
        """测试3: 树编辑距离计算"""
        print()
        print("=" * 70)
        print("测试3: 树编辑距离计算")
        print("=" * 70)
        
        calculator = TreeEditDistance()
        
        # 测试: 完全相同的程序
        prog1 = self.create_program(["a", "b"])
        prog2 = self.create_program(["a", "b"])
        
        distance = calculator.compute_distance(prog1, prog2)
        print(f"相同结构: 距离 = {distance}")
        assert distance == 0, f"相同结构的树距离应为0，实际{distance}"
        print("✅ 相同结构距离为0")
        
        # 测试: 空树和单节点树
        distance = calculator.compute_distance(None, prog1)
        print(f"None vs 单程序: 距离 = {distance}")
        assert distance >= 1, "空树vs有内容的树距离应>0"
        print("✅ 空树vs有内容距离>0")
        
        # 测试: 不同内容
        prog3 = self.create_program(["a", "c"])  # b -> c
        distance = calculator.compute_distance(prog1, prog3)
        print(f"b->c 变化: 距离 = {distance}")
        assert distance > 0, "内容变化距离应>0"
        print("✅ 内容变化距离>0")
        
        print("✅ 测试3通过")
        return True
    
    def test_diff_computation(self):
        """测试4: AST差异计算"""
        print()
        print("=" * 70)
        print("测试4: AST差异计算")
        print("=" * 70)
        
        updater = IncrementalASTUpdater()
        
        # 创建旧AST: program(a, b)
        old_ast = self.create_program(["a", "b"])
        
        # 创建新AST: program(a, c)
        new_ast = self.create_program(["a", "c"])
        
        # 计算差异
        diffs = updater.compute_diff(old_ast, new_ast)
        
        print(f"\n检测到 {len(diffs)} 个差异:")
        for diff in diffs:
            if diff.diff_type != DiffType.KEEP:
                print(f"  {diff}")
        
        # 统计
        stats = updater.get_update_statistics(diffs)
        print(f"\n统计: {stats}")
        
        # 验证 - 应该有变化
        total_changes = stats['update'] + stats['insert'] + stats['delete'] + stats['move']
        assert total_changes > 0, "应该检测到差异（a相同，b变c）"
        
        print("✅ 测试4通过")
        return True
    
    def test_incremental_update(self):
        """测试5: 增量更新应用"""
        print()
        print("=" * 70)
        print("测试5: 增量更新应用")
        print("=" * 70)
        
        updater = IncrementalASTUpdater()
        
        # 创建旧AST: program(x, y)
        old_ast = self.create_program(["x", "y"])
        
        # 创建新AST: program(x, y, z) — 多了一个变量
        new_ast = self.create_program(["x", "y", "z"])
        
        # 计算差异
        diffs = updater.compute_diff(old_ast, new_ast)
        
        print(f"应用增量更新前: 差异数={len(diffs)}")
        
        # 应用差异
        updated_ast = updater.apply_diff(old_ast, diffs)
        
        # 检查dirty标记
        is_dirty = updated_ast.get_attribute('_children_modified', False)
        print(f"children_modified标记: {is_dirty}")
        
        # 验证差异确实存在
        stats = updater.get_update_statistics(diffs)
        total = stats['update'] + stats['insert'] + stats['delete'] + stats['move']
        assert total > 0, "应该检测到差异"
        
        # 生成报告
        report = updater.generate_report(diffs)
        print(f"\n差异报告:\n{report}")
        
        print("✅ 测试5通过")
        return True
    
    def test_report_generation(self):
        """测试6: 报告生成"""
        print()
        print("=" * 70)
        print("测试6: 报告生成")
        print("=" * 70)
        
        updater = IncrementalASTUpdater()
        
        # 创建简单的差异
        old_node = PrimitiveTypeNode("整数型")
        new_node = PrimitiveTypeNode("浮点型")
        
        diff = ASTDiff(
            diff_type=DiffType.UPDATE,
            node_id=old_node.node_id,
            old_node=old_node,
            new_node=new_node
        )
        
        diffs = [diff]
        report = updater.generate_report(diffs)
        
        print(report)
        
        assert "更新" in report, "报告应包含'更新'"
        assert "总差异数" in report, "报告应包含统计"
        
        print("✅ 测试6通过")
        return True
    
    def run_all_tests(self):
        """运行所有测试"""
        print()
        print("=" * 70)
        print("增量AST更新测试（统一AST体系）")
        print("=" * 70)
        print()
        
        results = []
        
        results.append(("节点哈希", self.test_node_hash()))
        results.append(("parent引用", self.test_parent_reference()))
        results.append(("树编辑距离", self.test_tree_edit_distance()))
        results.append(("差异计算", self.test_diff_computation()))
        results.append(("增量更新", self.test_incremental_update()))
        results.append(("报告生成", self.test_report_generation()))
        
        # 总结
        print()
        print("=" * 70)
        print("测试总结")
        print("=" * 70)
        
        for test_name, passed in results:
            status = "✅ 通过" if passed else "❌ 失败"
            print(f"{test_name}: {status}")
        
        all_passed = all(r[1] for r in results)
        
        print()
        if all_passed:
            print("🎉 所有测试通过!")
        else:
            print("⚠️ 部分测试失败")
        
        print("=" * 70)
        
        return all_passed


def main():
    """主函数"""
    suite = TestIncrementalAST()
    success = suite.run_all_tests()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
