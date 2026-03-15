# 知识衰减引擎（Knowledge Decay Engine — KDE）

> TTL不是标签，是会执行的引擎。
> 信息有保质期。过期信息不如没有信息——它给你虚假的确定性。
> 本协议定义知识的生命周期管理。

---

## 衰减规则

### experience-db 文件级 TTL

| 文件 | 衰减周期 | 衰减方式 | 说明 |
|------|---------|---------|------|
| failure-cases.md | 90天 | 降级归档 | 超过90天未复现的FC移入archive/，保留索引 |
| routing-patterns.md | 60天 | 标记陈旧 | 超过60天未被引用的路由经验加[STALE]标记 |
| team-performance.md | 30天 | 滑动窗口 | 只保留最近30天的任务评分，旧数据归档 |
| step-efficiency.md | 30天 | 滑动窗口 | 只保留最近30天的效率数据 |
| methodology-library.md | ∞ | 永久 | 方法论不过期，但可被更优方法论标记[SUPERSEDED] |
| evolution-ledger.md | ∞ | 永久 | 进化轨迹是审计资产，不可删除 |
| prompt-evolution.md | 模型换代时 | 全量审查 | 换模型时全部prompt记录需重新验证 |
| capability-frontier.md | 30天 | 状态审查 | 🟡状态超过30天未推进→标记[STALLED] |
| metrics.md | 30天 | 滑动窗口 | 只保留最近30天 |

### memory/ 文件级 TTL

| 类型 | 衰减周期 | 衰减方式 |
|------|---------|---------|
| 日常记录(YYYY-MM-DD.md) | 30天 | 压缩摘要 → 只保留"教训"和"决策"段落 |
| 专题记录(YYYY-MM-DD-topic.md) | 90天 | 降级 → 精华提取到对应skill |
| 方法论/永久记录 | ∞ | 不衰减 |
| 用户偏好/决策 | ∞ | 不衰减，但可被新决策覆盖 |

### 知识条目级 TTL（Gene 7）

| 数据类型 | TTL | 超期处理 |
|---------|-----|---------|
| 实体信息(公司/产品) | 90天 | 标记[UNVERIFIED]，下次引用前必须重新验证 |
| 价格/库存/排名 | 24小时 | 直接标记[EXPIRED]，禁止引用 |
| 技术趋势/预测 | 30天 | 标记[STALE]，引用时附带衰减警告 |
| 关系/合作/竞争格局 | 180天 | 标记[UNVERIFIED] |
| 政策/法规 | 365天 | 标记[CHECK_UPDATE] |
| 方法论/框架/模型 | ∞ | 被更优方案替代时标记[SUPERSEDED] |

---

## 衰减执行机制

### 自动触发
1. **Step 1.5经验召回时**：读取文件的同时检查条目日期，自动跳过[EXPIRED]条目
2. **Step 11系统自检时**：扫描全部experience-db和memory，执行TTL规则
3. **月度首日**：全量衰减扫描

### Pattern Reference文件膨胀检查（v5.3.1新增）

```
阈值规则：
  🟢 <500行：健康
  🟡 500-800行：监控，下次编辑时检查是否有可合并section
  🔴 >800行：强制压缩，执行以下操作：
    1. 合并重复/覆盖关系的section（如旧版DNA继承被新版覆盖）
    2. Prompt模板中冗余注释删除（保留模板框架，删除解释性文字）
    3. 示例从3个缩减到1个（典型场景保留，非典型移入archive/）
    4. 已被全局化的section标注[→DNA底座]引用，不在Pattern内重复

当前状态（2026-03-04 压缩后）：
  🟡 pattern-intelligence.md: 847行 (H源头,内容不可压)
  🟡 pattern-content-matrix.md: 819行 (H基因抽取+Gene1压缩)
  🟡 pattern-patent.md: 822行 (H基因抽取)
  🟡 pattern-tech-eval.md: 765行 (H基因抽取+Gene1压缩)
  🟢 pattern-competitive.md: 630行 (H基因抽取)
  🟢 pattern-business-plan.md: 468行 (H基因抽取+Gene1压缩+DNA压缩)
  🟢 pattern-ecommerce.md: 343行
  新增公共定义: h-gene-common.md (避免6文件重复)
```

### 手动触发
- 用户说"清理一下"/"整理memory"
- 系统自检发现噪声比>30%
- Pattern reference文件行数超过🔴阈值

### 执行步骤
```
1. 扫描目标目录（experience-db/ + memory/）
2. 对每个文件/条目检查最后更新日期
3. 按TTL规则标记状态：[STALE] / [EXPIRED] / [UNVERIFIED]
4. [EXPIRED]条目移入archive/（带移入日期和原因）
5. 生成衰减报告：清理了X条，归档了Y条，标记了Z条
6. 更新进化账本：记录知识库健康度指标
```

---

## 知识库健康度指标

| 指标 | 健康 | 警告 | 危险 |
|------|------|------|------|
| [EXPIRED]条目占比 | <5% | 5-15% | >15% |
| [STALE]条目占比 | <10% | 10-25% | >25% |
| 30天内无更新的文件数 | <3 | 3-5 | >5 |
| archive/归档条目增长率 | 稳定 | 加速 | 爆发(说明活跃知识在大量过期) |

---

## 压缩摘要协议

当日常记录(YYYY-MM-DD.md)超过30天TTL时，不是删除，而是压缩：

### 保留
- 用户的决策和偏好变更
- 失败案例和教训
- 方法论发现
- 系统架构变更
- 未完成的TODO

### 删除
- 具体执行步骤细节
- 中间状态的调试信息
- 工具输出的raw数据
- 已被后续记录覆盖的信息

### 压缩格式
```markdown
# YYYY-MM-DD [COMPRESSED 压缩于YYYY-MM-DD]
## 关键决策: {列表}
## 教训: {列表}
## 方法论: {列表}
## 架构变更: {列表}
## 未完成: {列表}
```
