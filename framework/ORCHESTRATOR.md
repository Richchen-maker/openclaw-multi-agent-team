# ORCHESTRATOR Protocol — CONDUCTOR执行协议

## CONDUCTOR职责

CONDUCTOR是每支团队的领导Agent，负责：

1. **任务分解** — 接收用户指令 → 拆解为可并行/串行的子任务
2. **角色Dispatch** — 将子任务分配给合适的Role（sub-agent）
3. **冲突仲裁** — 多个Role产出矛盾时，基于数据做裁决
4. **质量门控** — 检查每个Role的产出是否满足标准
5. **Event Bus交互** — 跨团队协作的事件发射和响应

## 执行模式

| Mode | 触发 | 流程 |
|------|------|------|
| **Full Pipeline** | "Run team on X" | CONDUCTOR → 并行dispatch → 串行阶段 → 最终决策 |
| **Event-Driven** | 事件触发 | EventBus路由 → CONDUCTOR → 定向specialist → 事件写回 |
| **Reactive** | 外部触发 | CONDUCTOR → 并行分析 → 快速决策 |

## Event Bus集成

### 跨团队协作通过Event Bus实现

旧方式（已废弃）：`blackboard/CROSS-TEAM-HANDOFF.md` 文件交接
新方式：Event Bus事件驱动

**CONDUCTOR的Event Bus职责**：

1. **事件发射** — 团队发现需要其他团队协助时，写事件到 `events/pending/`
2. **事件响应** — 收到路由来的事件时，分解并分配给内部Role
3. **结果写回** — Role完成后，写回结果事件（含chain_id链路追踪）
4. **链深度管理** — 每次写回 chain_depth + 1，防止无限递归

### Dispatch决策树

```
收到任务/事件
    │
    ├─ 是内部任务？
    │   ├─ YES → 分解 → dispatch给内部Role
    │   └─ NO  → 判断是否需要跨团队
    │
    ├─ 需要跨团队？
    │   ├─ YES → 检查chain_depth < max(5)
    │   │   ├─ OK → 通过templates.py生成标准事件 → 写入events/pending/
    │   │   └─ EXCEEDED → 标记failed，报告用户
    │   └─ NO → 内部处理
    │
    └─ 处理完成
        ├─ 需要回传？→ 写回结果事件（DATA_READY/DEFENSE_REPORT等）
        └─ 最终结果？→ 汇总报告 → 推送用户
```

### 事件写回标准

使用 `framework/eventbus/templates.py` 生成标准化事件：

```python
from eventbus.templates import generate_event_script

script = generate_event_script(
    event_type="DATA_READY",
    source_team="data-collection-team",
    source_role="SPIDER",
    severity="MEDIUM",
    chain_depth=current_depth + 1,
    body="采集完成，共1200条数据...",
    workspace_dir=workspace,
    chain_id=current_chain_id,
    parent_event_id=current_event_id,
)
```

或直接用CLI：

```bash
PYTHONPATH=framework python3 -m eventbus emit DATA_READY \
  --source-team data-collection-team \
  --source-role SPIDER \
  --severity MEDIUM \
  --chain-depth 1 \
  --chain-id "chain-xxx" \
  --context "采集完成，共1200条数据"
```

## 内部Dispatch规则

1. **并行优先** — 独立子任务必须并行dispatch，不串行等待
2. **Red-team** — 每个Role的产出必须包含自我批评
3. **Confidence标注** — 所有结论标注 HIGH/MEDIUM/LOW 置信度
4. **数据优先** — 冲突时量化数据胜出
5. **来源标注** — 无来源的数据点 = 无效

## Blackboard协作（团队内部）

团队内部Role之间仍使用Blackboard（共享文件）协作：

```
blackboard/
├── task-brief.md        # CONDUCTOR写入的任务简报
├── {role}-output.md     # 各Role的产出
├── conflict-log.md      # 冲突记录
└── final-decision.md    # 最终决策
```

**跨团队协作 = Event Bus（事件驱动）**
**团队内部协作 = Blackboard（文件共享）**
