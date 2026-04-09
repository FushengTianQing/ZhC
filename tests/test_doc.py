"""文档生成模块测试。"""

import json

import pytest

from zhc.doc.comment_parser import parse_comment
from zhc.doc.models import (
    DocEnum,
    DocEnumMember,
    DocField,
    DocFunction,
    DocModule,
    DocParameter,
    DocProject,
    DocReturn,
    DocStructure,
)
from zhc.doc.formatter import (
    HtmlFormatter,
    JsonFormatter,
    MarkdownFormatter,
    TextFormatter,
    get_formatter,
)
from zhc.doc.api_generator import APIGenerator, generate_api_docs


class TestCommentParser:
    """注释解析器测试。"""

    def test_parse_simple_comment(self):
        """测试解析简单注释。"""
        comment = parse_comment("""
        这是一个简单的注释
        """)
        assert comment.description == "这是一个简单的注释"

    def test_parse_param_tags(self):
        """测试解析 @param 标签。"""
        comment = parse_comment("""
        /**
         * 计算两个数的和
         *
         * @param a 第一个数
         * @param b 第二个数
         */
        """)
        assert "计算两个数的和" in comment.description
        assert comment.get_param("a") == "第一个数"
        assert comment.get_param("b") == "第二个数"

    def test_parse_return_tag(self):
        """测试解析 @return 标签。"""
        comment = parse_comment("""
        /**
         * 获取用户信息
         *
         * @return 用户对象
         */
        """)
        assert comment.get_return() == "用户对象"

    def test_parse_example_tag(self):
        """测试解析 @示例 标签。"""
        comment = parse_comment("""
        /**
         * 示例函数
         *
         * @示例
         * 整数型 结果 = 加(1, 2);
         */
        """)
        assert len(comment.examples) > 0
        assert "加(1, 2)" in comment.examples[0]

    def test_parse_note_tag(self):
        """测试解析 @注意 标签。"""
        comment = parse_comment("""
        /**
         * 安全函数
         *
         * @注意 线程安全
         */
        """)
        assert len(comment.notes) > 0
        assert "线程安全" in comment.notes[0]

    def test_parse_multiple_tags(self):
        """测试解析多个标签。"""
        comment = parse_comment("""
        /**
         * 完整示例
         *
         * @param x 输入值
         * @return 输出值
         * @示例 加(1, 2)
         * @注意 可能溢出
         * @参见 减函数
         * @author 张三
         * @版本 1.0
         */
        """)
        assert comment.get_param("x") == "输入值"
        assert comment.get_return() == "输出值"
        assert len(comment.examples) > 0
        assert len(comment.notes) > 0
        assert comment.get_author() == "张三"
        assert comment.get_version() == "1.0"

    def test_doc_comment_to_dict(self):
        """测试 DocComment 转字典。"""
        comment = parse_comment("""
        /**
         * 测试函数
         *
         * @param a 参数
         */
        """)
        d = comment.to_dict()
        assert "description" in d
        assert "tags" in d
        assert isinstance(d["tags"], list)


class TestDocModels:
    """文档数据模型测试。"""

    def test_doc_function(self):
        """测试 DocFunction。"""
        func = DocFunction(
            name="add",
            description="加法函数",
            parameters=[
                DocParameter(name="a", type="整数型", description="第一个数"),
                DocParameter(name="b", type="整数型", description="第二个数"),
            ],
            returns=DocReturn(type="整数型", description="和"),
        )
        assert func.name == "add"
        assert len(func.parameters) == 2
        assert func.returns.type == "整数型"

    def test_doc_structure(self):
        """测试 DocStructure。"""
        struct = DocStructure(
            name="Point",
            description="坐标点",
            fields=[
                DocField(name="x", type="浮点型", description="X坐标"),
                DocField(name="y", type="浮点型", description="Y坐标"),
            ],
        )
        assert struct.name == "Point"
        assert len(struct.fields) == 2

    def test_doc_enum(self):
        """测试 DocEnum。"""
        enum = DocEnum(
            name="Color",
            description="颜色枚举",
            members=[
                DocEnumMember(name="RED", value="0", description="红色"),
                DocEnumMember(name="GREEN", value="1", description="绿色"),
            ],
        )
        assert enum.name == "Color"
        assert len(enum.members) == 2

    def test_doc_module(self):
        """测试 DocModule。"""
        module = DocModule(
            name="math",
            description="数学模块",
            functions=[
                DocFunction(name="add", description="加法"),
                DocFunction(name="sub", description="减法"),
            ],
        )
        assert module.name == "math"
        assert len(module.functions) == 2
        assert module.get_function("add") is not None

    def test_doc_project(self):
        """测试 DocProject。"""
        project = DocProject(
            name="TestProject",
            version="1.0.0",
            description="测试项目",
        )
        assert project.name == "TestProject"
        assert project.version == "1.0.0"

    def test_to_dict(self):
        """测试 to_dict 方法。"""
        func = DocFunction(name="test", description="测试函数")
        d = func.to_dict()
        assert d["name"] == "test"
        assert d["kind"] == "function"


class TestFormatters:
    """格式化器测试。"""

    def test_text_formatter(self):
        """测试文本格式化器。"""
        formatter = TextFormatter()
        module = DocModule(
            name="test",
            description="测试模块",
            functions=[DocFunction(name="add", description="加法")],
        )
        result = formatter.format_module(module)
        assert "test" in result
        assert "加法" in result

    def test_markdown_formatter(self):
        """测试 Markdown 格式化器。"""
        formatter = MarkdownFormatter()
        func = DocFunction(
            name="add",
            description="加法函数",
            parameters=[
                DocParameter(name="a", type="整数型", description="第一个数"),
            ],
            returns=DocReturn(type="整数型", description="和"),
        )
        result = formatter.format_function(func)
        assert "add" in result
        assert "参数" in result

    def test_json_formatter(self):
        """测试 JSON 格式化器。"""
        formatter = JsonFormatter()
        func = DocFunction(name="test", description="测试")
        result = formatter.format_function(func)
        data = json.loads(result)
        assert data["name"] == "test"

    def test_html_formatter(self):
        """测试 HTML 格式化器。"""
        formatter = HtmlFormatter()
        func = DocFunction(
            name="add",
            description="加法函数",
            signature="add(整数型 a, 整数型 b) -> 整数型",
        )
        result = formatter.format_function(func)
        assert "<h3" in result
        assert "add" in result

    def test_get_formatter(self):
        """测试获取格式化器。"""
        assert isinstance(get_formatter("text"), TextFormatter)
        assert isinstance(get_formatter("markdown"), MarkdownFormatter)
        assert isinstance(get_formatter("md"), MarkdownFormatter)
        assert isinstance(get_formatter("json"), JsonFormatter)
        assert isinstance(get_formatter("html"), HtmlFormatter)

    def test_get_formatter_invalid(self):
        """测试获取无效格式化器。"""
        with pytest.raises(ValueError, match="不支持的格式"):
            get_formatter("invalid")


class TestAPIGenerator:
    """API 生成器测试。"""

    def test_scan_source(self, tmp_path):
        """测试扫描源代码。"""
        # 创建测试源文件
        source_file = tmp_path / "test.zhc"
        source_file.write_text(
            """
/**
 * 加法函数
 *
 * @param a 第一个数
 * @param b 第二个数
 * @return 和
 */
函数 整数型 加(整数型 a, 整数型 b) {
    返回 a + b;
}

/**
 * 坐标点
 */
结构体 Point {
    浮点型 x;
    浮点型 y;
}

/**
 * 颜色枚举
 */
枚举 Color {
    RED = 0,
    GREEN = 1,
    BLUE = 2,
}
""",
            encoding="utf-8",
        )

        generator = APIGenerator(tmp_path)
        generator.scan_sources([tmp_path], extensions=[".zhc"])

        assert "加" in generator.functions
        assert "Point" in generator.structures
        assert "Color" in generator.enums

    def test_generate_markdown(self, tmp_path):
        """测试生成 Markdown 文档。"""
        # 创建测试源文件
        source_file = tmp_path / "test.zhc"
        source_file.write_text(
            """
/**
 * 测试函数
 *
 * @param x 输入值
 * @return 输出值
 */
函数 整数型 测试(整数型 x) {
    返回 x;
}
""",
            encoding="utf-8",
        )

        output_dir = tmp_path / "docs"

        generator = APIGenerator(tmp_path)
        generator.scan_sources([tmp_path], extensions=[".zhc"])
        generator.generate_docs(output_dir, format="markdown")

        assert (output_dir / "API.md").exists()
        content = (output_dir / "API.md").read_text()
        assert "测试" in content

    def test_generate_json(self, tmp_path):
        """测试生成 JSON 文档。"""
        source_file = tmp_path / "test.zhc"
        source_file.write_text(
            """
函数 整数型 add(整数型 a) {
    返回 a;
}
""",
            encoding="utf-8",
        )

        output_dir = tmp_path / "docs"

        generator = APIGenerator(tmp_path)
        generator.scan_sources([tmp_path], extensions=[".zhc"])
        generator.generate_docs(output_dir, format="json")

        assert (output_dir / "api.json").exists()
        data = json.loads((output_dir / "api.json").read_text())
        assert "modules" in data

    def test_generate_html(self, tmp_path):
        """测试生成 HTML 文档。"""
        source_file = tmp_path / "test.zhc"
        source_file.write_text(
            """
/**
 * 测试函数
 */
函数 整数型 test() {
    返回 0;
}
""",
            encoding="utf-8",
        )

        output_dir = tmp_path / "docs"

        generator = APIGenerator(tmp_path)
        generator.scan_sources([tmp_path], extensions=[".zhc"])
        generator.generate_docs(output_dir, format="html")

        assert (output_dir / "index.html").exists()
        content = (output_dir / "index.html").read_text()
        assert "<!DOCTYPE html>" in content
        assert "test" in content

    def test_generate_api_docs_convenience(self, tmp_path):
        """测试便捷函数。"""
        source_file = tmp_path / "test.zhc"
        source_file.write_text("函数 void test() { }", encoding="utf-8")

        output_dir = tmp_path / "docs"
        generate_api_docs(tmp_path, output_dir, format="json")

        assert (output_dir / "api.json").exists()


class TestDocComment:
    """DocComment 类测试。"""

    def test_get_tag(self):
        """测试获取标签。"""
        comment = parse_comment("@param x 参数")
        tag = comment.get_tag("param")
        assert tag is not None
        assert tag.name == "param"

    def test_get_all_tags(self):
        """测试获取所有标签。"""
        comment = parse_comment("""
        @param a 参数1
        @param b 参数2
        """)
        params = comment.get_all_tags("param")
        assert len(params) == 2

    def test_has_tag(self):
        """测试检查标签存在。"""
        comment = parse_comment("@deprecated 已废弃")
        assert comment.has_tag("deprecated")
        assert not comment.has_tag("author")

    def test_get_deprecated(self):
        """测试获取废弃说明。"""
        comment = parse_comment("@deprecated 请使用新函数")
        assert comment.get_deprecated() == "请使用新函数"

    def test_get_example(self):
        """测试获取示例。"""
        comment = parse_comment("""
        @示例
        test()
        """)
        example = comment.get_example(0)
        assert example is not None
        assert "test()" in example
