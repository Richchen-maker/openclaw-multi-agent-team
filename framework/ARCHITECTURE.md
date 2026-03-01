# Architecture — OpenClaw Multi-Agent Team Framework

## 整体架构

```
openclaw-multi-agent-team/
├── framework/                    # 框架层（domain-agnostic）
│   ├── eventbus/                 # EventBus Runtime Engine (21 modules, 4500+ lines Python)
│   │   ├── bus.py                # 核心：scan → route → dispatch 循环
│   │   ├── dispatcher.py         # Dispatcher抽象 + CronDispatcher + OpenClawDispatcher
│   │   ├── watchdog.py           # V3监控：5种检查 + 自动修复 + cron dispatch
│   │   ├── evolver.py            # 团队自进化：extract → crystallize → shortcut
│   │   ├── scheduler.py          # 多链路并行调度 + 团队锁
│   │   ├── registry.py           # 动态能力注册：capabilities.yaml → 路由表
│   │   ├── databus.py            # 数据管道：data_refs + schema验证
│   │   ├── memory_bridge.py      # 跨团队知识共享
│   │   ├── cost_controller.py    # 链路预算：severity→model映射 + token限额
│   │   ├── templates.py          # 标准化事件写回模板（shell + Python）
│   │   ├── router.py             # 双轨路由：静态DEFAULT_ROUTES + 动态Registry
│   │   ├── event.py              # Event数据模型（YAML frontmatter解析）
│   │   ├── config.py             # 配置管理：defaults + eventbus.yaml merge
│   │   ├── cli.py                # CLI入口：scan/emit/run/status/route/watchdog/trace/...
│   │   ├── analyzer.py           # V2事件分析器
│   │   ├── profiler.py           # V2团队画像
│   │   ├── predictor.py          # V2预测器
│   │   ├── history.py            # V2历史追踪
│   │   ├── recovery.py           # V2智能恢复引擎
│   │   ├── __init__.py           # Package init
│   │   └── __main__.py           # python -m eventbus 入口
│   ├── ARCHITECTURE.md           # 本文档
│   ├── ORCHESTRATOR.md           # CONDUCTOR执行协议
│   ├── EVENT-BUS.md              # Event Bus协议 + Runtime详解
│   ├── TEAM-ROUTER.md            # 多团队路由
│   ├── TOOL-BOOTSTRAP.md         # Sub-agent工具注入
│   └── BLACKBOARD-SPEC.md        # Blackboard读写规则
├── examples/                     # 示例团队（可直接部署）
│   ├── ecommerce-team/           # 🛒 电商（6 roles）
│   ├── data-collection-team/     # 📡 数据采集（6 roles）
│   ├── arc-team/                 # 🛡️ 安全攻防（6 roles, 54 weapons）
│   ├── content-team/             # 📝 内容生产（4 roles）
│   └── intelligence-team/        # 🔍 情报分析
├── events/                       # 事件状态机（运行时生成）
│   ├── pending/                  # ⏳ 待处理
│   ├── processing/               # 🔄 处理中
│   ├── resolved/                 # ✅ 已完成
│   ├── failed/                   # ❌ 失败
│   └── .watchdog/                # Watchdog状态 + patterns + budgets + scheduler
├── knowledge/                    # MemoryBridge共享知识库
│   └── {domain}/{topic}.md
├── eventbus.yaml                 # Event Bus配置
└── docs/                         # 用户文档
```

## Event Lifecycle — 事件状态机

```
           emit / sub-agent写回
                 │
                 ▼
            ┌─────────┐
            │ pending  │  ← YAML文件落入 events/pending/
            └────┬─────┘
                 │ EventBus.scan() + priority排序(CRITICAL first)
                 │ Router.resolve(event_type) → target_team + mode
                 ▼
           ┌──────────┐
           │processing │  ← 文件移入 events/processing/
           └─────┬─────┘
                 │ Dispatcher.execute() → sub-agent执行
                 │
          ┌──────┴──────┐
          ▼             ▼
     ┌─────────┐  ┌─────────┐
     │resolved │  │ failed  │
     └─────────┘  └─────────┘
          │
          ▼
     Evolver.extract_from_chain()  → 模式提取 → shortcut
     MemoryBridge.store()          → 知识沉淀
```

**事件文件格式**：YAML frontmatter + Markdown body

```yaml
---
event_id: 'abc12345-def67890'
event_type: 'DATA_GAP'
severity: 'HIGH'
source_team: 'ecommerce-team'
chain_depth: 0
chain_id: 'chain-xxx'
parent_event_id: ''
metadata:
  source_role: 'RADAR'
---
需要补充蓝牙耳机品类的供应商价格数据...
```

## Dispatch机制 — 三种模式

| 模式 | dispatch_mode | 行为 |
|------|--------------|------|
| **Default** | `default` | 打印shell命令到stdout（dry-run/CI） |
| **Cron** | `cron` | 写DispatchRequest YAML到 `events/.dispatch/` → Watchdog cron消费 |
| **Live** | `live` | OpenClawDispatcher直接spawn sub-agent |

**CronDispatcher流程**：
```
EventBus.process_event()
  → CronDispatcher.execute()
    → 写 DispatchRequest YAML 到 events/.dispatch/
      → Watchdog cron定时扫描 .dispatch/
        → 读取pending request → openclaw spawn执行
          → sub-agent完成 → 写回事件到 events/pending/
```

## 路由 — 双轨制

**静态路由**（router.py DEFAULT_ROUTES）：
```python
DEFAULT_ROUTES = {
    "DATA_GAP":          {"target_team": "data-collection-team", "target_mode": "A"},
    "CRAWL_BLOCKED":     {"target_team": "arc-team",             "target_mode": "C"},
    "DATA_READY":        {"target_team": "ecommerce-team",       "target_mode": "A"},
    "SECURITY_INCIDENT": {"target_team": "arc-team",             "target_mode": "C"},
    ...
}
```

**动态路由**（Registry扫描 capabilities.yaml）：
```
Registry.scan()
  → 遍历 workspace下所有 *-team/ + examples/*-team/ + teams/*
    → 解析每个团队的 capabilities.yaml
      → 构建 event_type → {target_team, target_mode} 映射
        → priority高的优先
```

**优先级**：显式传入routes > 动态Registry > 静态DEFAULT_ROUTES

## 安全机制

| 机制 | 实现 | 说明 |
|------|------|------|
| **chain_depth限制** | bus.py, 默认max=5 | 防止事件链无限递归 |
| **去重** | `_dispatched_ids` set + dedup_window | 同一事件不重复dispatch |
| **处理超时** | processing_timeout=1800s | 卡死事件自动标记failed |
| **成本控制** | CostController per-chain budget | 超预算暂停链路 |
| **事件不可变** | 文件写入后只移动不修改 | 审计友好 |
| **Watchdog** | 5种检查 + 自动修复 | STALE_PENDING/STALE_PROCESSING/CHAIN_BROKEN/FORMAT_ERROR/BUS_DOWN |

## 团队接入 — 零代码

1. 创建团队目录（如 `examples/my-team/`）
2. 放入 `capabilities.yaml`：
```yaml
team: my-team
description: "My custom team"
capabilities:
  - event_type: MY_EVENT
    modes: [A, B]
    priority: 10
```
3. Registry自动扫描发现 → 事件自动路由到该团队
4. 无需修改任何框架代码

## 核心模块清单（21个Python文件，4500+ lines）

| 模块 | 职责 | 优先级 |
|------|------|--------|
| bus.py | 核心引擎：scan → route → dispatch → move | P0 |
| event.py | Event数据模型 + YAML解析 | P0 |
| router.py | 双轨路由 | P0 |
| dispatcher.py | 3种Dispatcher实现 | P0 |
| config.py | 配置加载 + 默认值 | P0 |
| cli.py | CLI入口（12+子命令） | P0 |
| templates.py | 标准化事件写回 | P0 |
| watchdog.py | V3监控 + 5种检查 + cron dispatch | P1 |
| registry.py | 动态能力发现 | P1 |
| databus.py | 数据引用 + schema验证 | P1 |
| memory_bridge.py | 跨团队知识共享 | P1 |
| cost_controller.py | 链路预算控制 | P1 |
| scheduler.py | 多链路并行调度 | P1 |
| evolver.py | 团队自进化引擎 | P2 |
| analyzer.py | 事件模式分析 | P2 |
| profiler.py | 团队性能画像 | P2 |
| predictor.py | 预测器 | P2 |
| history.py | 历史追踪 | P2 |
| recovery.py | 智能恢复引擎 | P2 |
| __init__.py | Package导出 | P3 |
| __main__.py | Module入口 | P3 |
