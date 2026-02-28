# Cross-Team Collaboration Guide

Complete guide to deploying and using the Event Bus for automated cross-team workflows.

---

## Part 1: Concepts

### Why Cross-Team Collaboration?

Single teams hit walls. E-commerce needs data it can't collect. Data collection hits anti-bot defenses it can't bypass. Each team is excellent at its specialty but helpless outside it.

The Event Bus connects teams automatically. When one team hits a wall, it writes an event. The bus routes it to whichever team can solve it. No human intervention needed.

### How Event Bus Works

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│  Team A      │  event  │  Event Bus   │  route   │  Team B      │
│              │ ──────→ │              │ ──────→  │              │
│  hits wall   │         │  polls       │         │  solves it   │
│  writes event│ ←────── │  pending/    │ ←────── │  writes back │
│  reads result│  result │              │  result  │              │
└──────────────┘         └──────────────┘         └──────────────┘
```

### Event Lifecycle

```
pending → processing → resolved
                    ↘ failed (needs human intervention)
```

| Status | Meaning | Location |
|--------|---------|----------|
| `pending` | Waiting for dispatch | `events/pending/` |
| `processing` | Dispatched to target team, in progress | `events/processing/` |
| `resolved` | Completed successfully | `events/resolved/` |
| `failed` | Target team couldn't handle it | `events/failed/` |

---

## Part 2: Deployment

### Directory Structure

```
workspace/
├── events/
│   ├── pending/       # New events land here
│   ├── processing/    # Currently being handled
│   ├── resolved/      # Done (retained 7 days)
│   └── failed/        # Needs manual fix
├── ecommerce-team/
├── data-collection-team/
├── arc-team/
└── framework/
    └── eventbus/      # Event Bus module
```

### Create Event Directories

```bash
mkdir -p events/{pending,processing,resolved,failed}
```

Expected output: (no output = success)

### Install Dependencies

```bash
pip install pyyaml
```

Expected output:
```
Successfully installed PyYAML-6.0.x
```

### Verify Installation

```bash
python -m eventbus status
```

Expected output:
```
Event Bus Status
────────────────
  pending:    0
  processing: 0
  resolved:   0
  failed:     0
```

---

## Part 3: Configuration

### Default Routing Table

8 event types, pre-configured:

| Event Type | Target Team | Use Case |
|-----------|-------------|----------|
| `DATA_GAP` | data-collection-team | Missing data for analysis |
| `CRAWL_BLOCKED` | arc-team | Spider hit anti-bot |
| `CRAWL_STRATEGY` | arc-team | Need defense assessment for new platform |
| `DEFENSE_REPORT` | data-collection-team | ARC bypass strategy ready |
| `DATA_READY` | ecommerce-team | Cleaned data available |
| `ANOMALY` | data-collection-team | Data source changed/broken |
| `MARKET_SIGNAL` | ecommerce-team | External market event detected |
| `SECURITY_INCIDENT` | arc-team | Account ban / IP blacklist |

### Custom Routing (eventbus.yaml)

Create `eventbus.yaml` in workspace root:

```yaml
polling_interval: 30
max_chain_depth: 5
dedup_window: 3600
timeout: 1800

routes:
  DATA_GAP: data-collection-team          # default
  CRAWL_BLOCKED: arc-team                 # default
  TRANSLATION_NEEDED: content-team        # custom
  LEGAL_REVIEW: legal-team                # custom
  COST_ANALYSIS: finance-team             # custom
```

### Adding a New Event Type

Add one line to `routes:` in `eventbus.yaml`:

```yaml
routes:
  MY_NEW_EVENT: my-target-team
```

Then emit it:

```bash
python -m eventbus emit MY_NEW_EVENT \
  --source-team my-source-team \
  --source-role MY_ROLE \
  --severity MEDIUM \
  --context "description of what happened"
```

### Adding a New Team to Routing

Just reference it in `routes:`. No registration needed — the team directory must exist in your workspace.

```yaml
routes:
  LEGAL_REVIEW: legal-team    # legal-team/ must exist in workspace
```

---

## Part 4: Usage

### Emit an Event (Manual Test)

```bash
python -m eventbus emit DATA_GAP \
  --source-team ecommerce-team \
  --source-role RADAR \
  --severity HIGH \
  --context "缺少蓝牙耳机TOP20竞品价格数据"
```

Expected output:
```
✅ Event created: events/pending/20260228-093000-DATA_GAP.yaml
   Type: DATA_GAP
   Route: ecommerce-team/RADAR → data-collection-team
```

Verify the file:

```bash
cat events/pending/20260228-*-DATA_GAP.yaml
```

Expected output:
```yaml
event_id: "evt-20260228-001"
event_type: DATA_GAP
severity: HIGH
source_team: ecommerce-team
source_role: RADAR
timestamp: "2026-02-28T09:30:00Z"
status: pending
target_team: data-collection-team
context: "缺少蓝牙耳机TOP20竞品价格数据"
```

### Start Event Bus Polling

```bash
python -m eventbus run
```

Expected output:
```
🚌 Event Bus started (polling every 60s)
   Watching: events/pending/
   Routes loaded: 8 event types
[09:31:00] Processing: evt-20260228-001 DATA_GAP → data-collection-team
[09:31:00] Moved to: events/processing/20260228-093000-DATA_GAP.yaml
```

### Check Event Status

```bash
python -m eventbus status
```

Expected output:
```
Event Bus Status
────────────────
  pending:    0
  processing: 1
  resolved:   0
  failed:     0

Active Events:
  [processing] evt-20260228-001  DATA_GAP  → data-collection-team  (1m ago)
```

---

## Part 5: Complete 5-Step Cross-Team Example

Reproducing the full chain from the README: e-commerce category assessment triggers data collection, hits anti-bot, ARC breaks through, data flows back.

### Step 1: E-commerce RADAR Discovers Data Gap

```bash
python -m eventbus emit DATA_GAP \
  --source-team ecommerce-team \
  --source-role RADAR \
  --severity HIGH \
  --context "Analyzing Bluetooth earphone category. Missing: TOP20 competitor 30-day price history and promo frequency from Taobao."
```

Event file created (`events/pending/20260228-100000-DATA_GAP.yaml`):

```yaml
event_id: "evt-20260228-001"
event_type: DATA_GAP
severity: HIGH
source_team: ecommerce-team
source_role: RADAR
timestamp: "2026-02-28T10:00:00Z"
status: pending
target_team: data-collection-team
callback:
  team: ecommerce-team
  resume_role: RADAR
  write_to: "blackboard/MARKET-SIGNALS.md"
context: |
  Analyzing Bluetooth earphone category.
  Missing: TOP20 competitor 30-day price history and promo frequency from Taobao.
  Need: JSON with sku_id, title, price_history[], promo_events[]
```

Expected output:
```
✅ Event created: events/pending/20260228-100000-DATA_GAP.yaml
   Type: DATA_GAP
   Route: ecommerce-team/RADAR → data-collection-team
```

### Step 2: Data Collection SPIDER Gets Blocked

SPIDER starts crawling Taobao, hits slider CAPTCHA at page 3.

```bash
python -m eventbus emit CRAWL_BLOCKED \
  --source-team data-collection-team \
  --source-role SPIDER \
  --severity HIGH \
  --context "Taobao Bluetooth earphone crawl blocked at page 3/20. Slider CAPTCHA + IP rate limit triggered. Platform: taobao.com, Block type: slider_captcha + ip_throttle"
```

Event file (`events/pending/20260228-100500-CRAWL_BLOCKED.yaml`):

```yaml
event_id: "evt-20260228-002"
event_type: CRAWL_BLOCKED
severity: HIGH
source_team: data-collection-team
source_role: SPIDER
timestamp: "2026-02-28T10:05:00Z"
status: pending
target_team: arc-team
target_mode: "C"
callback:
  team: data-collection-team
  resume_role: SPIDER
context: |
  Taobao Bluetooth earphone crawl blocked at page 3/20.
  Slider CAPTCHA + IP rate limit triggered.
  Platform: taobao.com
  Block type: slider_captcha + ip_throttle
  Progress: 3/20 pages collected
```

Expected output:
```
✅ Event created: events/pending/20260228-100500-CRAWL_BLOCKED.yaml
   Type: CRAWL_BLOCKED
   Route: data-collection-team/SPIDER → arc-team
```

### Step 3: ARC Team Breaks Through

ARC analyzes Taobao's defenses, produces bypass strategy.

```bash
python -m eventbus emit DEFENSE_REPORT \
  --source-team arc-team \
  --source-role COMMANDER \
  --severity MEDIUM \
  --context "Taobao bypass strategy ready: 1) Rate limit to 2req/s with random intervals, 2) curl-impersonate Chrome131 fingerprint, 3) Slider CAPTCHA via captcha-recognizer L2 engine, 4) Rotate proxy IP pool. Confidence: HIGH"
```

Event file (`events/pending/20260228-101200-DEFENSE_REPORT.yaml`):

```yaml
event_id: "evt-20260228-003"
event_type: DEFENSE_REPORT
severity: MEDIUM
source_team: arc-team
source_role: COMMANDER
timestamp: "2026-02-28T10:12:00Z"
status: pending
target_team: data-collection-team
callback:
  team: data-collection-team
  resume_role: SPIDER
context: |
  Taobao bypass strategy ready:
  1) Rate limit to 2req/s with random intervals
  2) curl-impersonate Chrome131 fingerprint
  3) Slider CAPTCHA via captcha-recognizer L2 engine
  4) Rotate proxy IP pool
  Confidence: HIGH
```

Expected output:
```
✅ Event created: events/pending/20260228-101200-DEFENSE_REPORT.yaml
   Type: DEFENSE_REPORT
   Route: arc-team/COMMANDER → data-collection-team
```

### Step 4: Data Collection Retries and Succeeds

SPIDER applies ARC's strategy, completes collection.

```bash
python -m eventbus emit DATA_READY \
  --source-team data-collection-team \
  --source-role SPIDER \
  --severity LOW \
  --context "Taobao Bluetooth earphone TOP20 data collected. 20/20 SKUs complete. Cleaned data at: warehouse/cleaned/taobao_bt_earphone/. Format: JSON, 20 records with price_history and promo_events."
```

Event file (`events/pending/20260228-102500-DATA_READY.yaml`):

```yaml
event_id: "evt-20260228-004"
event_type: DATA_READY
severity: LOW
source_team: data-collection-team
source_role: SPIDER
timestamp: "2026-02-28T10:25:00Z"
status: pending
target_team: ecommerce-team
callback:
  team: ecommerce-team
  resume_role: RADAR
  write_to: "blackboard/MARKET-SIGNALS.md"
context: |
  Taobao Bluetooth earphone TOP20 data collected.
  20/20 SKUs complete.
  Cleaned data at: warehouse/cleaned/taobao_bt_earphone/
  Format: JSON, 20 records with price_history and promo_events.
data_path: "warehouse/cleaned/taobao_bt_earphone/"
```

Expected output:
```
✅ Event created: events/pending/20260228-102500-DATA_READY.yaml
   Type: DATA_READY
   Route: data-collection-team/SPIDER → ecommerce-team
```

### Step 5: E-commerce Completes Analysis

RADAR reads the cleaned data, completes the category assessment. No event needed — the chain ends here.

```bash
python -m eventbus status
```

Expected output:
```
Event Bus Status
────────────────
  pending:    0
  processing: 0
  resolved:   4
  failed:     0

Chain: evt-001 → evt-002 → evt-003 → evt-004 (complete)
Total time: 25 minutes
```

**Full chain, zero human intervention. You only said "assess Bluetooth earphone category".**

---

## Part 6: OpenClaw Integration

### Cron Job Auto-Polling

Add to OpenClaw config (`~/.openclaw/config.yaml`):

```yaml
cron:
  - name: event-bus-poll
    schedule: "*/1 * * * *"
    command: "python -m eventbus run --once"
```

This polls `events/pending/` every minute. `--once` runs a single poll cycle then exits (cron handles the loop).

### Inject Event Detection into ORCHESTRATOR.md

Add this block to each team's `ORCHESTRATOR.md`:

```markdown
## Pre-Execution: Event Check

Before executing user commands, scan for inbound events:

1. List files in `events/pending/` where `target_team` matches this team
2. If events found → process them first (event-driven mode)
3. No events → proceed with normal user instruction

## Post-Execution: Event Emission

After execution, check for blockers:

1. Did this execution hit a wall the team can't solve?
2. Yes → emit an event (see Event Type table in framework/eventbus/README.md)
3. Move any completed inbound events to `events/resolved/`
```

### Auto-Emit Events from Roles

Add this to each role's template (e.g., `templates/SPIDER.md`):

```markdown
## Event Protocol

When you encounter a situation you cannot resolve:

- **Data missing** → emit DATA_GAP with what you need
- **Blocked by anti-bot** → emit CRAWL_BLOCKED with platform, block type, progress
- **Data ready** → emit DATA_READY with data path and format
- **Security issue** → emit SECURITY_INCIDENT with details

Use the CLI:
\`\`\`bash
python -m eventbus emit {EVENT_TYPE} \
  --source-team {this-team} \
  --source-role {YOUR_CODENAME} \
  --severity {CRITICAL|HIGH|MEDIUM|LOW} \
  --context "{what happened and what you need}"
\`\`\`

Or write the YAML file directly to `events/pending/`.
```

---

## Part 7: Troubleshooting

### Event stuck in `processing`

**Cause:** Target team started but didn't finish within timeout (default 30min).

**Fix:**
```bash
# Check what's stuck
python -m eventbus list --status processing

# Option 1: Wait longer (increase timeout in eventbus.yaml)
# Option 2: Manually fail and retry
python -m eventbus fail evt-20260228-001 --reason "timeout"
mv events/failed/20260228-*-DATA_GAP.yaml events/pending/
```

### Event chain loop (A→B→A→B...)

**Cause:** Two teams keep emitting events to each other without resolving.

**Fix:** Built-in protection — max chain depth is 5 (configurable). If hit:
```
⚠️ Chain depth limit reached (5). Event evt-20260228-005 moved to failed/.
```

Manual resolution:
```bash
# Check the chain
python -m eventbus list --status failed

# Read the event to understand the loop
cat events/failed/20260228-*-CRAWL_BLOCKED.yaml

# Fix the root cause, then retry
mv events/failed/20260228-*.yaml events/pending/
```

### Route not found for event type

**Cause:** Custom event type not in default routes or `eventbus.yaml`.

**Symptom:**
```
⚠️ No route for event type: TRANSLATION_NEEDED. Event stays in pending.
```

**Fix:** Add routing in `eventbus.yaml`:
```yaml
routes:
  TRANSLATION_NEEDED: content-team
```

Then the next poll cycle picks it up automatically.
