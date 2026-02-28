# 数据采集团队 — DISPATCHER 调度协议

> DISPATCHER不是sub-agent，是Lead（鳄策异辉）自身的执行协议。

## 调度决策树

```
老板指令到达
  │
  ├── "采集XXX数据" → 模式A: 指令采集
  │     └── MAPPER → SPIDER → REFINER → WAREHOUSE
  │
  ├── "设置自动采集" / "定时采集" → 模式B: 定时采集
  │     └── 创建cron → SENTINEL监控 → 模式A循环
  │
  ├── "仓库有什么" / "导出数据" → 模式C: 数据查询
  │     └── 读取 warehouse/INDEX.md → 导出/摘要
  │
  ├── 选品团队需要数据 → 模式D: 供给模式
  │     └── 查INDEX → 有且新鲜→直接取 / 过期→触发模式A
  │
  └── SENTINEL告警 → 模式E: 应急处理
        └── 诊断问题 → 修复/暂停/通知老板
```

---

## 模式A: 指令采集 — 执行步骤

### Step 0: 初始化
1. 读取老板指令，提取：目标平台、数据类型、类目范围、时间范围
2. 执行工具健康自检（见 TOOL-BOOTSTRAP.md）
3. 结果写入 blackboard/TOOLKIT-STATUS.md
4. 如果关键工具不可用（Chrome登录态过期等）→ 暂停，通知老板

### Step 1: MAPPER 摸底
```
sessions_spawn:
  label: "dc-mapper"
  mode: "run"
  runTimeoutSeconds: 300
  task: [TOOL-BOOTSTRAP + templates/01-mapper.md + 目标信息]
```
产出：output/01-data-map.md
- 数据源清单
- 字段映射表
- 推荐采集策略

**质量门控：**
```
□ 是否识别出至少1个可用数据源？
□ 字段映射表是否完整？
□ 采集策略是否具体可执行？
→ 缺失任何一项 → 当前session补充，不重新spawn
```

### Step 2: SPIDER 采集
```
sessions_spawn:
  label: "dc-spider"
  mode: "run"
  runTimeoutSeconds: 600
  task: [TOOL-BOOTSTRAP + templates/02-spider.md + MAPPER产出]
```
产出：warehouse/raw/{platform}/{date}/*.json

**质量门控：**
```
□ 原始数据文件是否存在且非空？
□ 数据行数是否合理（不为0，不异常大）？
□ 是否有采集错误记录？
→ 数据为空 → 检查INCIDENTS.md → 决定重试或放弃
```

### Step 3: REFINER 清洗
```
sessions_spawn:
  label: "dc-refiner"
  mode: "run"
  runTimeoutSeconds: 300
  task: [TOOL-BOOTSTRAP + templates/03-refiner.md + SPIDER产出路径 + SCHEMA.md]
```
产出：warehouse/cleaned/{platform}/{date}/*.csv

**质量门控：**
```
□ 清洗后数据字段是否符合SCHEMA.md？
□ 空值率是否<10%？
□ 是否有去重报告？
□ 数据行数与原始数据比例是否合理？
```

### Step 4: WAREHOUSE 入库
```
sessions_spawn:
  label: "dc-warehouse"
  mode: "run"
  runTimeoutSeconds: 300
  task: [TOOL-BOOTSTRAP + templates/04-warehouse.md + REFINER产出路径]
```
产出：
- warehouse/INDEX.md 更新
- warehouse.db 更新（如使用SQLite）

### Step 5: 交付
1. 读取 warehouse/INDEX.md 确认入库成功
2. 生成数据摘要（行数、字段、时间范围、数据样本前5行）
3. 推送给老板

---

## 模式B: 定时采集

### 设置
1. 老板指定：类目列表 + 采集频率 + 数据类型
2. 写入 presets/{preset-name}.yml
3. 创建cron任务：
```
cron add:
  name: "数据采集-{preset-name}"
  schedule: { kind: "cron", expr: "0 9 * * *", tz: "Asia/Shanghai" }
  payload: { kind: "agentTurn", message: "执行数据采集预设: {preset-name}" }
  sessionTarget: "isolated"
```

### 执行
cron触发 → DISPATCHER读取preset → 按模式A执行

---

## 模式D: 供给选品团队

选品团队需要数据时，DISPATCHER检查：
```
1. 读取 warehouse/INDEX.md
2. 查找匹配的数据集（平台+类目+数据类型）
3. 检查数据新鲜度：
   - <24h → 直接返回路径
   - 24h-7d → 返回路径 + 标注 [数据非最新，采集于X天前]
   - >7d → 触发模式A重新采集
```

---

## 冲突仲裁

1. 多数据源数值冲突 → 取官方平台数据（生意参谋>第三方>推算）
2. 采集失败vs放弃 → 连续3次失败同一数据源 → 标记为不可用，切换备选
3. 数据质量争议 → REFINER标flag，WAREHOUSE照入库但标注可信度

---

## 进度通知

每个Step完成后通知老板：
```
[Step X/5] MAPPER完成 → 识别到3个数据源，推荐Chrome Extension采集
[Step X/5] SPIDER完成 → 采集到1,247行原始数据
[Step X/5] REFINER完成 → 清洗后1,103行有效数据（去重144行）
[Step X/5] WAREHOUSE完成 → 已入库，数据ID: sycm-fishing-20260227
```
