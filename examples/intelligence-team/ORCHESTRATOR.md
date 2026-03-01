# Intelligence Team — 竞争情报自动化

> 定时监控竞品动态，自动联动电商团队。

## Team Identity
- **Team:** intelligence-team
- **Mission:** 持续监控竞品价格、上新、广告投放变化，自动生成市场信号
- **Modes:**
  - Mode A: 定时巡检（cron触发，扫描竞品变化）
  - Mode B: 深度调查（接收MARKET_SIGNAL后深入分析特定竞品）
  - Mode C: 预警响应（检测到异常价格波动/竞品大动作时紧急通知）

## Roles
| Role | Function |
|------|----------|
| SCOUT | 竞品信息采集（价格、销量、评论变化） |
| ANALYST | 竞品数据分析（趋势、异常检测、对比） |
| SENTINEL | 异常监控（价格战预警、新品上线提醒） |
| STRATEGIST | 竞争策略建议（基于情报输出行动方案） |
| CONDUCTOR | 指挥调度 |

## Cross-Team Event Protocol

### Emit Events
| Situation | Event Type | Target |
|-----------|-----------|--------|
| 发现竞品异常价格波动 | MARKET_SIGNAL | ecommerce-team |
| 需要采集竞品详细数据 | DATA_GAP | data-collection-team |
| 采集被拦截 | CRAWL_BLOCKED | arc-team |

### Receive Events
| Event Type | Handler |
|-----------|---------|
| MARKET_SIGNAL | Mode B: ANALYST深入分析 |
| DATA_READY | ANALYST消费数据，更新竞品画像 |

## Execution Flow

### Mode A: 定时巡检
```
CONDUCTOR → SCOUT(采集竞品快照) → SENTINEL(对比历史数据) → ANALYST(异常检测)
  → 有异常 → emit MARKET_SIGNAL → ecommerce-team
  → 无异常 → 更新竞品画像，静默
```

### Mode B: 深度调查
```
CONDUCTOR → ANALYST(深入分析特定竞品) → STRATEGIST(输出竞争策略建议)
  → 写入 knowledge/market/{competitor}.md
```

### Mode C: 预警响应
```
SENTINEL(实时检测) → 价格战/大促/新品 → CONDUCTOR → emit MARKET_SIGNAL(severity=HIGH)
```
