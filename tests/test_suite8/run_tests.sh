#!/bin/bash
# 测试套件8运行脚本

echo "🚀 运行测试套件8：模块系统转换功能测试"
echo "=========================================="

# 进入项目根目录
cd "$(dirname "$0")/../.."

# 检查Python版本
echo "检查Python版本..."
python3 --version

# 运行测试
echo -e "\n运行测试套件8..."
python3 -m pytest tests/test_suite8/test_module_conversion.py -v

# 如果pytest不可用，使用unittest
if [ $? -ne 0 ]; then
    echo -e "\npytest不可用，使用unittest..."
    python3 tests/test_suite8/test_module_conversion.py
fi

# 运行其他测试文件（如果有）
echo -e "\n运行其他测试..."
for test_file in tests/test_suite8/test_*.py; do
    if [ "$test_file" != "tests/test_suite8/test_module_conversion.py" ]; then
        echo "运行: $test_file"
        python3 "$test_file"
    fi
done

echo -e "\n✅ 测试套件8运行完成"