"""
中文C关键词映射表

包含所有中文关键词到C语言关键词的映射。
"""

# 中文关键词映射表
M = {
    # 控制流关键字
    "返回": "return",
    "如果": "if",
    "否则": "else",
    "循环": "for",
    "判断": "while",
    "执行": "do",
    "选择": "switch",
    "分支": "case",
    "默认": "default",
    "跳出": "break",
    "继续": "continue",
    "去向": "goto",
    # 类型修饰符
    "常量": "const",
    "静态": "static",
    "易变": "volatile",
    "外部": "extern",
    "注册": "register",
    "内联": "inline",
    "无符号": "unsigned",
    "有符号": "signed",
    # 基础类型
    "整数型": "int",
    "字符型": "char",
    "浮点型": "float",
    "双精度浮点型": "double",
    "逻辑型": "_Bool",
    "长整数型": "long",
    "短整数型": "short",
    "无类型": "void",
    "空型": "void",
    # 复合类型
    "结构体": "struct",
    "共用体": "union",
    "别名": "typedef",
    "枚举": "enum",
    # 内存管理 (stdlib.h)
    "申请": "malloc",
    "释放": "free",
    "申请数组": "calloc",
    "重新申请": "realloc",
    "退出程序": "exit",
    "终止程序": "abort",
    "获取环境变量": "getenv",
    "随机数": "rand",
    "设置种子": "srand",
    "快速排序": "qsort",
    "二分查找": "bsearch",
    "绝对值": "abs",
    "绝对值长": "labs",
    "绝对值长长": "llabs",
    # 输入输出 (stdio.h)
    "打印": "printf",
    "输入": "scanf",
    "输出字符": "putchar",
    "输入字符": "getchar",
    "打印字符串": "puts",
    "获取字符串": "gets",
    "格式化打印到字符串": "sprintf",
    "格式化输入从字符串": "sscanf",
    "打开文件": "fopen",
    "关闭文件": "fclose",
    "读取字符": "fgetc",
    "写入字符": "fputc",
    "读取字符串": "fgets",
    "写入字符串": "fputs",
    "格式化打印到文件": "fprintf",
    "格式化输入从文件": "fscanf",
    "读取块": "fread",
    "写入块": "fwrite",
    "文件位置": "ftell",
    "移动文件位置": "fseek",
    "重置文件位置": "rewind",
    "刷新缓冲区": "fflush",
    "检查文件结束": "feof",
    "检查文件错误": "ferror",
    "清除错误标志": "clearerr",
    # 字符串操作 (string.h)
    "字符串长度": "strlen",
    "字符串复制": "strcpy",
    "字符串安全复制": "strncpy",
    "字符串连接": "strcat",
    "字符串安全连接": "strncat",
    "字符串比较": "strcmp",
    "字符串安全比较": "strncmp",
    "查找字符": "strchr",
    "查找最后字符": "strrchr",
    "查找子串": "strstr",
    "分割字符串": "strtok",
    "内存设置": "memset",
    "内存复制": "memcpy",
    "内存移动": "memmove",
    "内存比较": "memcmp",
    "查找内存字符": "memchr",
    # 数学函数 (math.h)
    "平方根": "sqrt",
    "立方根": "cbrt",
    "幂函数": "pow",
    "指数": "exp",
    "自然对数": "log",
    "常用对数": "log10",
    "正弦": "sin",
    "余弦": "cos",
    "正切": "tan",
    "反正弦": "asin",
    "反余弦": "acos",
    "反正切": "atan",
    "双曲正弦": "sinh",
    "双曲余弦": "cosh",
    "双曲正切": "tanh",
    "向上取整": "ceil",
    "向下取整": "floor",
    "四舍五入": "round",
    "截断小数": "trunc",
    "绝对值浮点": "fabs",
    # 时间函数 (time.h)
    "当前时间": "time",
    "程序运行时间": "clock",
    "格式化时间": "strftime",
    "本地时间": "localtime",
    "世界时间": "gmtime",
    "时间转字符串": "ctime",
    "等待": "sleep",
    "微秒等待": "usleep",
    # 字符处理 (ctype.h)
    "是字母": "isalpha",
    "是数字": "isdigit",
    "是字母数字": "isalnum",
    "是控制字符": "iscntrl",
    "是图形字符": "isgraph",
    "是小写": "islower",
    "是打印字符": "isprint",
    "是标点": "ispunct",
    "是空格": "isspace",
    "是大写": "isupper",
    "是十六进制": "isxdigit",
    "转小写": "tolower",
    "转大写": "toupper",
    # 主函数
    "主函数": "main",
    # 模块系统关键字
    "模块": "module",
    "导入": "import",
    "公开:": "public:",
    "私有:": "private:",
    "版本": "version",
    "为": "as",
}

# 添加前缀版本（兼容"中文"前缀）
for k, v in list(M.items()):
    M[f"中文{k}"] = v

# 排序（最长优先，用于匹配）
KEYS = sorted(M.keys(), key=len, reverse=True)


def get_sorted_keys():
    """获取排序后的关键词列表（最长优先）"""
    return KEYS


def translate(keyword: str) -> str:
    """翻译单个关键词"""
    return M.get(keyword, keyword)


__all__ = ["M", "KEYS", "get_sorted_keys", "translate"]
