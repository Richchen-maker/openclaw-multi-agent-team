# Team Router — 多团队路由机制

## 目录结构

团队位于 `examples/` 目录：

```
examples/
├── ecommerce-team/        # 🛒 电商选品
├── data-collection-team/  # 📡 数据采集
├── arc-team/              # 🛡️ 安全攻防
├── content-team/          # 📝 内容生产
└── intelligence-team/     # 🔍 情报分析
```

## 双轨路由

### Track 1: 静态路由（DEFAULT_ROUTES）

硬编码在 `framework/eventbus/router.py`：

```python
DEFAULT_ROUTES = {
    "DATA_GAP":           {"target_team": "data-collection-team", "target_mode": "A"},
    "CRAWL_BLOCKED":      {"target_team": "arc-team",             "target_mode": "C"},
    "CRAWL_STRATEGY":     {"target_team": "arc-team",             "target_mode": "B"},
    "DEFENSE_REPORT":     {"target_team": "data-collection-team", "target_mode": "A"},
    "DATA_READY":         {"target_team": "ecommerce-team",       "target_mode": "A"},
    "ANOMALY":            {"target_team": "data-collection-team", "target_mode": "B"},
    "MARKET_SIGNAL":      {"target_team": "ecommerce-team",       "target_mode": "A"},
    "SECURITY_INCIDENT":  {"target_team": "arc-team",             "target_mode": "C"},
}
```

### Track 2: 动态路由（Registry）

`framework/eventbus/registry.py` 自动扫描所有团队的 `capabilities.yaml`。

**扫描路径**：
```
workspace下所有 *-team/ 目录
+ examples/*-team/
+ teams/*
```

**capabilities.yaml 格式**：
```yaml
team: my-team
description: "团队描述"
capabilities:
  - event_type: MY_EVENT
    modes: [A, B, C]
    description: "处理MY_EVENT事件"
    priority: 10    # 多团队能处理同一事件时，priority高的优先
```

### 路由优先级

```
1. 构造时显式传入 routes        → 最高优先
2. Registry动态扫描结果         → 有capabilities.yaml就用
3. DEFAULT_ROUTES静态表         → 兜底
```

Router初始化逻辑（`router.py`）：
```python
class Router:
    def __init__(self, routes=None, workspace_dir=None):
        if routes is not None:
            self.routes = routes                    # 显式覆盖
        elif workspace_dir is not None:
            reg = Registry(workspace_dir)
            count = reg.scan()
            if count > 0:
                self.routes = reg.get_all_routes()  # 动态发现
            else:
                self.routes = dict(DEFAULT_ROUTES)  # 静态兜底
        else:
            self.routes = dict(DEFAULT_ROUTES)
```

## 路由查询

```bash
# CLI查看某事件类型的路由
PYTHONPATH=framework python3 -m eventbus route DATA_GAP

# CLI查看Registry扫描结果
PYTHONPATH=framework python3 -m eventbus registry --scan
```

## 新团队接入

零代码接入流程：

1. 创建目录 `examples/my-team/`
2. 创建 `capabilities.yaml`（声明能处理哪些event_type）
3. 创建团队模板（ORCHESTRATOR.md + templates/）
4. Registry自动发现 → EventBus自动路由

**不需要修改任何框架代码。**

## 架构图

```
                    ┌──────────────┐
                    │   EventBus   │
                    │  bus.py      │
                    └──────┬───────┘
                           │ event_type
                           ▼
                    ┌──────────────┐
                    │    Router    │
                    │  router.py   │
                    └──┬───────┬───┘
                       │       │
            ┌──────────┘       └──────────┐
            ▼                             ▼
    ┌───────────────┐             ┌───────────────┐
    │ DEFAULT_ROUTES│             │   Registry    │
    │  (静态表)      │             │ (capabilities │
    │               │             │  .yaml扫描)    │
    └───────────────┘             └───────────────┘
                                         │
                              ┌──────────┼──────────┐
                              ▼          ▼          ▼
                         ecommerce  data-coll    arc-team
                           -team     -team         ...
```
