# Event Bus

**File-based event routing between teams. No servers, no queues — just YAML files in a directory.**

---

## Architecture

```
┌──────────┐     write event      ┌──────────────┐     route & dispatch     ┌──────────┐
│  Team A  │ ──────────────────→  │  events/     │ ──────────────────────→  │  Team B  │
│          │                      │  pending/    │                          │          │
│ (source) │  ←──────────────────  │  resolved/   │  ←──────────────────────  │ (target) │
└──────────┘     read result      └──────────────┘     write result         └──────────┘
                                        ▲
                                        │
                                  ┌─────┴─────┐
                                  │ eventbus   │
                                  │ (poller)   │
                                  └───────────┘
```

---

## Install

```bash
pip install pyyaml
```

That's it. The event bus is a Python module inside `framework/eventbus/`.

---

## Quick Start

### Step 1: Create event directories

```bash
mkdir -p events/{pending,processing,resolved,failed}
```

### Step 2: Emit an event

```bash
python -m eventbus emit DATA_GAP \
  --source-team ecommerce-team \
  --source-role RADAR \
  --severity HIGH \
  --context "Missing Bluetooth earphone TOP20 competitor pricing data"
```

Expected output:
```
✅ Event created: events/pending/20260228-093000-DATA_GAP.yaml
   Type: DATA_GAP
   Route: ecommerce-team/RADAR → data-collection-team
```

### Step 3: Start the bus

```bash
python -m eventbus run
```

Expected output:
```
🚌 Event Bus started (polling every 60s)
   Watching: events/pending/
   Routes loaded: 8 event types
```

---

## CLI Commands

| Command | Description | Example |
|---------|-------------|---------|
| `emit` | Create a new event | `python -m eventbus emit DATA_GAP --source-team ecommerce-team --source-role RADAR --severity HIGH --context "..."` |
| `run` | Start polling loop | `python -m eventbus run` |
| `run --interval 30` | Poll every 30s (default: 60) | `python -m eventbus run --interval 30` |
| `status` | Show pending/processing/resolved/failed counts | `python -m eventbus status` |
| `list` | List events by status | `python -m eventbus list --status pending` |
| `resolve` | Manually resolve an event | `python -m eventbus resolve evt-20260228-001` |
| `fail` | Manually fail an event | `python -m eventbus fail evt-20260228-001 --reason "timeout"` |
| `route` | Show current routing table | `python -m eventbus route` |

### `status` output example

```
$ python -m eventbus status

Event Bus Status
────────────────
  pending:    2
  processing: 1
  resolved:   14
  failed:     0

Active Events:
  [processing] evt-20260228-003  CRAWL_BLOCKED  → arc-team  (5m ago)
  [pending]    evt-20260228-004  DATA_GAP       → data-collection-team
  [pending]    evt-20260228-005  ANOMALY        → data-collection-team
```

---

## Event Types

| Event Type | Meaning | Default Target | When to Emit |
|-----------|---------|----------------|-------------|
| `DATA_GAP` | Missing data | data-collection-team | Analysis finds critical data missing |
| `CRAWL_BLOCKED` | Crawler blocked | arc-team (Mode C) | Spider hits anti-bot / CAPTCHA / IP ban |
| `CRAWL_STRATEGY` | Need anti-bot strategy | arc-team (Mode B) | New platform, need defense assessment first |
| `DEFENSE_REPORT` | Defense assessment done | data-collection-team | ARC completed bypass strategy |
| `DATA_READY` | Data available | ecommerce-team | Collection + cleaning done, data in warehouse |
| `ANOMALY` | Data anomaly | data-collection-team | SENTINEL detects source change / data corruption |
| `MARKET_SIGNAL` | Market signal | ecommerce-team | External event needs e-commerce evaluation |
| `SECURITY_INCIDENT` | Security incident | arc-team (Mode C) | Account banned / IP blacklisted / API sig changed |

---

## Routing Table

Default routing (built-in):

```
DATA_GAP          → data-collection-team
CRAWL_BLOCKED     → arc-team
CRAWL_STRATEGY    → arc-team
DEFENSE_REPORT    → data-collection-team
DATA_READY        → ecommerce-team
ANOMALY           → data-collection-team
MARKET_SIGNAL     → ecommerce-team
SECURITY_INCIDENT → arc-team
```

---

## Event File Format

Path: `events/pending/{timestamp}-{EVENT_TYPE}.yaml`

```yaml
event_id: "evt-20260228-001"
event_type: DATA_GAP
severity: HIGH
source_team: ecommerce-team
source_role: RADAR
timestamp: "2026-02-28T09:30:00Z"
status: pending

target_team: data-collection-team
target_mode: "A"

callback:
  team: ecommerce-team
  write_to: "blackboard/MARKET-SIGNALS.md"
  resume_role: RADAR

context: |
  RADAR analyzing Bluetooth earphone category.
  Missing: TOP20 competitor 30-day price history + promo frequency.
  Need: JSON with sku_id, title, price_history[], promo_events[]

request: |
  Collect Taobao Bluetooth earphone TOP 20 SKU:
  - 30-day price history
  - Promo frequency (coupons, flash sales, festival participation)
  - Output: JSON to warehouse/cleaned/taobao_bt_earphone/
```

---

## Custom Routing (eventbus.yaml)

Create `eventbus.yaml` in your workspace root to override or extend routing:

```yaml
# eventbus.yaml
polling_interval: 30          # seconds (default: 60)
max_chain_depth: 5             # prevent infinite loops (default: 5)
dedup_window: 3600             # seconds, same event type dedup (default: 3600)
timeout: 1800                  # seconds, processing timeout (default: 1800)

routes:
  # Override default routes
  DATA_GAP: research-team
  
  # Add new event types
  TRANSLATION_NEEDED: content-team
  LEGAL_REVIEW: legal-team
  COST_ANALYSIS: finance-team

  # Multiple targets (fan-out)
  SECURITY_INCIDENT:
    - arc-team
    - notify-user
```

---

## Safety Rules

1. **Max chain depth: 5** — A→B→C→D→E stops. Prevents infinite event loops.
2. **Dedup window: 60min** — Same `source_team + event_type + context` won't re-trigger within the window.
3. **CRITICAL = notify user** — `severity: CRITICAL` events auto-notify the user in addition to routing.
4. **Failed = human intervention** — Events in `failed/` require manual resolution.
5. **Immutable pending events** — Only the Event Bus moves files out of `pending/`. Teams don't modify them.
6. **Processing timeout: 30min** — Events in `processing/` longer than 30min auto-fail with notification.

---

## OpenClaw Integration (Cron Job)

### Option 1: OpenClaw cron (recommended)

Add to your OpenClaw config:

```yaml
# ~/.openclaw/config.yaml
cron:
  - name: event-bus-poll
    schedule: "*/1 * * * *"    # every minute
    command: "python -m eventbus run --once"
```

### Option 2: System cron

```bash
crontab -e
# Add:
* * * * * cd /path/to/workspace && python -m eventbus run --once >> /tmp/eventbus.log 2>&1
```

### Option 3: Background daemon

```bash
python -m eventbus run &
```

---

## FAQ

**Q: What happens if no team matches the event type?**
A: Event stays in `pending/`. Bus logs a warning. Add routing in `eventbus.yaml` or use a supported event type.

**Q: Can I add custom event types?**
A: Yes. Add them to `eventbus.yaml` under `routes:`. Any string works as an event type.

**Q: What if two events target the same team simultaneously?**
A: Both get dispatched. The target team's CONDUCTOR handles task prioritization.

**Q: How do I replay a failed event?**
A: Move it back to `pending/`: `mv events/failed/xxx.yaml events/pending/`

**Q: Can events carry file attachments?**
A: No. Use `data_path` in the event YAML to reference files in the workspace.

**Q: How do I stop the event bus?**
A: `Ctrl+C` if running in foreground, or `kill $(cat /tmp/eventbus.pid)` for daemon mode.

**Q: Does this work across machines?**
A: Not yet. Events are local filesystem files. For distributed setups, sync the `events/` directory (rsync, Dropbox, git).

---

## Watchdog

智能监控系统，检测卡死的事件链并自动修复。

### 5种检查

| 检查类型 | 说明 | 级别 | 自动修复 |
|---|---|---|---|
| `STALE_PENDING` | pending/中事件超过5分钟未dispatch | WARNING→CRITICAL | ✅ 调用`run_once()` |
| `STALE_PROCESSING` | processing/中事件超过30分钟 | CRITICAL | ✅ 移到failed/ + 写retry事件 |
| `CHAIN_BROKEN` | resolved事件有callback但无后续事件 | CRITICAL | ✅ 重新emit callback事件 |
| `FORMAT_ERROR` | YAML解析失败或缺少必须字段 | WARNING | ✅ 移到failed/ |
| `BUS_DOWN` | EventBus进程/心跳丢失 | WARNING/CRITICAL | ❌ 需手动重启 |

### CLI用法

```bash
# 运行一次检查
python -m eventbus watchdog

# 运行检查 + 自动修复
python -m eventbus watchdog --fix

# 持续监控（默认每2分钟）
python -m eventbus watchdog --loop

# 自定义间隔（60秒）
python -m eventbus watchdog --loop --interval 60
```

### 自动修复机制

- **幂等性**：多次运行不会产生重复修复
- **重试上限**：每个事件最多自动重试2次（`max_auto_retries`）
- **链路恢复**：读取resolved事件的callback字段，自动emit后续事件
- **processing超时**：原事件移到failed/，新retry事件写入pending/并标注`[Watchdog auto-retry]`

### 与OpenClaw cron集成

```bash
# 每5分钟运行一次watchdog检查+修复
*/5 * * * * cd /path/to/workspace && python -m eventbus watchdog --fix >> /tmp/watchdog.log 2>&1
```

或使用OpenClaw内置cron：
```yaml
# openclaw.yaml
cron:
  - schedule: "*/5 * * * *"
    command: "python -m eventbus watchdog --fix"
    label: "eventbus-watchdog"
```
