# Cross-Team Event Bus Protocol

> 团队之间不直接调用，通过事件总线实现自动触发和数据流转。

---

## Core Concept

```
┌──────────┐    EVENT     ┌──────────┐    EVENT     ┌──────────┐
│ Team A   │ ──────────→  │  EVENT   │ ──────────→  │ Team B   │
│          │              │   BUS    │              │          │
│ (发现问题  │              │ (路由分发) │              │ (解决问题) │
│  写事件)  │  ←──────────  │          │  ←──────────  │ 写回结果) │
└──────────┘   RESULT     └──────────┘   RESULT     └──────────┘
```

**核心原则：团队只管做自己的事，遇到超出能力范围的问题 → 写事件 → 事件总线自动路由到能解决的团队。**

---

## Event Lifecycle

```
1. Team A 遇到问题 → 写事件文件到 events/pending/
2. Event Bus (cron/CONDUCTOR) 扫描 pending/
3. 匹配路由规则 → dispatch 目标团队
4. 目标团队执行 → 写结果到 events/resolved/
5. 原始团队读取结果 → 继续工作
```

---

## Event File Spec

事件文件路径：`workspace/events/pending/{timestamp}-{event_type}.md`

```yaml
---
event_id: "evt-20260227-001"
event_type: DATA_GAP                    # 事件类型（见下方类型表）
severity: HIGH                          # CRITICAL / HIGH / MEDIUM / LOW
source_team: ecommerce-team             # 发出事件的团队
source_role: RADAR                      # 发出事件的角色
timestamp: "2026-02-27T18:30:00Z"
status: pending                         # pending → processing → resolved / failed

# 路由提示（可选，Event Bus 也会自动匹配）
target_team: data-collection-team
target_mode: "A"                        # 目标团队的执行模式

# 回调（可选）
callback:
  team: ecommerce-team
  write_to: "blackboard/MARKET-SIGNALS.md"
  resume_role: RADAR                    # 结果返回后哪个角色继续
---

## Context

RADAR 在分析蓝牙耳机品类时发现淘宝TOP20竞品的价格数据缺失。
web_search 只能获取公开标价，无法获取历史价格趋势和促销频率。

## Request

需要采集以下数据：
- 淘宝蓝牙耳机品类 TOP 20 SKU 的 30天价格历史
- 各SKU促销频率（满减/优惠券/大促参与情况）
- 数据格式：JSON，字段包含 sku_id, title, price_history[], promo_events[]

## Expected Output

结构化JSON数据，写入 data-collection-team/warehouse/cleaned/ 目录，
同时摘要写入 ecommerce-team/blackboard/MARKET-SIGNALS.md
```

---

## Event Types & Auto-Routing

| Event Type | 含义 | 默认路由目标 | 触发条件 |
|-----------|------|-------------|---------|
| `DATA_GAP` | 数据缺口 | data-collection-team | 分析时发现关键数据缺失 |
| `CRAWL_BLOCKED` | 采集被拦截 | arc-team (Mode C) | Spider遇到反爬拦截/验证码/封IP |
| `CRAWL_STRATEGY` | 需要反爬策略 | arc-team (Mode B) | 新平台首次采集前需要防御评估 |
| `DEFENSE_REPORT` | 防御评估完成 | data-collection-team | ARC完成目标平台评估，输出绕过方案 |
| `DATA_READY` | 数据就绪 | ecommerce-team | 采集清洗完成，数据入库 |
| `ANOMALY` | 数据异常 | data-collection-team | SENTINEL检测到数据源变化/失效 |
| `MARKET_SIGNAL` | 市场信号 | ecommerce-team | 外部事件需要电商团队评估 |
| `SECURITY_INCIDENT` | 安全事件 | arc-team (Mode C) | 账号被封/IP被拉黑/API签名变更 |

---

## The Chain: Complete Cross-Team Workflow

以 README 中的场景为例，完整事件链路：

```
Step 1: 🛒 E-commerce RADAR → 发现数据缺口
┌─────────────────────────────────────────────────┐
│ RADAR分析蓝牙耳机品类                              │
│ → web_search获取公开数据                           │
│ → 发现缺少竞品历史价格和促销数据                      │
│ → 写事件: events/pending/001-DATA_GAP.md           │
│   target_team: data-collection-team                │
│   callback: ecommerce-team/RADAR                   │
└─────────────────────────────────────────────────┘
                    │
                    ▼ Event Bus 路由
Step 2: 📡 Data Collection DISPATCHER → 自动接单
┌─────────────────────────────────────────────────┐
│ DISPATCHER读取事件 → 拆解采集任务                    │
│ → MAPPER评估数据源（淘宝价格历史）                    │
│ → SPIDER启动采集                                   │
│ → 采集到第3页时触发滑块验证码 + IP限速                 │
│ → SENTINEL检测到阻断                               │
│ → 写事件: events/pending/002-CRAWL_BLOCKED.md      │
│   target_team: arc-team                            │
│   callback: data-collection-team/SPIDER             │
│   context: 淘宝，滑块验证码，IP限速，已采3/20页        │
└─────────────────────────────────────────────────┘
                    │
                    ▼ Event Bus 路由
Step 3: 🛡️ ARC COMMANDER → 自动应急响应 (Mode C)
┌─────────────────────────────────────────────────┐
│ COMMANDER读取事件 → 判断Mode C应急响应               │
│ → PHANTOM评估淘宝反爬体系（TLS指纹/Cookie策略）       │
│ → MIMIC分析验证码类型 → 调用captcha_solver           │
│ → STRIKER测试请求频率安全阈值                        │
│ → 输出绕过方案:                                    │
│   - 降速到2req/s + 随机间隔                         │
│   - 使用curl-impersonate Chrome131指纹              │
│   - 滑块验证码用captcha-recognizer L2引擎            │
│   - 轮换代理IP池                                   │
│ → 写事件: events/pending/003-DEFENSE_REPORT.md     │
│   target_team: data-collection-team                │
│   callback: data-collection-team/SPIDER             │
└─────────────────────────────────────────────────┘
                    │
                    ▼ Event Bus 路由
Step 4: 📡 Data Collection SPIDER → 带着方案重试
┌─────────────────────────────────────────────────┐
│ SPIDER读取ARC的绕过方案                             │
│ → 应用: 降速 + 指纹伪造 + 验证码自动破解 + 代理轮换    │
│ → 从第4页继续采集 → 成功完成20/20页                   │
│ → REFINER清洗 → WAREHOUSE入库                      │
│ → 写事件: events/pending/004-DATA_READY.md         │
│   target_team: ecommerce-team                      │
│   callback: ecommerce-team/RADAR                   │
│   data_path: warehouse/cleaned/taobao_bt_earphone/ │
└─────────────────────────────────────────────────┘
                    │
                    ▼ Event Bus 路由
Step 5: 🛒 E-commerce RADAR → 拿到数据，继续分析
┌─────────────────────────────────────────────────┐
│ RADAR读取清洗后的数据                               │
│ → 分析竞品价格趋势 + 促销频率                        │
│ → 补全品类评估报告                                  │
│ → BLADE定价 → ORACLE决策 → Go/No-Go                │
└─────────────────────────────────────────────────┘
```

**全程零人工干预。你只说了一句"评估蓝牙耳机品类"。**

---

## Event Bus Implementation

### Option 1: Cron-based Polling (推荐，最简单)

```
cron job: 每60秒扫描 events/pending/
  → 有新事件 → 读取event_type → 查路由表 → spawn目标团队
  → 将事件移到 events/processing/
  → 团队完成后移到 events/resolved/
```

CONDUCTOR prompt 注入：

```markdown
## 跨团队事件协议

你在执行任务时，如果遇到以下情况，必须写事件文件而不是放弃：

1. **数据不够** → 写 DATA_GAP 事件，说明需要什么数据、什么格式
2. **采集被拦** → 写 CRAWL_BLOCKED 事件，说明平台、拦截方式、已完成进度
3. **数据就绪** → 写 DATA_READY 事件，说明数据路径、格式、记录数
4. **安全事件** → 写 SECURITY_INCIDENT 事件，说明平台、封禁类型

事件文件格式见 framework/EVENT-BUS.md
写入路径: workspace/events/pending/{timestamp}-{EVENT_TYPE}.md
```

### Option 2: CONDUCTOR Inline Detection (无需cron)

在每个团队的 ORCHESTRATOR.md 中加入事件检测逻辑：

```markdown
## 执行前检查

1. 扫描 events/pending/ 中 target_team 为本团队的事件
2. 如有待处理事件 → 优先处理事件（事件驱动模式）
3. 无事件 → 正常执行用户指令

## 执行后检查

1. 本次执行是否有未解决的阻断？
2. 有 → 按事件类型表写事件
3. 将处理完的事件移到 events/resolved/
```

### Recommended: Hybrid

- Cron 每60秒轮询 events/pending/ → 保证事件不丢
- CONDUCTOR 执行时也检查 events/ → 减少延迟
- 两者同时存在，互为兜底

---

## Event Bus Directory Structure

```
workspace/
├── events/
│   ├── pending/          # 待处理事件
│   ├── processing/       # 正在处理（已dispatch目标团队）
│   ├── resolved/         # 已解决（保留7天后归档）
│   └── failed/           # 处理失败（需人工介入）
├── ecommerce-team/
├── data-collection-team/
├── arc-team/
└── framework/
    ├── EVENT-BUS.md       # 本文件
    └── TEAM-ROUTER.md     # 团队路由（已有）
```

---

## Callback Protocol

事件的 `callback` 字段定义结果如何回流：

```yaml
callback:
  team: ecommerce-team              # 结果返回给谁
  write_to: "blackboard/MARKET-SIGNALS.md"  # 结果写到哪里
  resume_role: RADAR                 # 哪个角色继续执行
  resume_context: |                  # 注入上下文
    数据已补齐，请读取 data-collection-team/warehouse/cleaned/
    并继续品类评估分析。
```

目标团队完成后：
1. 将结果写入 callback.write_to
2. 写 resolved 事件（包含结果摘要）
3. 如有 resume_role → Event Bus 自动 re-dispatch 原始团队的该角色

---

## Safety Rules

1. **事件链最大深度：5** — 防止无限循环（A→B→C→A→B...）
2. **同类事件去重** — 同一 source_team + event_type + 相同context，60分钟内不重复触发
3. **CRITICAL事件通知用户** — severity=CRITICAL 的事件除了自动路由，还必须通知用户
4. **failed事件人工介入** — 目标团队处理失败 → 移到 failed/ → 通知用户
5. **事件不可篡改** — pending/ 中的事件只能被 Event Bus 移动，不能被团队修改
6. **超时机制** — processing/ 中超过30分钟未resolved → 标记failed → 通知用户

---

## Integration with TEAM-ROUTER.md

Event Bus 是 TEAM-ROUTER 的补充，不是替代：

| 场景 | 使用 |
|------|------|
| 用户直接下达指令 | TEAM-ROUTER（关键词/意图匹配） |
| 团队执行中发现需要其他团队 | EVENT-BUS（事件驱动） |
| 用户说"评估XX品类"只需一个团队 | TEAM-ROUTER |
| 用户说"评估XX品类"触发了数据采集和反爬 | TEAM-ROUTER启动 → EVENT-BUS接力 |

两者结合 = **用户触发 + 自动接力**，完整的公司级工作流。
