# Phase 4：AI 编程接口

**版本**: v1.0
**日期**: 2026-04-13
**基于文档**: `06-AI编程接入接口.md`、`12-项目规模与工时估算.md`、`15-重构任务执行清单.md`
**目标**: 完成编译器内嵌 AI 助手，能解释错误、提供修复建议
**工时**: 307h（含 20% 风险缓冲）
**日历时间**: 约 2.5 个月
**前置条件**: Phase 2 完成（编译能力可用）

---

## 4.1 阶段目标

在编译器中内嵌 AI 助手（不是插件），提供：

1. **AI 编排器**：统一管理 AI 请求
2. **多模型适配器**：支持 OpenAI/Claude/Gemini/本地模型
3. **模型路由器**：智能选择模型（按任务类型、成本、延迟）
4. **AI 诊断集成**：错误解释 + 自动修复建议
5. **CLI AI 参数**：`-ai` 系列参数
6. **中文提示词优化**：针对中文编程场景优化

---

## 4.2 Month 1：核心架构

### 任务 4.2.1 AI 编排器

#### T4.1 实现 AI Orchestrator

**交付物**: `include/zhc/ai/Orchestrator.h` + `lib/ai/Orchestrator.cpp`

**操作步骤**:
1. 实现统一的 AI 请求管理器：

```cpp
// include/zhc/ai/Orchestrator.h
namespace zhc::ai {

class Orchestrator {
public:
    Orchestrator();

    /// 配置选项
    struct Options {
        std::string DefaultModel = "gpt-4o";
        bool EnableCache = true;
        unsigned MaxRetries = 3;
        unsigned TimeoutMs = 30000;
        bool EnableFallback = true;
    };

    /// 发送请求
    struct Request {
        std::string Prompt;
        std::string SystemPrompt;
        std::string ModelHint;  // "fast", "smart", "local"
        std::map<std::string, std::string> Context;
    };

    struct Response {
        std::string Content;
        std::string ModelUsed;
        unsigned TokensUsed;
        double LatencyMs;
        bool Success;
        std::string ErrorMsg;
    };

    Response send(const Request &Req);

    /// 流式响应（用于实时补全）
    void sendStreaming(const Request &Req,
                       std::function<void(std::string)> OnChunk);

    /// 缓存管理
    void clearCache();
    void setCacheSize(unsigned MaxEntries);

private:
    std::unique_ptr<ModelRouter> Router;
    std::unique_ptr<ResponseCache> Cache;
    Options Opts;
};

} // namespace zhc::ai
```

2. 实现请求队列和超时处理：
```cpp
Response Orchestrator::send(const Request &Req) {
    // 1. 检查缓存
    if (Opts.EnableCache) {
        auto Cached = Cache->lookup(Req.Prompt);
        if (Cached) return *Cached;
    }

    // 2. 选择模型
    std::string Model = Router->selectModel(Req.ModelHint);

    // 3. 发送请求（带重试）
    Response Resp;
    for (unsigned i = 0; i < Opts.MaxRetries; ++i) {
        Resp = Router->send(Model, Req);
        if (Resp.Success) break;
        // 失败后等待并重试
        std::this_thread::sleep_for(std::chrono::milliseconds(1000 * (i + 1)));
    }

    // 4. 缓存成功响应
    if (Resp.Success && Opts.EnableCache)
        Cache->insert(Req.Prompt, Resp);

    return Resp;
}
```

**参考**: `06-AI编程接入接口.md`

**工时**: 60h

---

### 任务 4.2.2 模型适配器

#### T4.2 实现模型适配器接口

**交付物**: `include/zhc/ai/Adapter.h`

**操作步骤**:
1. 定义统一的模型适配器接口：

```cpp
// include/zhc/ai/Adapter.h
namespace zhc::ai {

class ModelAdapter {
public:
    virtual ~ModelAdapter() = default;

    /// 发送请求
    virtual Response send(const Request &Req) = 0;

    /// 流式请求
    virtual void sendStreaming(const Request &Req,
                               std::function<void(std::string)> OnChunk) = 0;

    /// 模型信息
    virtual std::string getName() const = 0;
    virtual std::vector<std::string> getSupportedModels() const = 0;
    virtual bool isAvailable() const = 0;

    /// 配置
    virtual void setApiKey(const std::string &Key) = 0;
    virtual void setEndpoint(const std::string &Url) = 0;
};

} // namespace zhc::ai
```

**工时**: 8h

---

#### T4.3 实现 OpenAI 适配器

**交付物**: `lib/ai/AdapterOpenAI.cpp`

**操作步骤**:
1. 实现 OpenAI API 调用：

```cpp
// lib/ai/AdapterOpenAI.cpp
class OpenAIAdapter : public ModelAdapter {
public:
    Response send(const Request &Req) override {
        // 构建 HTTP 请求
        std::string Body = buildRequestBody(Req);

        // 发送 POST 到 https://api.openai.com/v1/chat/completions
        auto HttpResp = HttpClient::post(
            Endpoint + "/v1/chat/completions",
            Body,
            {"Authorization: Bearer " + ApiKey,
             "Content-Type: application/json"});

        if (!HttpResp.Success) {
            return { .Success = false, .ErrorMsg = HttpResp.Error };
        }

        // 解析 JSON 响应
        auto Json = llvm::json::parse(HttpResp.Body);
        if (!Json) {
            return { .Success = false, .ErrorMsg = "JSON 解析失败" };
        }

        auto *Root = Json->getAsObject();
        auto *Choices = Root->getArray("choices");
        if (!Choices || Choices->empty()) {
            return { .Success = false, .ErrorMsg = "无响应内容" };
        }

        auto *FirstChoice = Choices->front().getAsObject();
        auto *Message = FirstChoice->getObject("message");
        auto *Content = Message->getString("content");

        return {
            .Content = Content->str(),
            .ModelUsed = Root->getString("model")->str(),
            .TokensUsed = Root->getObject("usage")
                          ->getInteger("total_tokens")->value_or(0),
            .Success = true
        };
    }

private:
    std::string buildRequestBody(const Request &Req) {
        llvm::json::Object Body;
        Body["model"] = Req.ModelHint.empty() ? "gpt-4o" : Req.ModelHint;
        Body["messages"] = llvm::json::Array{
            llvm::json::Object{{"role", "system"}, {"content", Req.SystemPrompt}},
            llvm::json::Object{{"role", "user"}, {"content", Req.Prompt}}
        };
        return llvm::json::toString(Body);
    }
};
```

**工时**: 16h

---

#### T4.4 实现 Claude 适配器

**交付物**: `lib/ai/AdapterAnthropic.cpp`

**操作步骤**:
1. 实现 Anthropic Claude API 调用（类似 OpenAI，但 API 格式不同）：

```cpp
// Claude API 格式
// POST https://api.anthropic.com/v1/messages
// Headers: x-api-key, anthropic-version
// Body: { model, max_tokens, messages }
```

**工时**: 16h

---

#### T4.5 实现 Gemini 适配器

**交付物**: `lib/ai/AdapterGoogle.cpp`

**操作步骤**:
1. 实现 Google Gemini API 调用：

```cpp
// Gemini API 格式
// POST https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=API_KEY
// Body: { contents: [{ parts: [{ text: prompt }] }] }
```

**工时**: 16h

---

#### T4.6 实现本地模型适配器

**交付物**: `lib/ai/AdapterLocal.cpp`

**操作步骤**:
1. 实现 Ollama/LM Studio 本地模型调用：

```cpp
// Ollama API 格式
// POST http://localhost:11434/api/generate
// Body: { model, prompt, stream: false }
```

2. 支持的本地模型：
   - Ollama: `llama3`, `mistral`, `codellama`
   - LM Studio: 通过 OpenAI-compatible API

**工时**: 16h

---

### 任务 4.2.3 模型路由器

#### T4.7 实现智能模型路由

**交付物**: `include/zhc/ai/Router.h` + `lib/ai/Router.cpp`

**操作步骤**:
1. 实现模型选择策略：

```cpp
// include/zhc/ai/Router.h
class ModelRouter {
public:
    /// 选择最佳模型
    std::string selectModel(const std::string &Hint);

    /// 注册适配器
    void registerAdapter(std::unique_ptr<ModelAdapter> Adapter);

    /// 发送请求到指定模型
    Response send(const std::string &Model, const Request &Req);

private:
    std::map<std::string, std::unique_ptr<ModelAdapter>> Adapters;

    /// 路由策略
    enum Strategy { Fastest, Smartest, Cheapest, LocalFirst };
    Strategy CurrentStrategy = Strategy::Smartest;

    /// 模型能力表
    struct ModelInfo {
        std::string Name;
        double Speed;      // 相对速度（1.0 = 基准）
        double Quality;    // 相对质量（1.0 = 基准）
        double Cost;       // 每 1K tokens 成本（美元）
        bool IsLocal;      // 是否本地模型
    };
    std::vector<ModelInfo> ModelTable;
};
```

2. 路由策略：
   - `fast`: 选择最快的模型（本地优先）
   - `smart`: 选择最智能的模型（GPT-4o/Claude）
   - `cheap`: 选择最便宜的模型（Gemini Flash）
   - `local`: 强制使用本地模型

**工时**: 24h

---

## 4.3 Month 2：诊断集成 + CLI

### 任务 4.3.1 AI 诊断集成

#### T4.8 实现 AI 诊断增强

**交付物**: `include/zhc/ai/DiagnosticsAI.h` + `lib/ai/DiagnosticsAI.cpp`

**操作步骤**:
1. 在诊断引擎中集成 AI 解释：

```cpp
// include/zhc/ai/DiagnosticsAI.h
class AIDiagnosticsEnhancer {
public:
    AIDiagnosticsEnhancer(Orchestrator &O, DiagnosticsEngine &D);

    /// 增强诊断消息
    struct EnhancedDiag {
        std::string OriginalMessage;
        std::string AIExplanation;
        std::string FixSuggestion;
        std::string CodeSnippet;  // 修复后的代码片段
    };

    EnhancedDiag enhance(const Diagnostic &Diag);

    /// 自动修复
    bool autoFix(const Diagnostic &Diag,
                 std::function<void(std::string)> ApplyFix);

private:
    Orchestrator &TheOrchestrator;
    DiagnosticsEngine &Diags;

    /// 构建 AI 提示词
    std::string buildPrompt(const Diagnostic &Diag);
};
```

2. 提示词模板：
```cpp
std::string AIDiagnosticsEnhancer::buildPrompt(const Diagnostic &Diag) {
    return llvm::formatv(
        "你是一个 ZhC 编译器的 AI 助手。请解释以下编译错误并提供修复建议。\n\n"
        "错误信息：{0}\n"
        "源文件：{1}\n"
        "行号：{2}\n"
        "代码片段：\n{3}\n\n"
        "请用中文回答，格式如下：\n"
        "1. 错误原因：...\n"
        "2. 修复方法：...\n"
        "3. 修复后的代码：...",
        Diag.getMessage(),
        Diag.getFile(),
        Diag.getLine(),
        Diag.getSourceSnippet());
}
```

**参考**: `06-AI编程接入接口.md`

**工时**: 32h

---

#### T4.9 实现错误修复建议

**交付物**: `lib/ai/AutoFix.cpp`

**操作步骤**:
1. 实现自动修复逻辑：

```cpp
// lib/ai/AutoFix.cpp
bool AIDiagnosticsEnhancer::autoFix(
    const Diagnostic &Diag,
    std::function<void(std::string)> ApplyFix) {

    // 1. 发送修复请求
    Request Req;
    Req.Prompt = buildFixPrompt(Diag);
    Req.SystemPrompt = "你是 ZhC 编译器的自动修复助手。"
                       "只输出修复后的代码，不要解释。";
    Req.ModelHint = "smart";

    Response Resp = TheOrchestrator.send(Req);
    if (!Resp.Success) return false;

    // 2. 解析修复后的代码
    std::string FixedCode = extractCode(Resp.Content);
    if (FixedCode.empty()) return false;

    // 3. 应用修复
    ApplyFix(FixedCode);
    return true;
}
```

**工时**: 20h

---

#### T4.10 实现代码补全

**交付物**: `lib/ai/Completion.cpp`

**操作步骤**:
1. 实现基于 AI 的代码补全：

```cpp
// lib/ai/Completion.cpp
class AICompletionProvider {
public:
    struct CompletionResult {
        std::string Text;
        std::string DisplayText;
        std::string Documentation;
        unsigned InsertPosition;
    };

    std::vector<CompletionResult> complete(
        const std::string &Prefix,
        const std::string &Context,
        const std::string &FileContent,
        unsigned CursorPos);

private:
    std::string buildCompletionPrompt(
        const std::string &Prefix,
        const std::string &Context);
};
```

**工时**: 20h

---

### 任务 4.3.2 CLI AI 参数

#### T4.11 实现 CLI AI 参数

**交付物**: `tools/zhc/zhc.cpp` 中的 AI 参数

**操作步骤**:
1. 添加 AI 相关命令行参数：

```cpp
// tools/zhc/zhc.cpp

cl::opt<bool> EnableAI("ai",
    cl::desc("启用 AI 助手（解释错误、提供修复建议）"),
    cl::init(false));

cl::opt<bool> AutoFix("ai-auto-fix",
    cl::desc("自动修复编译错误"),
    cl::init(false));

cl::opt<std::string> AIModel("ai-model",
    cl::desc("指定 AI 模型（gpt-4o, claude-3, gemini-pro, local）"),
    cl::init(""));

cl::opt<std::string> AIEndpoint("ai-endpoint",
    cl::desc("指定 AI API endpoint"),
    cl::init(""));

cl::opt<std::string> AIKey("ai-key",
    cl::desc("指定 AI API key"),
    cl::init(""));
```

2. 在编译流程中集成：
```cpp
if (EnableAI) {
    // 初始化 AI 编排器
    Orchestrator AI;
    if (!AIKey.empty())
        AI.setApiKey(AIKey);
    if (!AIEndpoint.empty())
        AI.setEndpoint(AIEndpoint);

    // 增强诊断
    AIDiagnosticsEnhancer Enhancer(AI, Diags);
    for (auto &Diag : Diags.getDiagnostics()) {
        auto Enhanced = Enhancer.enhance(Diag);
        llvm::outs() << "\n🤖 AI 解释:\n" << Enhanced.AIExplanation << "\n";
        if (AutoFix && !Enhanced.CodeSnippet.empty()) {
            llvm::outs() << "🔧 自动修复:\n" << Enhanced.CodeSnippet << "\n";
            // 应用修复...
        }
    }
}
```

**工时**: 16h

---

### 任务 4.3.3 中文提示词优化

#### T4.12 实现中文提示词优化

**交付物**: `include/zhc/ai/ChinesePrompt.h` + `lib/ai/ChinesePrompt.cpp`

**操作步骤**:
1. 针对中文编程场景优化提示词：

```cpp
// include/zhc/ai/ChinesePrompt.h
class ChinesePromptOptimizer {
public:
    /// 优化提示词
    std::string optimize(const std::string &RawPrompt);

    /// 添加中文编程上下文
    std::string addContext(const std::string &Prompt);

private:
    /// 中文关键词映射表
    std::map<std::string, std::string> KeywordTranslations;

    /// 常见错误模板
    std::vector<std::string> ErrorTemplates;
};
```

2. 优化策略：
   - 将中文关键词翻译为英文等价词（帮助模型理解）
   - 添加 ZhC 语言特性说明
   - 使用中文编程教学风格的语言

**工时**: 20h

---

### 任务 4.3.4 AI 功能测试

#### T4.13 AI 功能集成测试

**交付物**: `test/ai_tests/ai_test.cpp`

**操作步骤**:
1. 测试场景：
   - 错误解释：故意写错代码，验证 AI 解释正确
   - 自动修复：验证修复后的代码可编译
   - 代码补全：验证补全建议合理
   - 模型路由：验证不同 hint 选择正确模型
   - 超时处理：验证超时后降级到本地模型

2. Mock 测试（不依赖真实 API）：
```cpp
TEST_F(AITest, ErrorExplanationMock) {
    MockOrchestrator Mock;
    Mock.setResponse("这是一个类型不匹配错误...");

    AIDiagnosticsEnhancer Enhancer(Mock, Diags);
    auto Result = Enhancer.enhance(Diag);

    EXPECT_TRUE(Result.AIExplanation.find("类型") != std::string::npos);
}
```

**验收标准**:
```bash
zhc compile error.zhc -ai
# AI 建议: 第 5 行缺少分号，请添加 ';'

zhc compile error.zhc -ai-auto-fix
# ✅ 已自动修复 1 个错误
```

**工时**: 40h

---

## 4.4 Phase 4 Go/No-Go 检查点

| 检查项 | 验收命令 | 通过标准 |
|:---|:---|:---|
| **AI 解释** | `zhc compile error.zhc -ai` | 输出中文解释 |
| **自动修复** | `zhc compile error.zhc -ai-auto-fix` | 修复后可编译 |
| **模型路由** | `-ai-model=local` | 使用本地模型 |
| **超时处理** | 模拟超时 | 降级到本地模型 |
| **响应时间** | P95 < 5s | 95% 请求 < 5s |

**量化标准**：
- AI 错误解释成功率 > 80%
- P95 响应时间 < 5s

**如未通过**：
- 增加超时处理
- 增加本地模型作为降级选项

---

## 4.5 参考资料

| 资料 | 路径 | 用途 |
|:---|:---|:---|
| AI 接口设计 | `06-AI编程接入接口.md` | 功能设计参考 |
| OpenAI API | https://platform.openai.com/docs | API 格式参考 |
| Claude API | https://docs.anthropic.com | API 格式参考 |
| Gemini API | https://ai.google.dev/docs | API 格式参考 |
| Ollama API | https://github.com/ollama/ollama | 本地模型参考 |