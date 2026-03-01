# Cross-Team Collaboration Guide V3

## 概述

团队间协作通过 **Event Bus** 实现。团队A发现需要团队B协助 → 写事件文件 → EventBus路由 → 团队B处理 → 写回结果事件。

**全链路零人工干预。**

## 快速开始

### 1. 确保Event Bus可用

```bash
cd /path/to/openclaw-multi-agent-team
PYTHONPATH=framework python3 -m eventbus status
```

### 2. 发射一个测试事件

```bash
PYTHONPATH=framework python3 -m eventbus emit DATA_GAP \
  --source-team ecommerce-team \
  --source-role RADAR \
  --severity HIGH \
  --context "测试：需要蓝牙耳机价格数据"
```

### 3. 查看路由

```bash
PYTHONPATH=framework python3 -m eventbus route DATA_GAP
# → data-collection-team / mode A
```

### 4. 运行dispatch

```bash
# Dry-run模式（打印命令不执行）
PYTHONPATH=framework python3 -m eventbus run

# Cron模式（写DispatchRequest，由Watchdog消费）
# 需要配置 eventbus.yaml dispatch_mode: cron

# Live模式（直接spawn sub-agent）
PYTHONPATH=framework python3 -m eventbus run --live
```

## Dispatch机制

### CronDispatcher + Watchdog

生产环境推荐 `dispatch_mode: cron`：

```
EventBus scan pending/
  → 路由到目标团队
  → CronDispatcher写DispatchRequest到 events/.dispatch/
    → Watchdog cron定时扫描（每N秒）
      → 读取pending request
      → openclaw spawn执行
      → sub-agent完成后写回事件
```

**为什么用Cron而不是Live**：
- 解耦：EventBus和执行器独立运行
- 可控：Watchdog可以做流控、排队、优先级
- 可审计：DispatchRequest文件留痕

## eventbus.yaml 配置

```yaml
# 放在workspace根目录
workspace_dir: "."
poll_interval: 60              # EventBus轮询间隔
max_chain_depth: 5             # 防止无限递归
dedup_window: 3600             # 去重窗口（秒）
processing_timeout: 1800       # 超时后标记failed
resolved_retention: 7          # resolved保留天数
dispatch_mode: "cron"          # cron | live | default
dispatch_timeout: 300          # sub-agent超时
bus_mode: "cron"               # cron(skip BUS_DOWN check) | daemon
```

## chain_id 链路追踪

每条跨团队协作链共享一个 `chain_id`，用于追踪整个链路。

### 写回事件时传递chain_id

```python
from eventbus.templates import generate_event_script

script = generate_event_script(
    event_type="DATA_READY",
    source_team="data-collection-team",
    source_role="SPIDER",
    severity="MEDIUM",
    chain_depth=current_depth + 1,   # 深度+1
    body="采集完成...",
    workspace_dir=workspace,
    chain_id=original_chain_id,       # 传递原始chain_id
    parent_event_id=triggering_event_id,
)
```

### CLI发射带chain_id的事件

```bash
PYTHONPATH=framework python3 -m eventbus emit DATA_READY \
  --source-team data-collection-team \
  --source-role SPIDER \
  --severity MEDIUM \
  --chain-depth 2 \
  --chain-id "chain-abc123" \
  --parent "original-event-id" \
  --context "采集完成，1200条数据"
```

### 可视化链路

```bash
PYTHONPATH=framework python3 -m eventbus trace chain-abc123
```

## 事件写回标准

使用 `framework/eventbus/templates.py` 确保格式一致。

**必填字段**：event_type, source_team, source_role, severity, chain_depth, body
**推荐字段**：chain_id, parent_event_id
**自动生成**：event_id, timestamp

templates.py 提供两种方式：
1. `generate_event_script()` → 生成shell脚本字符串
2. `write_event_file()` → 直接写Python

## 完整协作链示例

```
🛒 电商团队发现数据缺口
  → emit DATA_GAP (chain_id=chain-001, depth=0)
    │
    ▼ EventBus路由 → data-collection-team
📡 数据采集团队执行采集
  → 被反爬拦截
  → emit CRAWL_BLOCKED (chain_id=chain-001, depth=1)
    │
    ▼ EventBus路由 → arc-team
🛡️ ARC团队评估防御
  → emit DEFENSE_REPORT (chain_id=chain-001, depth=2)
    │
    ▼ EventBus路由 → data-collection-team
📡 数据采集团队用新策略重试
  → 成功
  → emit DATA_READY (chain_id=chain-001, depth=3)
    │
    ▼ EventBus路由 → ecommerce-team
🛒 电商团队完成分析 → Go/No-Go决策
```

**4个团队，4次事件流转，零人工干预。**

## 快捷命令速查

```bash
# 所有命令前缀
PYTHONPATH=framework python3 -m eventbus

# 常用
eventbus status              # 事件统计
eventbus scan                # 扫描pending
eventbus run                 # 单次dispatch
eventbus run --live          # 直接执行
eventbus watchdog            # 健康检查
eventbus watchdog --fix      # 自动修复
eventbus trace <id>          # 链路追踪
eventbus registry --scan     # 团队能力扫描
eventbus cost                # 预算报告
eventbus scheduler           # 调度状态
```

## Watchdog监控

5种检查：

| 类型 | 说明 | 自动修复 |
|------|------|----------|
| STALE_PENDING | pending超时未dispatch | 重新dispatch |
| STALE_PROCESSING | processing中超时 | 标记failed + 重试 |
| CHAIN_BROKEN | 事件链断裂 | 通知用户 |
| FORMAT_ERROR | YAML格式错误 | 移到failed |
| BUS_DOWN | EventBus进程丢失 | 重启提示 |

```bash
# 一次性检查
PYTHONPATH=framework python3 -m eventbus watchdog

# 自动修复
PYTHONPATH=framework python3 -m eventbus watchdog --fix

# 持续监控
PYTHONPATH=framework python3 -m eventbus watchdog --loop --interval 120
```
