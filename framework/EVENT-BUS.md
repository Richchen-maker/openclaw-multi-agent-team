# Event Bus — 跨团队自动协作引擎

## Part 1: 协议设计

### 核心理念

团队之间不直接通信。通过文件系统的事件（YAML文件）异步协作。

- **松耦合** — 团队只知道事件类型，不知道谁在处理
- **可审计** — 所有事件都是文件，天然可追溯
- **可恢复** — 任何环节失败，事件还在，可重试

### 事件格式

```yaml
---
event_id: 'abc12345-def67890'
event_type: 'DATA_GAP'
severity: 'HIGH'               # CRITICAL > HIGH > MEDIUM > LOW > INFO
source_team: 'ecommerce-team'
chain_depth: 0                  # 链深度，max=5
chain_id: 'chain-xxx'          # 链路追踪ID
parent_event_id: ''            # 父事件ID
metadata:
  source_role: 'RADAR'
  data_refs: []                # DataBus数据引用
---
事件正文（Markdown格式）
```

### 状态机

```
pending → processing → resolved
                    → failed
```

### 路由表

event_type → target_team + target_mode

详见 [TEAM-ROUTER.md](TEAM-ROUTER.md)

---

## Part 2: Runtime实现

### 21个Python模块（4500+ lines）

```
framework/eventbus/
├── bus.py              # 核心引擎 — scan/route/dispatch循环
├── event.py            # Event数据模型
├── router.py           # 双轨路由（静态+动态Registry）
├── dispatcher.py       # 3种Dispatcher：Default/Cron/OpenClaw
├── config.py           # 配置管理
├── cli.py              # CLI（12+子命令）
├── templates.py        # 事件写回模板
├── watchdog.py         # V3监控（5种检查+自动修复+cron dispatch）
├── registry.py         # 动态能力发现
├── databus.py          # 数据引用+Schema验证
├── memory_bridge.py    # 跨团队知识共享
├── cost_controller.py  # 链路预算控制
├── scheduler.py        # 多链路并行调度
├── evolver.py          # 团队自进化
├── analyzer.py         # 事件模式分析（V2）
├── profiler.py         # 团队性能画像（V2）
├── predictor.py        # 预测器（V2）
├── history.py          # 历史追踪（V2）
├── recovery.py         # 智能恢复引擎（V2）
├── __init__.py
└── __main__.py
```

### CLI命令

```bash
# 设置PYTHONPATH（所有命令前缀）
export PYTHONPATH=framework

# 基础
python3 -m eventbus scan                    # 扫描pending事件
python3 -m eventbus status                  # 事件统计
python3 -m eventbus route DATA_GAP          # 查路由

# 发射事件
python3 -m eventbus emit DATA_GAP \
  --source-team ecommerce-team \
  --source-role RADAR \
  --severity HIGH \
  --context "需要补充蓝牙耳机数据"

# 运行
python3 -m eventbus run                     # 单次poll
python3 -m eventbus run --interval 30       # 持续poll
python3 -m eventbus run --live              # 直接spawn sub-agent
python3 -m eventbus run --daemon            # 后台daemon

# 监控
python3 -m eventbus watchdog                # 健康检查
python3 -m eventbus watchdog --fix          # 自动修复
python3 -m eventbus watchdog --dashboard    # Dashboard
python3 -m eventbus watchdog --loop         # 持续监控

# 链路追踪
python3 -m eventbus trace <chain_id/event_id/keyword>

# Registry
python3 -m eventbus registry --scan         # 扫描团队能力

# DataBus
python3 -m eventbus data list               # 列出数据文件
python3 -m eventbus data validate <ref>     # Schema验证

# 成本
python3 -m eventbus cost                    # 预算报告
python3 -m eventbus cost --set chain-xxx 100000  # 设置预算

# 调度器
python3 -m eventbus scheduler               # 调度状态
python3 -m eventbus scheduler --chains      # 活跃链路

# 自进化
python3 -m eventbus shortcut DATA_GAP       # 查shortcut
```

### 配置（eventbus.yaml）

```yaml
# eventbus.yaml — 放在workspace根目录
workspace_dir: "."
poll_interval: 60              # 轮询间隔（秒）
max_chain_depth: 5             # 事件链最大深度
dedup_window: 3600             # 去重窗口（秒）
processing_timeout: 1800       # processing超时（秒）
resolved_retention: 7          # resolved保留天数
dispatch_mode: "cron"          # cron | live | default
dispatch_timeout: 300          # sub-agent超时
bus_mode: "cron"               # cron | daemon
```

### CronDispatcher工作流

```
EventBus.process_event()
  │
  ▼
CronDispatcher.execute(team, mode, event, prompt)
  │
  ├─ DataBus.inject_data_refs(event)     # 注入数据引用
  │
  ├─ 写 DispatchRequest YAML
  │   → events/.dispatch/20260301_120000_arc-team_abc12345.yaml
  │
  └─ return True
       │
       ▼
Watchdog cron (定时扫描 .dispatch/)
  │
  ├─ 读取 status=pending 的request
  ├─ openclaw spawn --task "..." --label team-dispatch
  ├─ 标记 status=dispatched
  │
  └─ sub-agent完成 → 写回事件到 events/pending/
```

### chain_id链路追踪

每条事件链共享同一个 `chain_id`：

```
chain_id: "chain-abc123"

  [depth=0] DATA_GAP (ecommerce→data-collection)
    └─[depth=1] CRAWL_BLOCKED (data-collection→arc)
        └─[depth=2] DEFENSE_REPORT (arc→data-collection)
            └─[depth=3] DATA_READY (data-collection→ecommerce)
```

用 `trace` 命令可视化：
```bash
PYTHONPATH=framework python3 -m eventbus trace chain-abc123
```

输出：
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Event Chain: chain-abc123
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
abc12345 [DATA_GAP] ecommerce-team/RADAR ⏳
│  ├→ def67890 [CRAWL_BLOCKED] data-collection-team/SPIDER 🔄
│  │  ├→ ghi90123 [DEFENSE_REPORT] arc-team/SHIELD ✅
│  │  │  ├→ jkl45678 [DATA_READY] data-collection-team/SPIDER ✅
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total: 4 events | Resolved: 2/4
```

### 功能清单

| 优先级 | 功能 | 状态 |
|--------|------|------|
| **P0** | EventBus core（scan/route/dispatch） | ✅ |
| **P0** | Event YAML解析 + 状态机 | ✅ |
| **P0** | 双轨路由（静态+动态） | ✅ |
| **P0** | 3种Dispatcher | ✅ |
| **P0** | CLI（12+子命令） | ✅ |
| **P0** | 标准化事件模板 | ✅ |
| **P1** | Watchdog V3（5种检查+自动修复） | ✅ |
| **P1** | CronDispatcher + DispatchRequest | ✅ |
| **P1** | Dynamic Registry | ✅ |
| **P1** | DataBus + Schema验证 | ✅ |
| **P1** | MemoryBridge | ✅ |
| **P1** | CostController | ✅ |
| **P1** | Parallel Scheduler | ✅ |
| **P2** | Evolver自进化 | ✅ |
| **P2** | Analyzer + Profiler + Predictor | ✅ |
| **P2** | History + Recovery | ✅ |
| **P2** | Chain trace可视化 | ✅ |
| **P3** | Priority Queue（severity排序） | ✅ |
| **P3** | Severity→Model映射 | ✅ |
