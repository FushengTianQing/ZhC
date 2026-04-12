# Phase 5：AI 可信执行监控 — 开发任务清单

**版本**: v1.0  
**所属阶段**: Phase 5（2.5 个月 / 408h 含缓冲）  
**前置阶段**: Phase 4（AI 编程接口）完成后进入  
**文档目的**: 直接指导程序员进行开发，包含操作步骤、代码示例、验收标准  

---

## 5.0 阶段概述

### 目标

在 Phase 4 完成的 AI 编程接口基础上，增加**可信执行监控层**，确保 AI 生成的代码在执行前经过安全检查、幻觉检测和沙箱隔离，防止危险操作影响用户系统。

### 核心模块

| 模块 | 文件 | 工时 | 说明 |
|:---|:---|:---:|:---|
| 监控管理器 | `zhc_ai_monitor.cpp/h` | 60h | 核心监控引擎 |
| 安全策略引擎 | `zhc_security_policy.cpp` | 40h | 策略规则引擎 |
| 策略库 | `policies/default_policy.json` | 16h | 预定义安全策略 |
| 幻觉检测器 | `zhc_hallucination_detector.cpp` | 48h | AI 幻觉检测 |
| 内置知识库 | `builtin_knowledge.cpp/h` | 16h | 已知函数签名库 |
| 沙箱执行器 | `zhc_sandbox_executor.cpp` | 56h | 隔离执行 |
| 内存安全分析 | `zhc_memory_safety.cpp` | 32h | 静态内存检查 |
| 系统调用过滤 | `zhc_syscall_filter.cpp` | 24h | Seccomp/eBPF |
| 告警日志 | `zhc_alert_logger.cpp/h` | 20h | 统一告警 |
| CLI 集成 | `zhc_cli.cpp` | 12h | `-ai-monitor` 参数 |
| 集成测试 | `test/ai_monitor_test.cpp` | 40h | 端到端测试 |

**总工时**: 364h（无缓冲）/ 408h（含 12% 缓冲）

---

## T5.1：监控管理器（核心引擎）

**工时**: 60h  
**依赖**: Phase 4 完成的 AI Orchestrator  
**交付物**: `zhc_ai_monitor.cpp/h`

### 1.1 头文件设计

**文件**: `include/zhc/ai/zhc_ai_monitor.h`

```cpp
#pragma once

#include <string>
#include <vector>
#include <memory>
#include <chrono>
#include "zhc_ai_types.h"

namespace zhc {
namespace ai {

// 前向声明
class SecurityPolicy;
class HallucinationDetector;
class SandboxExecutor;
class AlertLogger;

// 监控级别
enum class MonitorLevel {
    Off,      // 完全关闭
    Warning,  // 仅警告
    Strict    // 阻止并报错
};

// 监控结果
struct MonitorResult {
    bool IsAllowed;
    float TrustScore;        // 0.0-1.0，可信度评分
    std::vector<std::string> Warnings;
    std::vector<std::string> BlockedReasons;
    std::chrono::milliseconds AnalysisTime;
    
    // 静态工厂
    static MonitorResult Allow(float trust_score = 1.0f) {
        return {true, trust_score, {}, {}, {}};
    }
    static MonitorResult Deny(float trust_score, const std::vector<std::string>& reasons) {
        return {false, trust_score, {}, reasons, {}};
    }
};

// AI 代码请求（带监控上下文）
struct MonitoredAIRequest {
    std::string OriginalPrompt;      // 原始用户提示
    std::string GeneratedCode;        // AI 生成的代码
    std::string SourceLanguage;       // "zhc", "c", "python"
    std::string TargetFunction;      // 目标函数名
    std::vector<std::string> CalledFunctions;  // 调用函数列表
    bool IsUserRequest;              // 是否用户直接输入
};

// 监控管理器类
class AIMonitorManager {
public:
    explicit AIMonitorManager(
        std::shared_ptr<SecurityPolicy> Policy,
        std::shared_ptr<HallucinationDetector> Hallucination,
        std::shared_ptr<SandboxExecutor> Sandbox,
        std::shared_ptr<AlertLogger> Logger
    );
    
    // 禁用拷贝
    AIMonitorManager(const AIMonitorManager&) = delete;
    AIMonitorManager& operator=(const AIMonitorManager&) = delete;
    
    // === 核心监控接口 ===
    
    // 分析 AI 生成的代码，返回是否可以执行
    MonitorResult AnalyzeCode(const MonitoredAIRequest& Request);
    
    // 异步分析（用于长时间分析）
    std::future<MonitorResult> AnalyzeCodeAsync(const MonitoredAIRequest& Request);
    
    // 运行时行为监控（程序执行时）
    void MonitorRuntime(const std::string& FunctionName, const void* Args, size_t ArgCount);
    
    // 运行时异常上报
    void ReportRuntimeViolation(const std::string& ViolationType, 
                                const std::string& Details);
    
    // === 配置接口 ===
    
    void SetMonitorLevel(MonitorLevel Level);
    MonitorLevel GetMonitorLevel() const;
    
    void SetTrustThreshold(float Threshold);  // 0.0-1.0
    float GetTrustThreshold() const;
    
    void SetBuiltinKnowledge(std::shared_ptr<BuiltinKnowledge> Knowledge);
    
    // === 查询接口 ===
    
    std::vector<std::string> GetRecentAlerts() const;
    float GetAverageTrustScore() const;
    size_t GetBlockedCount() const;

private:
    // 内部方法
    float CalculateTrustScore(const MonitoredAIRequest& Request);
    bool ShouldBlock(float TrustScore);
    void LogDecision(const MonitoredAIRequest& Request, const MonitorResult& Result);
    
    // 依赖注入
    std::shared_ptr<SecurityPolicy> Policy_;
    std::shared_ptr<HallucinationDetector> Hallucination_;
    std::shared_ptr<SandboxExecutor> Sandbox_;
    std::shared_ptr<AlertLogger> Logger_;
    std::shared_ptr<BuiltinKnowledge> BuiltinKnowledge_;
    
    // 配置
    MonitorLevel Level_ = MonitorLevel::Warning;
    float TrustThreshold_ = 0.7f;  // 默认阈值
    
    // 统计
    std::atomic<size_t> BlockedCount_{0};
    std::atomic<size_t> AllowedCount_{0};
    std::vector<float> RecentTrustScores_;  // 滑动窗口
    mutable std::mutex StatsMutex_;
};

} // namespace ai
} // namespace zhc
```

### 1.2 实现文件

**文件**: `src/ai/zhc_ai_monitor.cpp`

**关键实现逻辑**:

```cpp
#include "zhc_ai_monitor.h"
#include "zhc_security_policy.h"
#include "zhc_hallucination_detector.h"
#include "zhc_sandbox_executor.h"
#include "zhc_alert_logger.h"

namespace zhc {
namespace ai {

AIMonitorManager::AIMonitorManager(
    std::shared_ptr<SecurityPolicy> Policy,
    std::shared_ptr<HallucinationDetector> Hallucination,
    std::shared_ptr<SandboxExecutor> Sandbox,
    std::shared_ptr<AlertLogger> Logger)
    : Policy_(Policy)
    , Hallucination_(Hallucination)
    , Sandbox_(Sandbox)
    , Logger_(Logger)
{}

MonitorResult AIMonitorManager::AnalyzeCode(const MonitoredAIRequest& Request) {
    // 阶段 1：安全策略检查
    auto PolicyResult = Policy_->Check(Request.GeneratedCode);
    if (!PolicyResult.IsAllowed) {
        BlockedCount_.fetch_add(1);
        Logger_->LogAlert(AlertLevel::Critical, "SecurityPolicy", 
                         PolicyResult.Reasons);
        return MonitorResult::Deny(0.0f, PolicyResult.Reasons);
    }
    
    // 阶段 2：幻觉检测
    auto HallucinationResult = Hallucination_->Detect(Request);
    if (HallucinationResult.IsHighRisk) {
        Logger_->LogAlert(AlertLevel::Warning, "Hallucination",
                         {"可信度低: " + std::to_string(HallucinationResult.Confidence)});
    }
    
    // 阶段 3：计算总体信任评分
    float TrustScore = CalculateTrustScore(Request);
    
    // 阶段 4：判断是否阻止
    if (ShouldBlock(TrustScore)) {
        BlockedCount_.fetch_add(1);
        return MonitorResult::Deny(TrustScore, 
            {"信任评分 " + std::to_string(TrustScore) + " 低于阈值 " + std::to_string(TrustThreshold_)});
    }
    
    AllowedCount_.fetch_add(1);
    
    // 构建结果
    MonitorResult Result = MonitorResult::Allow(TrustScore);
    Result.Warnings = HallucinationResult.Warnings;
    return Result;
}

float AIMonitorManager::CalculateTrustScore(const MonitoredAIRequest& Request) {
    float Score = 1.0f;
    
    // 因子 1：用户输入 vs AI 生成（用户直接输入更可信）
    if (Request.IsUserRequest) {
        Score *= 1.2f;  // 加分
    } else {
        // AI 生成：检查函数调用
        for (const auto& Func : Request.CalledFunctions) {
            if (BuiltinKnowledge_ && BuiltinKnowledge_->IsKnownSafe(Func)) {
                Score *= 1.05f;  // 已知安全函数加分
            } else if (Policy_->IsDangerousFunction(Func)) {
                Score *= 0.5f;   // 危险函数减分
            }
        }
    }
    
    // 因子 2：源代码语言（ZHC 最可信）
    if (Request.SourceLanguage == "zhc") {
        Score *= 1.1f;
    } else if (Request.SourceLanguage == "c") {
        Score *= 0.95f;
    } else {
        Score *= 0.8f;  // Python 等风险更高
    }
    
    // 因子 3：代码长度（过长代码风险增加）
    if (Request.GeneratedCode.size() > 5000) {
        Score *= 0.9f;
    }
    
    // 限制在 [0.0, 1.0]
    return std::clamp(Score, 0.0f, 1.0f);
}

bool AIMonitorManager::ShouldBlock(float TrustScore) {
    if (Level_ == MonitorLevel::Off) return false;
    if (Level_ == MonitorLevel::Strict) {
        return TrustScore < TrustThreshold_;
    }
    // Warning 模式：返回 false，但记录警告
    return false;
}

void AIMonitorManager::SetMonitorLevel(MonitorLevel Level) {
    Level_ = Level;
}

MonitorLevel AIMonitorManager::GetMonitorLevel() const {
    return Level_;
}

std::future<MonitorResult> AIMonitorManager::AnalyzeCodeAsync(
    const MonitoredAIRequest& Request) {
    return std::async(std::launch::async, 
        [this](const MonitoredAIRequest& Req) {
            return this->AnalyzeCode(Req);
        }, Request);
}

} // namespace ai
} // namespace zhc
```

### 1.3 验收标准

```bash
# 单元测试：基本监控流程
./build/bin/zhc_ai_monitor_test --test-basic-flow
# 期望：分析代码并返回 MonitorResult

# 单元测试：危险代码阻止
./build/bin/zhc_ai_monitor_test --test-block-dangerous
# 期望：危险代码被阻止，可信度评分为 0.0

# 单元测试：异步分析
./build/bin/zhc_ai_monitor_test --test-async
# 期望：异步返回结果与同步一致

# 集成测试：完整监控流程
./build/bin/zhc_ai_monitor_test --test-full-pipeline
# 期望：通过 Policy + Hallucination + TrustScore 全流程
```

---

## T5.2：安全策略引擎

**工时**: 40h  
**依赖**: T5.1  
**交付物**: `zhc_security_policy.cpp`

### 2.1 头文件设计

**文件**: `include/zhc/ai/zhc_security_policy.h`

```cpp
#pragma once

#include <string>
#include <vector>
#include <unordered_map>
#include <unordered_set>

namespace zhc {
namespace ai {

// 危险操作类型
enum class DangerLevel {
    Safe,       // 安全
    Warning,    // 警告
    Dangerous,  // 危险
    Critical    // 严重危险
};

// 单条策略规则
struct PolicyRule {
    std::string Pattern;       // 正则表达式匹配模式
    std::string Description;   // 规则描述
    DangerLevel Level;         // 危险级别
    bool IsBlocking;           // 是否阻止执行
    std::string Recommendation; // 修复建议
};

// 策略检查结果
struct PolicyCheckResult {
    bool IsAllowed;
    std::vector<std::string> Reasons;
    std::vector<std::string> Recommendations;
    
    static PolicyCheckResult Allow() {
        return {true, {}, {}};
    }
    static PolicyCheckResult Deny(const std::vector<std::string>& reasons,
                                   const std::vector<std::string>& recs = {}) {
        return {false, reasons, recs};
    }
};

// 安全策略引擎
class SecurityPolicy {
public:
    SecurityPolicy();
    
    // 从 JSON 文件加载策略
    bool LoadFromFile(const std::string& Path);
    
    // 检查代码安全性
    PolicyCheckResult Check(const std::string& Code) const;
    
    // 检查单个函数是否危险
    bool IsDangerousFunction(const std::string& FuncName) const;
    
    // 获取函数的危险级别
    DangerLevel GetDangerLevel(const std::string& FuncName) const;
    
    // 添加自定义规则
    void AddRule(const PolicyRule& Rule);
    
    // 移除规则
    void RemoveRule(const std::string& Pattern);
    
    // 获取所有危险函数列表
    std::vector<std::string> GetDangerousFunctions() const;

private:
    std::vector<PolicyRule> Rules_;
    std::unordered_set<std::string> DangerousFunctions_;
    
    bool MatchPattern(const std::string& Code, const std::string& Pattern) const;
};

} // namespace ai
} // namespace zhc
```

### 2.2 实现文件

**文件**: `src/ai/zhc_security_policy.cpp`

**关键实现逻辑**:

```cpp
#include "zhc_security_policy.h"
#include <fstream>
#include <regex>
#include <algorithm>

namespace zhc {
namespace ai {

SecurityPolicy::SecurityPolicy() {
    // 默认危险函数列表
    DangerousFunctions_ = {
        // 系统操作
        "system", "popen", "exec", "fork", "vfork",
        // 文件操作（高风险）
        "remove", "rename", "rmdir", "unlink", "chmod", "chown",
        // 网络操作
        "socket", "connect", "bind", "listen", "accept",
        // 内存操作
        "malloc", "calloc", "realloc", "free",  // 需要配对检查
        "mmap", "mprotect", "mremap",
        // 进程操作
        "kill", "raise", "abort", "exit",
        // 危险库函数
        "gets", "strcpy", "strcat", "sprintf", "vsprintf"
    };
    
    // 默认策略规则
    Rules_ = {
        // 禁止直接调用危险函数
        {R"(system\s*\()", "直接调用 system() 函数", DangerLevel::Critical, true, 
         "使用更安全的替代方案，或通过沙箱执行"},
        
        // 禁止无边界 memcpy
        {R"(memcpy\s*\([^,]+,\s*[^,]+,\s*(?!sizeof))", "memcpy 未指定长度", 
         DangerLevel::Warning, false, "使用 memcpy(dst, src, sizeof(src))"},
        
        // 警告：可能未初始化的变量
        {R"(\bint\s+\w+\s*;[\s\S]*?\w+\s*\+)", "检测到可能未初始化变量使用", 
         DangerLevel::Warning, false, "确保变量使用前已初始化"},
        
        // 禁止 gets（已废弃）
        {R"(\bgets\s*\()", "gets() 是危险函数，已从 C11 移除", 
         DangerLevel::Critical, true, "使用 fgets() 替代"},
        
        // 警告：字符串操作
        {R"(\bstrcpy\s*\()", "strcpy() 可能导致缓冲区溢出", 
         DangerLevel::Warning, false, "使用 strncpy() 或 strlcpy()"},
    };
}

PolicyCheckResult SecurityPolicy::Check(const std::string& Code) const {
    std::vector<std::string> Reasons;
    std::vector<std::string> Recommendations;
    bool HasBlockingRule = false;
    
    for (const auto& Rule : Rules_) {
        if (MatchPattern(Code, Rule.Pattern)) {
            Reasons.push_back(Rule.Description);
            if (!Rule.Recommendation.empty()) {
                Recommendations.push_back(Rule.Recommendation);
            }
            if (Rule.IsBlocking) {
                HasBlockingRule = true;
            }
        }
    }
    
    if (HasBlockingRule || !Reasons.empty()) {
        return PolicyCheckResult::Deny(Reasons, Recommendations);
    }
    return PolicyCheckResult::Allow();
}

bool SecurityPolicy::MatchPattern(const std::string& Code, 
                                  const std::string& Pattern) const {
    try {
        std::regex Regex(Pattern);
        return std::regex_search(Code, Regex);
    } catch (const std::regex_error&) {
        // 如果正则表达式错误，尝试简单字符串匹配
        return Code.find(Pattern) != std::string::npos;
    }
}

bool SecurityPolicy::IsDangerousFunction(const std::string& FuncName) const {
    return DangerousFunctions_.find(FuncName) != DangerousFunctions_.end();
}

bool LoadPolicyFromJSON(SecurityPolicy& Policy, const std::string& Path) {
    std::ifstream File(Path);
    if (!File.is_open()) {
        return false;
    }
    
    // 简单的 JSON 解析（可替换为 nlohmann/json）
    std::string Content((std::istreambuf_iterator<char>(File)),
                         std::istreambuf_iterator<char>());
    
    // TODO: 解析 JSON 并添加规则
    // 此处使用简化实现
    return true;
}

} // namespace ai
} // namespace zhc
```

### 2.3 验收标准

```bash
# 测试 1：危险函数检测
echo "system(\"rm -rf /\");" | ./build/bin/zhc_security_test --check
# 期望输出：BLOCKED - 严重危险操作

# 测试 2：策略文件加载
./build/bin/zhc_security_test --load policies/default_policy.json
# 期望输出：Loaded 15 rules

# 测试 3：自定义规则
./build/bin/zhc_security_test --add-rule '{"pattern":"dangerous_func","level":"critical"}'
# 期望输出：Rule added successfully

# 测试 4：gets() 检测
echo 'char buf[100]; gets(buf);' | ./build/bin/zhc_security_test --check
# 期望输出：BLOCKED - gets() is deprecated
```

---

## T5.3：预定义策略库

**工时**: 16h  
**依赖**: T5.2  
**交付物**: `policies/default_policy.json`

### 3.1 策略文件结构

**文件**: `policies/default_policy.json`

```json
{
  "version": "1.0",
  "name": "默认安全策略",
  "description": "适用于教育场景的默认安全策略，平衡安全性与功能性",
  "last_updated": "2026-04-13",
  
  "dangerous_functions": {
    "critical": [
      "system",
      "popen",
      "exec",
      "fork",
      "vfork",
      "rmdir",
      "unlink",
      "chmod",
      "kill",
      "abort",
      "exit"
    ],
    "warning": [
      "socket",
      "connect",
      "bind",
      "mmap",
      "mprotect"
    ]
  },
  
  "patterns": [
    {
      "id": "P001",
      "pattern": "system\\s*\\(",
      "description": "直接调用 system() 函数",
      "severity": "critical",
      "blocking": true,
      "recommendation": "使用更安全的替代方案，或通过沙箱执行"
    },
    {
      "id": "P002",
      "pattern": "gets\\s*\\(",
      "description": "gets() 已从 C11 移除，存在严重缓冲区溢出风险",
      "severity": "critical",
      "blocking": true,
      "recommendation": "使用 fgets(buf, sizeof(buf), stdin) 替代"
    },
    {
      "id": "P003",
      "pattern": "strcpy\\s*\\(",
      "description": "strcpy() 不检查目标缓冲区大小",
      "severity": "warning",
      "blocking": false,
      "recommendation": "使用 strncpy() 或安全字符串库"
    },
    {
      "id": "P004",
      "pattern": "sprintf\\s*\\(",
      "description": "sprintf() 存在格式化字符串漏洞风险",
      "severity": "warning",
      "blocking": false,
      "recommendation": "使用 snprintf() 替代"
    },
    {
      "id": "P005",
      "pattern": "scanf\\s*\\(\\s*\"%s\"",
      "description": "scanf %s 不限制输入长度，可能导致缓冲区溢出",
      "severity": "warning",
      "blocking": false,
      "recommendation": "使用宽度说明符，如 %99s（假设缓冲区为 100 字节）"
    },
    {
      "id": "P006",
      "pattern": "rand\\s*\\(",
      "description": "rand() 不适合安全敏感的随机数需求",
      "severity": "info",
      "blocking": false,
      "recommendation": "如需安全随机数，使用 arc4random() 或 getrandom()"
    }
  ],
  
  "network_policy": {
    "allow_outgoing": false,
    "allow_incoming": false,
    "allowed_ports": [],
    "blocked_hosts": ["*"]
  },
  
  "file_policy": {
    "allowed_paths": ["/tmp/zhc_sandbox/"],
    "blocked_paths": [
      "/etc/",
      "/root/",
      "/home/*/",
      "/var/",
      "/sys/",
      "/proc/"
    ],
    "max_file_size": 10485760,
    "allow_network_file_access": false
  },
  
  "process_policy": {
    "allow_fork": false,
    "allow_exec": false,
    "max_processes": 1
  },
  
  "memory_policy": {
    "max_heap_size": 104857600,
    "check_uninitialized": true,
    "check_buffer_overflow": true,
    "check_null_dereference": true
  }
}
```

### 3.2 策略文件加载器

**文件**: `src/ai/policy_loader.cpp`

```cpp
#include <fstream>
#include <nlohmann/json.hpp>
#include "zhc_security_policy.h"

using json = nlohmann::json;

namespace zhc {
namespace ai {

class PolicyLoader {
public:
    static bool LoadPolicy(SecurityPolicy& Policy, const std::string& Path) {
        std::ifstream File(Path);
        if (!File.is_open()) {
            std::cerr << "Failed to open policy file: " << Path << std::endl;
            return false;
        }
        
        try {
            json Data = json::parse(File);
            
            // 加载危险函数
            if (Data.contains("dangerous_functions")) {
                auto& DF = Data["dangerous_functions"];
                if (DF.contains("critical")) {
                    for (const auto& Func : DF["critical"]) {
                        Policy.AddDangerousFunction(Func.get<std::string>(), 
                                                     DangerLevel::Critical);
                    }
                }
                if (DF.contains("warning")) {
                    for (const auto& Func : DF["warning"]) {
                        Policy.AddDangerousFunction(Func.get<std::string>(), 
                                                     DangerLevel::Warning);
                    }
                }
            }
            
            // 加载模式规则
            if (Data.contains("patterns")) {
                for (const auto& P : Data["patterns"]) {
                    PolicyRule Rule;
                    Rule.Pattern = P["pattern"];
                    Rule.Description = P["description"];
                    Rule.Level = ParseSeverity(P["severity"]);
                    Rule.IsBlocking = P.value("blocking", false);
                    Rule.Recommendation = P.value("recommendation", "");
                    Policy.AddRule(Rule);
                }
            }
            
            return true;
        } catch (const json::parse_error& e) {
            std::cerr << "JSON parse error: " << e.what() << std::endl;
            return false;
        }
    }
    
private:
    static DangerLevel ParseSeverity(const std::string& S) {
        if (S == "critical") return DangerLevel::Critical;
        if (S == "warning") return DangerLevel::Warning;
        return DangerLevel::Safe;
    }
};

} // namespace ai
} // namespace zhc
```

### 3.3 验收标准

```bash
# 测试 1：策略文件存在且格式正确
ls -la policies/default_policy.json
# 期望：文件存在，大小 > 1KB

# 测试 2：JSON 格式验证
python3 -c "import json; json.load(open('policies/default_policy.json'))"
# 期望：无错误

# 测试 3：策略加载
./build/bin/zhc_security_test --load policies/default_policy.json
# 期望：Loaded 6 patterns, 11 critical functions, 5 warning functions

# 测试 4：策略更新
./build/bin/zhc_security_test --update-policy policies/default_policy.json
# 期望：Policy updated successfully
```

---

## T5.4：AI 幻觉检测器

**工时**: 48h  
**依赖**: T5.1、T5.3  
**交付物**: `zhc_hallucination_detector.cpp`

### 4.1 头文件设计

**文件**: `include/zhc/ai/zhc_hallucination_detector.h`

```cpp
#pragma once

#include <string>
#include <vector>
#include <memory>
#include <unordered_map>

namespace zhc {
namespace ai {

// 幻觉检测结果
struct HallucinationResult {
    bool IsHighRisk;          // 是否高风险
    float Confidence;          // 置信度 0.0-1.0
    std::vector<std::string> Warnings;     // 警告信息
    std::vector<std::string> SuspiciousPatterns;  // 可疑模式
    
    static HallucinationResult Safe() {
        return {false, 1.0f, {}, {}};
    }
    static HallucinationResult Risky(float confidence,
                                     const std::vector<std::string>& warnings,
                                     const std::vector<std::string>& patterns = {}) {
        return {confidence < 0.7f, confidence, warnings, patterns};
    }
};

// 可疑代码模式
struct SuspiciousPattern {
    std::string Name;         // 模式名称
    std::string Regex;        // 匹配正则
    std::string Explanation;  // 解释
    float RiskWeight;          // 风险权重 0.0-1.0
};

// 幻觉检测器
class HallucinationDetector {
public:
    HallucinationDetector(std::shared_ptr<BuiltinKnowledge> Knowledge);
    
    // 检测 AI 生成的代码
    HallucinationResult Detect(const MonitoredAIRequest& Request);
    
    // 检测未知函数调用
    std::vector<std::string> DetectUnknownFunctions(const std::string& Code);
    
    // 检测不匹配的内存操作
    std::vector<std::string> DetectMemoryMismatch(const std::string& Code);
    
    // 检测不存在的库函数
    std::vector<std::string> DetectFakeLibraries(const std::string& Code);
    
    // 设置内置知识库
    void SetBuiltinKnowledge(std::shared_ptr<BuiltinKnowledge> Knowledge);
    
    // 添加自定义模式
    void AddPattern(const SuspiciousPattern& Pattern);
    
    // 训练数据反馈（用于后续改进）
    void ReportFalsePositive(const std::string& Code);
    void ReportTruePositive(const std::string& Code, const std::string& Issue);

private:
    std::shared_ptr<BuiltinKnowledge> Knowledge_;
    std::vector<SuspiciousPattern> Patterns_;
    
    float CalculateRiskScore(const std::string& Code);
    bool IsKnownFunction(const std::string& FuncName);
    bool IsFakeLibrary(const std::string& LibName);
    
    // 统计（用于自适应）
    std::unordered_map<std::string, int> PatternFrequency_;
};

} // namespace ai
} // namespace zhc
```

### 4.2 实现文件

**文件**: `src/ai/zhc_hallucination_detector.cpp`

**关键实现逻辑**:

```cpp
#include "zhc_hallucination_detector.h"
#include "builtin_knowledge.h"
#include <regex>
#include <algorithm>

namespace zhc {
namespace ai {

HallucinationDetector::HallucinationDetector(std::shared_ptr<BuiltinKnowledge> Knowledge)
    : Knowledge_(Knowledge) {
    // 初始化可疑模式库
    Patterns_ = {
        // 模式 1：不存在或不安全的库函数
        {"fake_func", R"(\bgets_s\s*\()", 
         "gets_s() 不是标准 C 函数，可能是 AI 虚构", 0.9f},
        
        // 模式 2：错误的参数数量
        {"wrong_args", R"(\bmalloc\s*\([^)]+\))",
         "malloc 可能参数不正确", 0.3f},
        
        // 模式 3：可疑的宏定义
        {"suspicious_macro", R"(#define\s+\w+\s+\d+L?)",
         "检测到硬编码长整型常量，可能应为更明确的类型", 0.2f},
        
        // 模式 4：可能不存在的系统调用
        {"fake_syscall", R"(\bsys_\w+\s*\()",
         "检测到系统调用，可能是虚构的", 0.7f},
        
        // 模式 5：注释中包含可疑信息
        {"suspicious_comment", R"(//.*\b(TODO|FIXME|HACK|XXX)\b.*)",
         "代码包含未完成标记", 0.1f},
    };
}

HallucinationResult HallucinationDetector::Detect(const MonitoredAIRequest& Request) {
    std::vector<std::string> Warnings;
    std::vector<std::string> SuspiciousPatterns;
    
    const std::string& Code = Request.GeneratedCode;
    
    // 1. 检测未知函数调用
    auto UnknownFuncs = DetectUnknownFunctions(Code);
    if (!UnknownFuncs.empty()) {
        Warnings.push_back("发现 " + std::to_string(UnknownFuncs.size()) + 
                          " 个未知函数调用");
        SuspiciousPatterns.insert(SuspiciousPatterns.end(), 
                                  UnknownFuncs.begin(), UnknownFuncs.end());
    }
    
    // 2. 检测内存不匹配
    auto MemIssues = DetectMemoryMismatch(Code);
    if (!MemIssues.empty()) {
        Warnings.push_back("发现内存管理问题");
        SuspiciousPatterns.insert(SuspiciousPatterns.end(),
                                  MemIssues.begin(), MemIssues.end());
    }
    
    // 3. 检测虚假库函数
    auto FakeLibs = DetectFakeLibraries(Code);
    if (!FakeLibs.empty()) {
        Warnings.push_back("发现可能的虚假库函数: " + 
                          FakeLibs[0]);
        SuspiciousPatterns.insert(SuspiciousPatterns.end(),
                                  FakeLibs.begin(), FakeLibs.end());
    }
    
    // 4. 模式匹配
    for (const auto& Pattern : Patterns_) {
        std::regex Regex(Pattern.Regex);
        if (std::regex_search(Code, Regex)) {
            Warnings.push_back(Pattern.Explanation);
            SuspiciousPatterns.push_back(Pattern.Name);
            PatternFrequency_[Pattern.Name]++;
        }
    }
    
    // 计算风险评分
    float RiskScore = CalculateRiskScore(Code);
    float Confidence = 1.0f - RiskScore;
    
    if (!Warnings.empty() || RiskScore > 0.3f) {
        return HallucinationResult::Risky(Confidence, Warnings, SuspiciousPatterns);
    }
    return HallucinationResult::Safe();
}

std::vector<std::string> HallucinationDetector::DetectUnknownFunctions(
    const std::string& Code) {
    std::vector<std::string> UnknownFuncs;
    
    // 提取函数调用
    std::regex FuncPattern(R"(\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\()");
    std::smatch Match;
    std::string::const_iterator Start(Code.cbegin());
    
    while (std::regex_search(Start, Code.cend(), Match, FuncPattern)) {
        std::string FuncName = Match[1].str();
        
        // 跳过关键字和已知函数
        if (!IsKnownFunction(FuncName) && 
            !Knowledge_->IsKnownSafe(FuncName)) {
            UnknownFuncs.push_back(FuncName);
        }
        Start = Match.suffix().first;
    }
    
    // 去重
    std::sort(UnknownFuncs.begin(), UnknownFuncs.end());
    UnknownFuncs.erase(std::unique(UnknownFuncs.begin(), UnknownFuncs.end()), 
                       UnknownFuncs.end());
    
    return UnknownFuncs;
}

bool HallucinationDetector::IsKnownFunction(const std::string& FuncName) {
    // 标准库函数列表
    static const std::unordered_set<std::string> KnownFuncs = {
        "printf", "scanf", "fprintf", "fscanf", "sprintf", "sscanf",
        "malloc", "calloc", "realloc", "free",
        "memcpy", "memmove", "memset", "memcmp", "memchr",
        "strcpy", "strncpy", "strcat", "strncat", "strlen", "strcmp",
        "strncmp", "strchr", "strrchr", "strstr",
        "fopen", "fclose", "fread", "fwrite", "fseek", "ftell", "rewind",
        "exit", "abort", "getenv", "setenv",
        // ZHC 特有函数
        "打印", "输入", "如果", "否则", "当", "对于", "函数"
    };
    return KnownFuncs.find(FuncName) != KnownFuncs.end();
}

float HallucinationDetector::CalculateRiskScore(const std::string& Code) {
    float Score = 0.0f;
    
    // 未知函数越多，风险越高
    auto Unknowns = DetectUnknownFunctions(Code);
    Score += Unknowns.size() * 0.1f;
    
    // 可疑模式越多，风险越高
    for (const auto& Pattern : Patterns_) {
        std::regex Regex(Pattern.Regex);
        if (std::regex_search(Code, Regex)) {
            Score += Pattern.RiskWeight * 0.2f;
        }
    }
    
    // 代码过长风险增加
    if (Code.size() > 10000) {
        Score += 0.2f;
    }
    
    return std::min(Score, 1.0f);
}

} // namespace ai
} // namespace zhc
```

### 4.3 验收标准

```bash
# 测试 1：已知安全函数（应返回 Safe）
echo 'printf("hello");' | ./build/bin/zhc_hallucination_test --check
# 期望：Confidence: 1.0, Warnings: 0

# 测试 2：未知函数（应警告）
echo 'unknown_func();' | ./build/bin/zhc_hallucination_test --check
# 期望：Confidence: 0.7, Warnings: ["发现未知函数调用"]

# 测试 3：虚假库函数检测
echo 'gets_s(buf);' | ./build/bin/zhc_hallucination_test --check
# 期望：Detected fake_func pattern

# 测试 4：内存不匹配
echo 'malloc(100);' | ./build/bin/zhc_hallucination_test --check
# 期望：Warnings about memory management
```

---

## T5.5：内置知识库

**工时**: 16h  
**依赖**: T5.4  
**交付物**: `builtin_knowledge.cpp/h`

### 5.1 头文件设计

**文件**: `include/zhc/ai/builtin_knowledge.h`

```cpp
#pragma once

#include <string>
#include <vector>
#include <unordered_map>
#include <unordered_set>

namespace zhc {
namespace ai {

// 函数签名
struct FunctionSignature {
    std::string Name;
    std::string ReturnType;
    std::vector<std::string> ArgTypes;
    bool IsVariadic;         // 是否可变参数
    bool IsSafe;              // 是否安全
    std::string SafetyNote;   // 安全说明
    std::string Description;  // 功能描述
};

// 标准库信息
struct LibraryInfo {
    std::string Name;
    std::string Version;
    std::unordered_set<std::string> Functions;
    std::string Description;
};

// 内置知识库
class BuiltinKnowledge {
public:
    BuiltinKnowledge();
    
    // 查询函数是否已知安全
    bool IsKnownSafe(const std::string& FuncName) const;
    
    // 获取函数签名
    const FunctionSignature* GetSignature(const std::string& FuncName) const;
    
    // 获取函数安全说明
    std::string GetSafetyNote(const std::string& FuncName) const;
    
    // 检查参数数量是否正确
    bool CheckArgCount(const std::string& FuncName, size_t ActualCount) const;
    
    // 获取库信息
    const LibraryInfo* GetLibrary(const std::string& LibName) const;
    
    // 获取所有已知函数
    std::vector<std::string> GetAllKnownFunctions() const;
    
    // 获取安全函数列表
    std::vector<std::string> GetSafeFunctions() const;

private:
    void LoadStandardLibrary();
    void LoadZHCLibrary();
    
    std::unordered_map<std::string, FunctionSignature> Signatures_;
    std::unordered_map<std::string, LibraryInfo> Libraries_;
    std::unordered_set<std::string> SafeFunctions_;
};

} // namespace ai
} // namespace zhc
```

### 5.2 实现文件

**文件**: `src/ai/builtin_knowledge.cpp`

```cpp
#include "builtin_knowledge.h"

namespace zhc {
namespace ai {

BuiltinKnowledge::BuiltinKnowledge() {
    LoadStandardLibrary();
    LoadZHCLibrary();
}

void BuiltinKnowledge::LoadStandardLibrary() {
    // === stdio.h ===
    LibraryInfo StdIO{"stdio.h", "C89", {}, "标准输入输出库"};
    std::vector<FunctionSignature> StdIOSignatures = {
        {"printf", "int", {"const char*"}, false, true, 
         "安全：格式化输出",
         "格式化打印到标准输出"},
        {"scanf", "int", {"const char*"}, true, false,
         "警告：%s 不限制长度，应使用 fgets + sscanf",
         "从标准输入格式化读取"},
        {"fprintf", "int", {"FILE*", "const char*"}, true, true,
         "安全：文件格式化输出",
         "格式化打印到文件"},
        {"fscanf", "int", {"FILE*", "const char*"}, true, false,
         "警告：%s 不限制长度",
         "从文件格式化读取"},
        {"fopen", "FILE*", {"const char*", "const char*"}, false, true,
         "安全：文件操作",
         "打开文件"},
        {"fclose", "int", {"FILE*"}, false, true,
         "安全：关闭文件句柄",
         "关闭文件"},
        {"fread", "size_t", {"void*", "size_t", "size_t", "FILE*"}, false, true,
         "安全：二进制读取",
         "从文件读取数据块"},
        {"fwrite", "size_t", {"const void*", "size_t", "size_t", "FILE*"}, false, true,
         "安全：二进制写入",
         "向文件写入数据块"},
        {"sprintf", "int", {"char*", "const char*"}, true, false,
         "警告：目标缓冲区可能溢出，应使用 snprintf",
         "字符串格式化"},
        {"snprintf", "int", {"char*", "size_t", "const char*"}, true, true,
         "安全：带长度限制的格式化",
         "安全字符串格式化"},
        {"gets", "char*", {"char*"}, false, false,
         "危险：已废弃，不检查边界，C11 移除",
         "读取字符串（危险，不推荐）"},
    };
    for (const auto& Sig : StdIOSignatures) {
        Signatures_[Sig.Name] = Sig;
        if (Sig.IsSafe) SafeFunctions_.insert(Sig.Name);
    }
    StdIO.Functions = {"printf", "scanf", "fprintf", "fscanf", "fopen", 
                       "fclose", "fread", "fwrite", "sprintf", "snprintf"};
    Libraries_["stdio.h"] = StdIO;
    
    // === stdlib.h ===
    LibraryInfo StdLib{"stdlib.h", "C89", {}, "标准库"};
    std::vector<FunctionSignature> StdLibSignatures = {
        {"malloc", "void*", {"size_t"}, false, false,
         "注意：需检查返回值，可能返回 NULL",
         "动态内存分配"},
        {"calloc", "void*", {"size_t", "size_t"}, false, true,
         "安全：分配并初始化为 0",
         "分配并清零内存"},
        {"realloc", "void*", {"void*", "size_t"}, false, false,
         "注意：可能移动内存块，原指针需更新",
         "重新分配内存"},
        {"free", "void", {"void*"}, false, true,
         "安全：释放内存（需确保非空、非重复释放",
         "释放动态内存"},
        {"exit", "void", {"int"}, false, false,
         "警告：立即终止程序",
         "正常程序终止"},
        {"abort", "void", {}, false, false,
         "危险：异常程序终止",
         "异常程序终止"},
        {"atexit", "int", {"void(*)()"}, false, true,
         "安全：注册退出处理函数",
         "注册退出回调"},
        {"getenv", "char*", {"const char*"}, false, true,
         "安全：获取环境变量",
         "获取环境变量"},
    };
    for (const auto& Sig : StdLibSignatures) {
        Signatures_[Sig.Name] = Sig;
        if (Sig.IsSafe) SafeFunctions_.insert(Sig.Name);
    }
    StdLib.Functions = {"malloc", "calloc", "realloc", "free", 
                       "exit", "abort", "atexit", "getenv"};
    Libraries_["stdlib.h"] = StdLib;
    
    // === string.h ===
    LibraryInfo String{"string.h", "C89", {}, "字符串库"};
    std::vector<FunctionSignature> StringSignatures = {
        {"strlen", "size_t", {"const char*"}, false, true,
         "安全：返回字符串长度",
         "获取字符串长度"},
        {"strcpy", "char*", {"char*", "const char*"}, false, false,
         "危险：不检查目标缓冲区大小，可能溢出",
         "复制字符串（危险）"},
        {"strncpy", "char*", {"char*", "const char*", "size_t"}, false, false,
         "警告：可能不添加终止符",
         "复制指定长度字符串"},
        {"strcmp", "int", {"const char*", "const char*"}, false, true,
         "安全：比较字符串",
         "比较字符串"},
        {"strncmp", "int", {"const char*", "const char*", "size_t"}, false, true,
         "安全：比较指定长度",
         "比较指定长度字符串"},
        {"strcat", "char*", {"char*", "const char*"}, false, false,
         "危险：不检查目标缓冲区",
         "连接字符串（危险）"},
        {"strncat", "char*", {"char*", "const char*", "size_t"}, false, true,
         "安全：限制连接长度",
         "安全连接字符串"},
        {"memcpy", "void*", {"void*", "const void*", "size_t"}, false, true,
         "安全：复制内存区域（非重叠）",
         "复制内存"},
        {"memmove", "void*", {"void*", "const void*", "size_t"}, false, true,
         "安全：复制内存（允许重叠）",
         "移动内存"},
        {"memset", "void*", {"void*", "int", "size_t"}, false, true,
         "安全：设置内存",
         "设置内存值"},
        {"memcmp", "int", {"const void*", "const void*", "size_t"}, false, true,
         "安全：比较内存",
         "比较内存"},
    };
    for (const auto& Sig : StringSignatures) {
        Signatures_[Sig.Name] = Sig;
        if (Sig.IsSafe) SafeFunctions_.insert(Sig.Name);
    }
    String.Functions = {"strlen", "strcpy", "strncpy", "strcmp", "strncmp",
                       "strcat", "strncat", "memcpy", "memmove", "memset"};
    Libraries_["string.h"] = String;
}

void BuiltinKnowledge::LoadZHCLibrary() {
    // ZHC 标准库函数
    std::vector<FunctionSignature> ZHCSignatures = {
        {"打印", "void", {"const char*"}, false, true,
         "安全：输出字符串",
         "打印到控制台"},
        {"打印行", "void", {"const char*"}, false, true,
         "安全：输出并换行",
         "打印一行"},
        {"输入", "整数型", {}, false, false,
         "注意：需检查 EOF 返回值",
         "从控制台读取整数"},
        {"输入行", "字符串型", {}, false, true,
         "安全：读取一行文本",
         "读取一行输入"},
        {"申请内存", "指针型", {"整数型"}, false, false,
         "注意：需检查返回值",
         "申请动态内存"},
        {"释放内存", "void", {"指针型"}, false, true,
         "安全：释放内存",
         "释放动态内存"},
        {"打开文件", "文件型", {"字符串型", "字符串型"}, false, true,
         "安全：打开文件",
         "打开文件"},
        {"关闭文件", "void", {"文件型"}, false, true,
         "安全：关闭文件",
         "关闭文件"},
        {"读取文件", "整数型", {"文件型", "指针型", "整数型"}, false, true,
         "安全：读取文件数据",
         "读取文件"},
        {"写入文件", "整数型", {"文件型", "指针型", "整数型"}, false, true,
         "安全：写入文件数据",
         "写入文件"},
    };
    for (const auto& Sig : ZHCSignatures) {
        Signatures_[Sig.Name] = Sig;
        SafeFunctions_.insert(Sig.Name);
    }
}

bool BuiltinKnowledge::IsKnownSafe(const std::string& FuncName) const {
    return SafeFunctions_.find(FuncName) != SafeFunctions_.end();
}

const FunctionSignature* BuiltinKnowledge::GetSignature(
    const std::string& FuncName) const {
    auto It = Signatures_.find(FuncName);
    if (It != Signatures_.end()) {
        return &It->second;
    }
    return nullptr;
}

std::string BuiltinKnowledge::GetSafetyNote(const std::string& FuncName) const {
    auto* Sig = GetSignature(FuncName);
    if (Sig) {
        return Sig->SafetyNote;
    }
    return "未知函数，请手动确认安全性";
}

std::vector<std::string> BuiltinKnowledge::GetSafeFunctions() const {
    return std::vector<std::string>(SafeFunctions_.begin(), SafeFunctions_.end());
}

} // namespace ai
} // namespace zhc
```

### 5.3 验收标准

```bash
# 测试 1：已知安全函数
./build/bin/zhc_builtin_test --check-safe printf
# 期望：IsSafe: true

# 测试 2：危险函数
./build/bin/zhc_builtin_test --check-safe gets
# 期望：IsSafe: false, SafetyNote: "危险：已废弃"

# 测试 3：获取签名
./build/bin/zhc_builtin_test --signature malloc
# 期望：ReturnType: void*, Args: [size_t], Safe: false

# 测试 4：参数数量检查
./build/bin/zhc_builtin_test --check-args printf 1
# 期望：Valid: true
./build/bin/zhc_builtin_test --check-args malloc 0
# 期望：Valid: false (malloc requires 1 arg)
```

---

## T5.6：沙箱执行器

**工时**: 56h  
**依赖**: T5.1  
**交付物**: `zhc_sandbox_executor.cpp`

### 6.1 头文件设计

**文件**: `include/zhc/ai/zhc_sandbox_executor.h`

```cpp
#pragma once

#include <string>
#include <vector>
#include <memory>
#include <chrono>
#include <future>

namespace zhc {
namespace ai {

// 执行结果
struct ExecutionResult {
    bool Success;
    int ExitCode;
    std::chrono::milliseconds ExecutionTime;
    std::string Stdout;
    std::string Stderr;
    std::vector<std::string> Violations;  // 违反的策略
    
    static ExecutionResult SuccessResult(int exit_code, 
                                         const std::string& stdout,
                                         const std::chrono::milliseconds& time) {
        return {true, exit_code, time, stdout, "", {}};
    }
    static ExecutionResult FailureResult(const std::string& stderr,
                                         const std::vector<std::string>& violations) {
        return {false, -1, {}, "", stderr, violations};
    }
};

// 沙箱配置
struct SandboxConfig {
    std::string WorkingDirectory = "/tmp/zhc_sandbox/";
    size_t MaxMemoryMB = 100;           // 最大内存 MB
    size_t MaxTimeMs = 5000;            // 最大执行时间 ms
    size_t MaxFileSizeKB = 10240;       // 最大文件大小 KB
    bool EnableNetwork = false;         // 是否允许网络
    bool AllowFork = false;             // 是否允许 fork
    bool AllowExec = false;             // 是否允许 exec
    std::vector<std::string> AllowedPaths;   // 允许的路径
    std::vector<std::string> BlockedPaths;  // 禁止的路径
};

// 沙箱执行器
class SandboxExecutor {
public:
    explicit SandboxExecutor(const SandboxConfig& Config);
    ~SandboxExecutor();
    
    // 禁用拷贝
    SandboxExecutor(const SandboxExecutor&) = delete;
    SandboxExecutor& operator=(const SandboxExecutor&) = delete;
    
    // 在沙箱中执行代码
    ExecutionResult Execute(const std::string& Code, 
                           const std::string& SourceFile);
    
    // 异步执行
    std::future<ExecutionResult> ExecuteAsync(const std::string& Code,
                                               const std::string& SourceFile);
    
    // 执行预编译的二进制
    ExecutionResult ExecuteBinary(const std::string& BinaryPath,
                                  const std::vector<std::string>& Args);
    
    // 设置工作目录
    void SetWorkingDirectory(const std::string& Path);
    
    // 获取配置
    const SandboxConfig& GetConfig() const;

private:
    bool SetupSandbox();
    bool TeardownSandbox();
    ExecutionResult RunWithLimits(pid_t Pid);
    
    SandboxConfig Config_;
    bool IsSetup_ = false;
    std::string SandboxDir_;
};

} // namespace ai
} // namespace zhc
```

### 6.2 实现文件

**文件**: `src/ai/zhc_sandbox_executor.cpp`

```cpp
#include "zhc_sandbox_executor.h"
#include <sys/wait.h>
#include <sys/resource.h>
#include <sys/prctl.h>
#include <unistd.h>
#include <fstream>
#include <sstream>
#include <random>
#include <chrono>

namespace zhc {
namespace ai {

SandboxExecutor::SandboxExecutor(const SandboxConfig& Config)
    : Config_(Config) {
    // 创建临时沙箱目录
    std::random_device Rd;
    std::mt19937 Gen(Rd());
    std::uniform_int_distribution<> Dis(10000, 99999);
    
    SandboxDir_ = Config_.WorkingDirectory + "zhc_sandbox_" + 
                  std::to_string(Dis(Gen)) + "/";
}

SandboxExecutor::~SandboxExecutor() {
    TeardownSandbox();
}

ExecutionResult SandboxExecutor::Execute(const std::string& Code,
                                         const std::string& SourceFile) {
    // 1. 创建沙箱环境
    if (!SetupSandbox()) {
        return ExecutionResult::FailureResult("Failed to setup sandbox", 
                                               {"Sandbox setup failed"});
    }
    
    // 2. 写入源代码
    std::string SourcePath = SandboxDir_ + SourceFile;
    std::ofstream OutFile(SourcePath);
    if (!OutFile) {
        return ExecutionResult::FailureResult("Failed to write source file",
                                               {"File write failed"});
    }
    OutFile << Code;
    OutFile.close();
    
    // 3. 编译（使用 ZHC 编译器）
    std::string BinaryPath = SandboxDir_ + "a.out";
    int CompileResult = system(("zhc compile " + SourcePath + " -o " + 
                               BinaryPath).c_str());
    if (CompileResult != 0) {
        std::string Stderr = "Compilation failed";
        return ExecutionResult::FailureResult(Stderr, {"Compilation error"});
    }
    
    // 4. 执行
    return ExecuteBinary(BinaryPath, {});
}

std::future<ExecutionResult> SandboxExecutor::ExecuteAsync(
    const std::string& Code, const std::string& SourceFile) {
    return std::async(std::launch::async, 
        [this](const std::string& C, const std::string& F) {
            return this->Execute(C, F);
        }, Code, SourceFile);
}

ExecutionResult SandboxExecutor::ExecuteBinary(const std::string& BinaryPath,
                                               const std::vector<std::string>& Args) {
    auto StartTime = std::chrono::steady_clock::now();
    
    pid_t Pid = fork();
    if (Pid < 0) {
        return ExecutionResult::FailureResult("fork() failed", {"Fork error"});
    }
    
    if (Pid == 0) {
        // 子进程
        
        // 设置资源限制
        struct rlimit Rl;
        Rl.rlim_cur = Config_.MaxMemoryMB * 1024 * 1024;
        Rl.rlim_max = Config_.MaxMemoryMB * 1024 * 1024;
        setrlimit(RLIMIT_AS, &Rl);
        
        Rl.rlim_cur = Config_.MaxTimeMs / 1000;
        Rl.rlim_max = Config_.MaxTimeMs / 1000;
        setrlimit(RLIMIT_CPU, &Rl);
        
        // 设置工作目录
        if (chdir(SandboxDir_.c_str()) != 0) {
            _exit(1);
        }
        
        // 限制文件访问
        if (chroot(SandboxDir_.c_str()) != 0) {
            // chroot 可能失败，使用路径检查替代
        }
        
        // 重定向输入输出
        freopen("/dev/null", "r", stdin);
        freopen((SandboxDir_ + "stdout.txt").c_str(), "w", stdout);
        freopen((SandboxDir_ + "stderr.txt").c_str(), "w", stderr);
        
        // 执行
        std::vector<char*> ArgsVec;
        ArgsVec.push_back(const_cast<char*>(BinaryPath.c_str()));
        for (const auto& A : Args) {
            ArgsVec.push_back(const_cast<char*>(A.c_str()));
        }
        ArgsVec.push_back(nullptr);
        
        execv(BinaryPath.c_str(), ArgsVec.data());
        _exit(127);  // exec 失败
    }
    
    // 父进程
    return RunWithLimits(Pid);
}

ExecutionResult SandboxExecutor::RunWithLimits(pid_t Pid) {
    int Status;
    struct rusage Usage;
    
    auto StartTime = std::chrono::steady_clock::now();
    
    // 等待子进程，设置超时
    while (true) {
        int Result = wait4(Pid, &Status, WNOHANG, &Usage);
        
        if (Result == 0) {
            // 还在运行，检查超时
            auto Elapsed = std::chrono::steady_clock::now() - StartTime;
            if (std::chrono::duration_cast<std::chrono::milliseconds>(
                    Elapsed).count() > Config_.MaxTimeMs) {
                // 超时，杀死进程
                kill(Pid, SIGKILL);
                wait4(Pid, &Status, 0, &Usage);
                return ExecutionResult::FailureResult("Execution timeout",
                                                      {"Execution timeout"});
            }
            usleep(10000);  // 10ms
            continue;
        }
        
        if (Result < 0) {
            return ExecutionResult::FailureResult("wait4() failed",
                                                  {"Wait error"});
        }
        
        // 子进程结束
        auto ExecTime = std::chrono::milliseconds(
            Usage.ru_utime.tv_sec * 1000 + Usage.ru_utime.tv_usec / 1000);
        
        // 读取输出
        std::string Stdout, Stderr;
        std::ifstream StdoutFile(SandboxDir_ + "stdout.txt");
        if (StdoutFile) {
            std::ostringstream Ss;
            Ss << StdoutFile.rdbuf();
            Stdout = Ss.str();
        }
        std::ifstream StderrFile(SandboxDir_ + "stderr.txt");
        if (StderrFile) {
            std::ostringstream Ss;
            Ss << StderrFile.rdbuf();
            Stderr = Ss.str();
        }
        
        if (WIFEXITED(Status)) {
            return ExecutionResult::SuccessResult(WEXITSTATUS(Status),
                                                  Stdout, ExecTime);
        } else if (WIFSIGNALED(Status)) {
            return ExecutionResult::FailureResult(
                "Terminated by signal: " + std::to_string(WTERMSIG(Status)),
                {"Process killed"});
        }
        
        return ExecutionResult::FailureResult("Unknown exit status", {});
    }
}

bool SandboxExecutor::SetupSandbox() {
    if (IsSetup_) return true;
    
    // 创建目录
    if (mkdir(SandboxDir_.c_str(), 0755) != 0) {
        return false;
    }
    
    // 创建必要的子目录
    mkdir((SandboxDir_ + "tmp").c_str(), 1777);
    
    IsSetup_ = true;
    return true;
}

bool SandboxExecutor::TeardownSandbox() {
    if (!IsSetup_) return true;
    
    // 删除沙箱目录（递归删除）
    std::string Cmd = "rm -rf " + SandboxDir_;
    system(Cmd.c_str());
    
    IsSetup_ = false;
    return true;
}

} // namespace ai
} // namespace zhc
```

### 6.3 验收标准

```bash
# 测试 1：安全代码执行
echo '打印行("Hello");' | ./build/bin/zhc_sandbox_test --execute
# 期望：Success: true, ExitCode: 0

# 测试 2：危险代码阻止（需配合策略引擎）
echo 'system("rm -rf /");' | ./build/bin/zhc_sandbox_test --execute
# 期望：Success: false, Violations: ["dangerous system call"]

# 测试 3：超时检测
echo '当(真) { 打印行("infinite loop"); }' | ./build/bin/zhc_sandbox_test --execute
# 期望：Success: false, Violations: ["Execution timeout"]

# 测试 4：内存限制
./build/bin/zhc_sandbox_test --memory-limit 10 --execute large_alloc.zhc
# 期望：Success: false, Violations: ["Memory limit exceeded"]

# 测试 5：沙箱隔离验证
./build/bin/zhc_sandbox_test --verify-isolation
# 期望：Can only access sandbox directory
```

---

## T5.7：内存安全分析

**工时**: 32h  
**依赖**: T5.2  
**交付物**: `zhc_memory_safety.cpp`

### 7.1 功能说明

静态分析 AI 生成的代码，检测潜在的内存安全问题：
- 内存泄漏（malloc/free 配对）
- 缓冲区溢出
- 空指针解引用
- 双重释放
- 未初始化使用

### 7.2 头文件设计

**文件**: `include/zhc/ai/zhc_memory_safety.h`

```cpp
#pragma once

#include <string>
#include <vector>
#include <unordered_map>
#include <unordered_set>

namespace zhc {
namespace ai {

// 内存安全问题
struct MemoryIssue {
    std::string Type;      // "leak", "overflow", "null_deref", "double_free", "uninit"
    int Line;
    std::string Variable;
    std::string Description;
    float Severity;        // 0.0-1.0
};

// 内存追踪信息
struct MemoryInfo {
    std::string Variable;
    int AllocationLine;
    std::string AllocationFunc;  // "malloc", "calloc", "new"
    bool IsFreed;
    int FreeLine;
    std::string FreeFunc;
};

// 内存安全分析器
class MemorySafetyAnalyzer {
public:
    MemorySafetyAnalyzer();
    
    // 分析代码
    std::vector<MemoryIssue> Analyze(const std::string& Code);
    
    // 检查内存泄漏
    std::vector<MemoryIssue> CheckLeaks(const std::string& Code);
    
    // 检查缓冲区溢出
    std::vector<MemoryIssue> CheckOverflow(const std::string& Code);
    
    // 检查空指针
    std::vector<MemoryIssue> CheckNullDeref(const std::string& Code);

private:
    std::vector<MemoryInfo> TraceAllocations(const std::string& Code);
    std::vector<MemoryInfo> TraceFrees(const std::string& Code);
    
    std::string ExtractVariable(const std::string& Line);
    int FindLineNumber(const std::string& Code, const std::string& Pattern);
};

} // namespace ai
} // namespace zhc
```

### 7.3 验收标准

```bash
# 测试 1：内存泄漏检测
echo 'int* p = malloc(100);' | ./build/bin/zhc_memory_test --check-leaks
# 期望：Issue found: Memory leak at line 1

# 测试 2：无问题代码
echo 'int* p = malloc(100); free(p);' | ./build/bin/zhc_memory_test --check-leaks
# 期望：No issues found

# 测试 3：缓冲区溢出检测
echo 'char buf[10]; strcpy(buf, "this is longer than 10 chars");' | \
     ./build/bin/zhc_memory_test --check-overflow
# 期望：Issue found: Buffer overflow

# 测试 4：空指针检测
echo 'int* p = NULL; *p = 42;' | ./build/bin/zhc_memory_test --check-null
# 期望：Issue found: Null pointer dereference
```

---

## T5.8：系统调用过滤（Seccomp/eBPF）

**工时**: 24h  
**依赖**: T5.6  
**交付物**: `zhc_syscall_filter.cpp`

### 8.1 功能说明

使用 Linux seccomp-bpf 或 eBPF 限制 AI 生成代码可执行的系统调用。

### 8.2 关键实现

**文件**: `src/ai/zhc_syscall_filter.cpp`

```cpp
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <linux/seccomp.h>
#include <linux/filter.h>

namespace zhc {
namespace ai {

// 允许的系统调用
static const std::unordered_set<long> AllowedSyscalls = {
    // 文件操作
    SYS_read, SYS_write, SYS_open, SYS_close, SYS_fstat,
    // 内存
    SYS_mmap, SYS_mprotect, SYS_brk, SYS_munmap,
    // 进程
    SYS_exit, SYS_getpid, SYS_getuid,
    // 时间
    SYS_time, SYS_clock_gettime,
    // 套接字（有限）
    // SYS_socket, SYS_connect, SYS_accept,  // 默认禁止，除非开启网络
};

// 禁止的系统调用
static const std::unordered_set<long> BlockedSyscalls = {
    SYS_execve, SYS_fork, SYS_vfork, SYS_clone,
    SYS_kill, SYS_ptrace, SYS_syslog,
    SYS_mount, SYS_umount2,
    SYS_reboot, SYS_setuid, SYS_setgid,
    SYS_capset, SYS_ptrace,
};

// seccomp 过滤器安装
bool InstallSyscallFilter(bool AllowNetwork = false) {
    struct sock_filter Filter[] = {
        // 加载系统调用号
        BPF_STMT(BPF_LD + BPF_W + BPF_ABS, offsetof(struct seccomp_data, nr)),
        
        // 检查是否为允许列表中的调用
        BPF_JUMP(BPF_JMP + BPF_JEQ + BPF_K, SYS_read, 0, 1),
        BPF_STMT(BPF_RET + BPF_K, SECCOMP_RET_ALLOW),
        
        BPF_JUMP(BPF_JMP + BPF_JEQ + BPF_K, SYS_write, 0, 1),
        BPF_STMT(BPF_RET + BPF_K, SECCOMP_RET_ALLOW),
        
        // ... 其他允许的调用 ...
        
        // 默认拒绝
        BPF_STMT(BPF_RET + BPF_K, SECCOMP_RET_KILL),
    };
    
    struct sock_fprog Prog = {
        .len = (unsigned short)(sizeof(Filter) / sizeof(Filter[0])),
        .filter = Filter,
    };
    
    if (prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &Prog) != 0) {
        return false;
    }
    return true;
}

} // namespace ai
} // namespace zhc
```

### 8.3 验收标准

```bash
# 测试 1：安装过滤器
./build/bin/zhc_syscall_test --install-filter
# 期望：Filter installed successfully

# 测试 2：允许的调用
./build/bin/zhc_syscall_test --test-syscall read
# 期望：Allowed

# 测试 3：禁止的调用
./build/bin/zhc_syscall_test --test-syscall execve
# 期望：Blocked (SIGSYS)

# 测试 4：进程被杀死
./build/bin/zhc_syscall_test --test-dangerous
# 期望：Process killed by seccomp
```

---

## T5.9：告警日志系统

**工时**: 20h  
**依赖**: T5.1  
**交付物**: `zhc_alert_logger.cpp/h`

### 9.1 头文件设计

**文件**: `include/zhc/ai/zhc_alert_logger.h`

```cpp
#pragma once

#include <string>
#include <vector>
#include <memory>
#include <mutex>
#include <fstream>
#include <chrono>

namespace zhc {
namespace ai {

enum class AlertLevel {
    Info,       // 信息
    Warning,    // 警告
    Critical,   // 严重
    Blocked     // 已阻止
};

// 告警记录
struct AlertRecord {
    std::chrono::system_clock::time_point Timestamp;
    AlertLevel Level;
    std::string Source;           // 来源模块
    std::string Message;
    std::vector<std::string> Details;
    std::string CodeSnippet;      // 相关代码片段
};

// 告警日志器
class AlertLogger {
public:
    AlertLogger(const std::string& LogPath = "zhc_monitor.log");
    ~AlertLogger();
    
    // 记录告警
    void LogAlert(AlertLevel Level, const std::string& Source,
                  const std::vector<std::string>& Details = {},
                  const std::string& CodeSnippet = "");
    
    // 获取最近告警
    std::vector<AlertRecord> GetRecentAlerts(size_t Count = 100) const;
    
    // 获取特定级别的告警
    std::vector<AlertRecord> GetAlertsByLevel(AlertLevel Level) const;
    
    // 清空告警历史
    void ClearHistory();
    
    // 导出告警到 JSON
    std::string ExportToJSON() const;
    
    // 设置最小记录级别
    void SetMinLevel(AlertLevel Level);

private:
    void WriteToFile(const AlertRecord& Record);
    std::string FormatLevel(AlertLevel Level);
    AlertRecord ParseFromJSON(const std::string& JSON);
    
    std::string LogPath_;
    std::vector<AlertRecord> History_;
    mutable std::mutex Mutex_;
    AlertLevel MinLevel_ = AlertLevel::Info;
    std::ofstream FileStream_;
};

} // namespace ai
} // namespace zhc
```

### 9.2 验收标准

```bash
# 测试 1：记录告警
./build/bin/zhc_alert_test --log "危险操作" --level critical
# 期望：Alert logged successfully

# 测试 2：获取最近告警
./build/bin/zhc_alert_test --get-recent 10
# 期望：返回最近 10 条告警

# 测试 3：按级别过滤
./build/bin/zhc_alert_test --get-level critical
# 期望：返回所有严重告警

# 测试 4：导出 JSON
./build/bin/zhc_alert_test --export
# 期望：输出 JSON 格式告警记录
```

---

## T5.10：CLI 监控参数集成

**工时**: 12h  
**依赖**: T5.1-T5.9  
**交付物**: `zhc_cli.cpp` 修改

### 10.1 新增 CLI 参数

**文件**: `src/driver/zhc_cli.cpp`

```cpp
#include <iostream>
#include <string>

// === 新增监控参数 ===

// 启用 AI 监控
cl::opt<bool> EnableAIMonitor(
    "ai-monitor",
    cl::desc("启用 AI 可信执行监控（检查代码安全性和幻觉）"),
    cl::init(false));

// 监控级别
cl::opt<std::string> AIMonitorLevel(
    "ai-monitor-level",
    cl::desc("监控级别: off, warning, strict（默认: warning）"),
    cl::value_desc("level"),
    cl::init("warning"));

// 信任阈值
cl::opt<float> TrustThreshold(
    "ai-trust-threshold",
    cl::desc("信任评分阈值 0.0-1.0（低于此值阻止执行）"),
    cl::value_desc("threshold"),
    cl::init(0.7));

// 启用沙箱执行
cl::opt<bool> EnableSandbox(
    "ai-sandbox",
    cl::desc("在沙箱中执行 AI 生成的代码"),
    cl::init(false));

// 策略文件路径
cl::opt<std::string> PolicyFile(
    "ai-policy",
    cl::desc("指定安全策略 JSON 文件路径"),
    cl::value_desc("path"),
    cl::init("policies/default_policy.json"));

// 告警日志路径
cl::opt<std::string> AlertLogPath(
    "ai-alert-log",
    cl::desc("告警日志输出路径"),
    cl::value_desc("path"),
    cl::init("zhc_monitor.log"));

// === 监控初始化示例 ===

bool InitializeAIMonitor() {
    if (!EnableAIMonitor) {
        return true;  // 未启用，不需要初始化
    }
    
    // 解析监控级别
    MonitorLevel Level = MonitorLevel::Warning;
    if (AIMonitorLevel == "off") {
        Level = MonitorLevel::Off;
    } else if (AIMonitorLevel == "strict") {
        Level = MonitorLevel::Strict;
    }
    
    // 加载策略文件
    auto Policy = std::make_shared<SecurityPolicy>();
    if (!Policy->LoadFromFile(PolicyFile)) {
        std::cerr << "Warning: Failed to load policy file: " << PolicyFile << std::endl;
    }
    
    // 创建监控组件
    auto Hallucination = std::make_shared<HallucinationDetector>(BuiltinKnowledge);
    auto Sandbox = std::make_shared<SandboxExecutor>(SandboxConfig{});
    auto Logger = std::make_shared<AlertLogger>(AlertLogPath);
    
    // 创建监控管理器
    auto Monitor = std::make_shared<AIMonitorManager>(
        Policy, Hallucination, Sandbox, Logger);
    Monitor->SetMonitorLevel(Level);
    Monitor->SetTrustThreshold(TrustThreshold);
    
    // 设置全局实例
    GlobalAIMonitor = Monitor;
    
    std::cout << "AI Monitor initialized: level=" << AIMonitorLevel 
              << ", threshold=" << TrustThreshold << std::endl;
    
    return true;
}
```

### 10.2 验收标准

```bash
# 测试 1：帮助信息
zhc compile --help | grep -A2 "ai-monitor"
# 期望：显示 ai-monitor 参数说明

# 测试 2：启用监控（警告模式）
zhc compile ai_code.zhc -ai-monitor
# 期望：⚠️ 警告: 检测到未验证函数调用

# 测试 3：严格模式
zhc compile ai_code.zhc -ai-monitor-level=strict
# 期望：❌ 阻止执行：信任评分 0.45 < 0.70

# 测试 4：自定义策略
zhc compile ai_code.zhc -ai-monitor -ai-policy=my_policy.json
# 期望：Loaded 10 rules from my_policy.json

# 测试 5：沙箱执行
zhc compile ai_code.zhc -ai-sandbox
# 期望：Code executed in sandbox
```

---

## T5.11：集成测试

**工时**: 40h  
**依赖**: T5.1-T5.10  
**交付物**: `test/ai_monitor_test.cpp`

### 11.1 测试用例设计

**文件**: `test/ai_monitor_test.cpp`

```cpp
#include <gtest/gtest.h>
#include "zhc_ai_monitor.h"
#include "zhc_security_policy.h"
#include "zhc_hallucination_detector.h"
#include "zhc_sandbox_executor.h"

using namespace zhc::ai;

class AIMonitorIntegrationTest : public ::testing::Test {
protected:
    void SetUp() override {
        // 初始化测试环境
        Policy = std::make_shared<SecurityPolicy>();
        Hallucination = std::make_shared<HallucinationDetector>(BuiltinKnowledge);
        Sandbox = std::make_shared<SandboxExecutor>(SandboxConfig{});
        Logger = std::make_shared<AlertLogger>("/tmp/test_monitor.log");
        
        Monitor = std::make_shared<AIMonitorManager>(
            Policy, Hallucination, Sandbox, Logger);
        Monitor->SetMonitorLevel(MonitorLevel::Warning);
        Monitor->SetTrustThreshold(0.5f);
    }
    
    std::shared_ptr<AIMonitorManager> Monitor;
    std::shared_ptr<SecurityPolicy> Policy;
    std::shared_ptr<HallucinationDetector> Hallucination;
    std::shared_ptr<SandboxExecutor> Sandbox;
    std::shared_ptr<AlertLogger> Logger;
    std::shared_ptr<BuiltinKnowledge> BuiltinKnowledge = std::make_shared<BuiltinKnowledge>();
};

// 测试 1：安全代码通过
TEST_F(AIMonitorIntegrationTest, SafeCodePasses) {
    MonitoredAIRequest Request{
        .GeneratedCode = R"(
            函数 整数型 main() {
                整数型 x = 10;
                打印行("Hello");
                返回 x;
            }
        )",
        .SourceLanguage = "zhc",
        .IsUserRequest = false
    };
    
    auto Result = Monitor->AnalyzeCode(Request);
    EXPECT_TRUE(Result.IsAllowed);
    EXPECT_GT(Result.TrustScore, 0.8f);
}

// 测试 2：危险代码被阻止
TEST_F(AIMonitorIntegrationTest, DangerousCodeBlocked) {
    MonitoredAIRequest Request{
        .GeneratedCode = R"(
            函数 整数型 main() {
                system("rm -rf /");
                返回 0;
            }
        )",
        .SourceLanguage = "zhc",
        .IsUserRequest = false
    };
    
    auto Result = Monitor->AnalyzeCode(Request);
    EXPECT_FALSE(Result.IsAllowed);
    EXPECT_EQ(Result.TrustScore, 0.0f);
}

// 测试 3：幻觉检测
TEST_F(AIMonitorIntegrationTest, HallucinationDetected) {
    MonitoredAIRequest Request{
        .GeneratedCode = R"(
            函数 整数型 main() {
                fake_unknown_function();
                返回 0;
            }
        )",
        .SourceLanguage = "zhc",
        .IsUserRequest = false
    };
    
    auto Result = Monitor->AnalyzeCode(Request);
    EXPECT_TRUE(Result.IsAllowed);  // 警告但不阻止
    EXPECT_FALSE(Result.Warnings.empty());
}

// 测试 4：严格模式下低信任评分阻止
TEST_F(AIMonitorIntegrationTest, LowTrustBlockedInStrictMode) {
    Monitor->SetMonitorLevel(MonitorLevel::Strict);
    Monitor->SetTrustThreshold(0.7f);
    
    MonitoredAIRequest Request{
        .GeneratedCode = R"(
            函数 整数型 main() {
                调用一些复杂的未知函数(1, 2, 3, 4, 5);
                返回 0;
            }
        )",
        .SourceLanguage = "python",
        .IsUserRequest = false
    };
    
    auto Result = Monitor->AnalyzeCode(Request);
    EXPECT_FALSE(Result.IsAllowed);
    EXPECT_LT(Result.TrustScore, 0.7f);
}

// 测试 5：异步分析
TEST_F(AIMonitorIntegrationTest, AsyncAnalysis) {
    MonitoredAIRequest Request{
        .GeneratedCode = "打印行(\"test\");",
        .SourceLanguage = "zhc",
        .IsUserRequest = false
    };
    
    auto Future = Monitor->AnalyzeCodeAsync(Request);
    auto Result = Future.get();
    
    EXPECT_TRUE(Result.IsAllowed);
}

// 测试 6：沙箱执行
TEST_F(AIMonitorIntegrationTest, SandboxExecution) {
    std::string Code = R"(
        函数 整数型 main() {
            打印行("Hello from sandbox");
            返回 0;
        }
    )";
    
    auto Result = Sandbox->Execute(Code, "test.zhc");
    EXPECT_TRUE(Result.Success);
    EXPECT_EQ(Result.ExitCode, 0);
    EXPECT_NE(Result.Stdout.find("Hello from sandbox"), std::string::npos);
}

// 测试 7：沙箱超时
TEST_F(AIMonitorIntegrationTest, SandboxTimeout) {
    std::string Code = R"(
        函数 整数型 main() {
            当(真) {
                打印行("infinite");
            }
            返回 0;
        }
    )";
    
    SandboxConfig Config;
    Config.MaxTimeMs = 100;  // 100ms 超时
    auto SandboxedExec = std::make_shared<SandboxExecutor>(Config);
    
    auto Result = SandboxedExec->Execute(Code, "infinite.zhc");
    EXPECT_FALSE(Result.Success);
    EXPECT_NE(Result.Violations.end(),
              std::find(Result.Violations.begin(), 
                       Result.Violations.end(), 
                       "Execution timeout"));
}

// 测试 8：完整流程
TEST_F(AIMonitorIntegrationTest, FullPipeline) {
    MonitoredAIRequest Request{
        .OriginalPrompt = "写一个计算斐波那契的函数",
        .GeneratedCode = R"(
            函数 整数型 fibonacci(整数型 n) {
                如果 (n <= 1) {
                    返回 n;
                }
                返回 fibonacci(n - 1) + fibonacci(n - 2);
            }
            
            函数 整数型 main() {
                整数型 result = fibonacci(10);
                打印行(result);
                返回 0;
            }
        )",
        .SourceLanguage = "zhc",
        .CalledFunctions = {"fibonacci", "打印行"},
        .IsUserRequest = false
    };
    
    auto Result = Monitor->AnalyzeCode(Request);
    
    EXPECT_TRUE(Result.IsAllowed);
    EXPECT_GT(Result.TrustScore, 0.5f);
    
    // 尝试沙箱执行
    auto ExecResult = Sandbox->Execute(Request.GeneratedCode, "fib.zhc");
    EXPECT_TRUE(ExecResult.Success);
}

// 运行所有测试
int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
```

### 11.2 验收标准

```bash
# 编译测试
cmake --build build --target zhc_ai_monitor_test

# 运行所有集成测试
./build/bin/zhc_ai_monitor_test
# 期望：All tests passed (8/8)

# 运行特定测试
./build/bin/zhc_ai_monitor_test --gtest_filter="*Dangerous*"
# 期望：1 test passed

# 生成覆盖率报告
lcov --capture --directory build --output coverage.info
genhtml coverage.info --output-directory coverage_html
# 期望：Coverage report generated
```

---

## 5.12 Go/No-Go 检查点

每个检查点必须通过才能进入下一任务：

| 检查点 | 验证命令 | 通过条件 | 失败处理 |
|:---|:---|:---|:---|
| **P5.1** | `./build/bin/zhc_ai_monitor_test --test-basic` | 监控管理器初始化成功 | 检查依赖注入 |
| **P5.2** | `./build/bin/zhc_security_test --check "system("ls")"` | 危险函数被检测并阻止 | 检查规则库 |
| **P5.3** | `./build/bin/zhc_hallucination_test --check "fake_func()"` | 虚假函数被检测 | 检查模式库 |
| **P5.4** | `./build/bin/zhc_sandbox_test --execute hello.zhc` | 安全代码在沙箱中执行成功 | 检查 seccomp 配置 |
| **P5.5** | `./build/bin/zhc_memory_test --check-leaks` | 内存泄漏检测正常 | 检查分析器逻辑 |
| **P5.6** | `./build/bin/zhc_alert_test --log test` | 告警正确写入日志 | 检查文件权限 |
| **P5.7** | `zhc compile test.zhc -ai-monitor` | CLI 参数生效 | 检查 CLI 集成 |

### 最终验收标准

```bash
# ✅ 验收命令 1：危险代码阻止
echo 'system("rm -rf /");' | ./build/bin/test_monitor --dangerous
# 期望：BLOCKED - SecurityPolicy, Critical

# ✅ 验收命令 2：安全代码通过
echo 'printf("hello\n");' | ./build/bin/test_monitor --safe
# 期望：ALLOWED - TrustScore: 0.95

# ✅ 验收命令 3：完整 CLI 流程
zhc compile ai_generated.zhc -ai-monitor -ai-monitor-level=strict -ai-trust-threshold=0.7
# 期望：⚠️ 警告 + ❌ 阻止（如果信任评分 < 0.7）

# ✅ 验收命令 4：沙箱隔离
./build/bin/test_isolation
# 期望：进程只能访问 /tmp/zhc_sandbox/ 目录

# ✅ 验收命令 5：告警日志
cat zhc_monitor.log
# 期望：包含时间戳、级别、来源、详情

# ✅ 验收命令 6：覆盖率
./build/bin/zhc_ai_monitor_test --coverage
# 期望：覆盖率 ≥ 70%
```

---

## 5.13 文件清单

Phase 5 新增文件列表：

| 文件路径 | 类型 | 说明 |
|:---|:---:|:---|
| `include/zhc/ai/zhc_ai_monitor.h` | 头文件 | 监控管理器声明 |
| `src/ai/zhc_ai_monitor.cpp` | 实现 | 监控管理器实现 |
| `include/zhc/ai/zhc_security_policy.h` | 头文件 | 安全策略引擎声明 |
| `src/ai/zhc_security_policy.cpp` | 实现 | 安全策略引擎实现 |
| `include/zhc/ai/zhc_hallucination_detector.h` | 头文件 | 幻觉检测器声明 |
| `src/ai/zhc_hallucination_detector.cpp` | 实现 | 幻觉检测器实现 |
| `include/zhc/ai/builtin_knowledge.h` | 头文件 | 内置知识库声明 |
| `src/ai/builtin_knowledge.cpp` | 实现 | 内置知识库实现（~300 行）|
| `include/zhc/ai/zhc_sandbox_executor.h` | 头文件 | 沙箱执行器声明 |
| `src/ai/zhc_sandbox_executor.cpp` | 实现 | 沙箱执行器实现 |
| `include/zhc/ai/zhc_memory_safety.h` | 头文件 | 内存安全分析器声明 |
| `src/ai/zhc_memory_safety.cpp` | 实现 | 内存安全分析器实现 |
| `src/ai/zhc_syscall_filter.cpp` | 实现 | 系统调用过滤器实现 |
| `include/zhc/ai/zhc_alert_logger.h` | 头文件 | 告警日志声明 |
| `src/ai/zhc_alert_logger.cpp` | 实现 | 告警日志实现 |
| `policies/default_policy.json` | 配置 | 默认安全策略 |
| `src/ai/policy_loader.cpp` | 实现 | 策略文件加载器 |
| `test/ai_monitor_test.cpp` | 测试 | AI 监控集成测试 |
| `test/security_policy_test.cpp` | 测试 | 安全策略单元测试 |
| `test/hallucination_test.cpp` | 测试 | 幻觉检测单元测试 |
| `test/sandbox_test.cpp` | 测试 | 沙箱执行单元测试 |

**新增代码量**：约 3,500 行 C++ / 300 行 JSON

---

*文档版本: v1.0*  
*创建时间: 2026-04-13*  
*所属阶段: Phase 5（AI 可信执行监控）*
