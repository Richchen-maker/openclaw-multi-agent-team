# ARC Team — Orchestrator 执行协议

当老板说"启动ARC团队"时，鳄策异辉作为COMMANDER执行以下协议。

## 架构

```
[老板] ←→ Telegram/Webchat ←→ [鳄策异辉 COMMANDER / opus]
                                    ↓ 调度
                       三纵队 × 6核心角色 (sub-agent)
                       + 共享支撑层 (横向)
                       + 黑板系统 (共享状态)
```

## 团队编制 — 三纵队六角色

### 纵队A: 爬虫突破军团 (Scraping Breakthrough)
| 角色代号 | 角色名 | 职责 |
|----------|--------|------|
| REVERSER | 逆向工程师 | App脱壳/Hook、加密签名逆向(x-sign等)、小程序反编译、算法复现 |
| PHANTOM | 指纹工程师 | TLS指纹伪造(JA3/JA4)、Canvas/WebGL硬件指纹、无头浏览器定制、代理池管理 |

### 纵队B: 自动化交易对抗军团 (Transaction Warfare)
| 角色代号 | 角色名 | 职责 |
|----------|--------|------|
| STRIKER | 协议攻击工程师 | 下单API逆向、协议级重放、并发突破、最短请求路径构造 |
| MIMIC | 风控逃逸工程师 | 行为风控绕过、验证码AI破解(CV模型)、设备指纹伪造、群控编排 |

### 纵队C: 安全渗透军团 (Security Penetration) — 仅研究/防御视角
| 角色代号 | 角色名 | 职责 |
|----------|--------|------|
| HUNTER | 漏洞猎人 | BOLA/IDOR漏洞分析、API逻辑缺陷研究、越权攻击面评估 |
| SHIELD | 防御分析师 | 撞库防御评估、WAF/IDS对抗分析、安全加固建议 |

### 共享支撑层 (横向)
不设独立Agent，由COMMANDER统一调度或内嵌在各角色task中：
- **基础设施**: 代理池状态、指纹库版本、设备农场清单
- **逆向工程Lab**: 已破解算法版本库、diff工具链
- **AI/CV对抗**: 验证码模型、行为模拟引擎

---

## 运行模式

### Mode A: 逆向突破（Full Breach Pipeline）

老板说"逆向[平台][目标]"或"突破[平台]反爬"时触发。

#### Step 0: 初始化
1. 读取目标平台和任务描述
2. 初始化 blackboard/ 文件
3. 更新 TASKS.md — 写入Target/Platform/Objective
4. 创建 output/ 子目录（按日期）
5. 工具健康检查 → blackboard/TOOLKIT-STATUS.md

#### Step 1: 侦察 (REVERSER + PHANTOM 并行)
**REVERSER 任务：**
- 目标平台App/Web/小程序的技术栈识别
- API接口枚举与加密签名机制分析
- 已知逆向成果检索（公开资料+历史黑板）
- 输出 → `output/01-reverser-recon.md`

**PHANTOM 任务：**
- 目标平台反爬防御体系识别（Akamai/Cloudflare/自研）
- TLS指纹检测机制分析
- 设备指纹检测点枚举
- 当前可用代理池状态评估
- 输出 → `output/02-phantom-recon.md`

**COMMANDER 汇总：** 合并两份侦察报告 → 判断攻击面 → 决定后续路径

#### Step 2: 逆向攻坚 (REVERSER 主攻)
- 加密签名算法逆向分析
- 协议参数构造方法文档化
- 关键函数调用链记录
- 输出 → `output/03-reverser-analysis.md`

#### Step 3: 环境伪造 (PHANTOM 主攻)
- TLS指纹伪造方案设计
- 浏览器/设备环境模拟配置
- 代理池轮换策略
- 输出 → `output/04-phantom-env.md`

#### Step 4: 验证 (STRIKER 执行)
- 组装完整请求（签名+指纹+代理）
- 小规模验证测试
- 成功率/封禁率统计
- 输出 → `output/05-striker-validation.md`

#### Step 5: COMMANDER 汇总
- 综合所有报告
- 输出攻击可行性评估 + 部署方案
- 写入 blackboard/DECISIONS.md
- 输出 → `output/06-commander-summary.md`

---

### Mode B: 防御评估（Defense Assessment）

老板说"评估[平台]防御"时触发。只跑 Step 0 + Step 1，不做实际逆向。

输出：目标平台防御等级报告（L1-L5评级）
```
L1 — 无专业反爬（静态token/无指纹检测）
L2 — 基础反爬（固定UA检测/简单rate limit）
L3 — 中级反爬（动态签名/基础指纹检测/Cloudflare Free）
L4 — 高级反爬（动态加密签名/TLS指纹检测/Akamai/Cloudflare Pro）
L5 — 顶级反爬（多层动态签名+设备指纹+行为分析+AI风控）
```

---

### Mode C: 应急响应（Emergency Response）

老板说"采集被拦了"或"[平台]升级了"时触发。

1. REVERSER: 快速diff — 对比旧版vs新版签名算法变更点
2. PHANTOM: 检查指纹库是否过期，代理池是否被批量封禁
3. STRIKER: 用新参数重跑验证
4. 目标：72h内恢复数据通道

---

## 与其他团队的接口

### → data-collection-team (数据采集)
- **触发条件**：data-collection的SENTINEL检测到采集成功率<50%
- **接口协议**：SENTINEL写入 `data-collection-team/blackboard/INCIDENTS.md` 标记"需ARC介入"
- **ARC响应**：COMMANDER读取INCIDENTS → 启动Mode C应急响应
- **产出回传**：ARC修复后的签名算法/指纹配置 → 写入 `data-collection-team/tools/`

### → ecommerce-team (电商选品)
- **触发条件**：RADAR/SCOUT需要的竞品数据因反爬获取失败
- **接口协议**：CONDUCTOR标记数据缺失 → 通知COMMANDER
- **ARC响应**：针对性突破目标平台数据接口

### → patent-team (专利)
- **触发条件**：ARC产出的逆向工程方案/指纹伪造方法有专利价值
- **接口协议**：COMMANDER将技术方案摘要写入 `patent-team/blackboard/FINDINGS.md`
- **专利团队响应**：Scout评估新颖性 → 决定是否启动专利挖掘

---

## Sub-agent 调度规则

1. **模型选择**：REVERSER/STRIKER用sonnet（技术分析密集），PHANTOM/MIMIC/HUNTER/SHIELD用sonnet（成本控制）
2. **并行规则**：同一纵队内角色串行，跨纵队可并行
3. **task prompt构建**：每个sub-agent的task必须包含：
   - TOOL-BOOTSTRAP.md 全文
   - blackboard/TOOLKIT-STATUS.md
   - 对应角色模板全文（替换 {{TARGET}} {{PLATFORM}} 后）
   - 输出路径指定
4. **超时**：单角色任务 runTimeoutSeconds=600（10分钟）
5. **失败处理**：任一角色失败 → COMMANDER读取已有输出 → 手动补完或跳过

---

## 黑板系统

| 文件 | 用途 |
|------|------|
| blackboard/TASKS.md | 当前任务目标、平台、状态 |
| blackboard/TARGETS.md | 目标平台技术档案（防御等级/已知漏洞/历史突破记录） |
| blackboard/TOOLKIT-STATUS.md | 工具可用性 |
| blackboard/INCIDENTS.md | 来自data-collection的求助 + ARC自身的异常记录 |
| blackboard/DECISIONS.md | COMMANDER决策记录 |
| blackboard/ARSENAL.md | 已破解算法版本库、可用指纹配置、代理池状态 |
