#!/bin/bash
# 测试套件7运行脚本

echo "========================================="
echo "中文C编译器 - 测试套件7：模块系统测试"
echo "========================================="

# 设置项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

# 检查Python环境
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

echo "项目根目录: $PROJECT_ROOT"
echo "Python命令: $PYTHON_CMD"
echo ""

# 运行模块系统测试
echo "=== 运行模块系统测试 ==="
"$PYTHON_CMD" tests/test_suite7/test_module_system.py

TEST_RESULT=$?

echo ""
echo "=== 创建测试示例文件 ==="

# 创建测试目录
TEST_EXAMPLES_DIR="tests/test_suite7/examples"
mkdir -p "$TEST_EXAMPLES_DIR"

# 创建基础模块示例
cat > "$TEST_EXAMPLES_DIR/basic_module.zhc" << 'EOF'
模块 数学库 {
    公开:
        函数 加法(整数型 a, 整数型 b) -> 整数型 {
            返回 a + b;
        }

        函数 乘法(整数型 a, 整数型 b) -> 整数型 {
            返回 a * b;
        }

    私有:
        整数型 内部常量 = 100;
}

模块 主程序 {
    导入 数学库

    主函数() -> 整数型 {
        整数型 结果1 = 加法(3, 4);
        整数型 结果2 = 乘法(3, 4);

        打印("加法结果: %d\n", 结果1);
        打印("乘法结果: %d\n", 结果2);

        返回 0;
    }
}
EOF

# 创建多模块导入示例
cat > "$TEST_EXAMPLES_DIR/multi_module.zhc" << 'EOF'
模块 工具库 {
    公开:
        函数 最大值(整数型 a, 整数型 b) -> 整数型 {
            如果 (a > b) {
                返回 a;
            } 否则 {
                返回 b;
            }
        }

        函数 最小值(整数型 a, 整数型 b) -> 整数型 {
            如果 (a < b) {
                返回 a;
            } 否则 {
                返回 b;
            }
        }
}

模块 数学库 {
    公开:
        函数 平方(整数型 x) -> 整数型 {
            返回 x * x;
        }

        函数 立方(整数型 x) -> 整数型 {
            返回 x * x * x;
        }
}

模块 主程序 {
    导入 工具库
    导入 数学库

    主函数() -> 整数型 {
        整数型 a = 5;
        整数型 b = 3;

        整数型 最大 = 最大值(a, b);
        整数型 最小 = 最小值(a, b);
        整数型 平 = 平方(a);
        整数型 立 = 立方(b);

        打印("最大: %d, 最小: %d\n", 最大, 最小);
        打印("平方: %d, 立方: %d\n", 平, 立);

        返回 0;
    }
}
EOF

echo "测试示例文件已创建到: $TEST_EXAMPLES_DIR"
echo ""

# 运行模块解析器测试
echo "=== 测试模块解析器 ==="
"$PYTHON_CMD" -c "
import sys
from pathlib import Path
sys.path.insert(0, 'src')

from zhpp.parser.module import ModuleParser

test_code = '''
模块 测试模块 {
    公开:
        函数 测试函数(整数型 x) -> 整数型 {
            返回 x * 2;
        }
}
'''

print('测试模块解析器...')
parser = ModuleParser()
lines = test_code.split('\n')
for i, line in enumerate(lines, 1):
    parser.parse_line(line.strip(), i)

print('解析成功!')
print('模块数:', len(parser.modules))
print('公开符号数:', len(parser.modules['测试模块'].public_symbols))
"

echo ""
echo "=== 测试作用域管理器 ==="
"$PYTHON_CMD" -c "
import sys
from pathlib import Path
sys.path.insert(0, 'src')

from zhpp.parser.scope import ScopeManager, Visibility, ScopeType

print('测试作用域管理器...')
manager = ScopeManager()

manager.enter_scope('模块A', ScopeType.MODULE)
manager.add_symbol('公开函数', Visibility.PUBLIC, 10)
manager.add_symbol('私有变量', Visibility.PRIVATE, 12)
manager.exit_scope()

stats = manager.get_statistics()
print('测试成功!')
print('模块数:', stats['modules'])
print('公开符号:', stats['public_symbols'])
print('私有符号:', stats['private_symbols'])
"

echo ""
echo "========================================="
if [ $TEST_RESULT -eq 0 ]; then
    echo "✅ 测试套件7运行完成 - 所有测试通过！"
else
    echo "❌ 测试套件7运行完成 - 有测试失败"
fi
echo "========================================="

exit $TEST_RESULT