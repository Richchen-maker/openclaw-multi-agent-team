# 电商团队 Orchestrator 执行协议

当老板说"启动电商团队"时，your lead agent作为CONDUCTOR执行以下协议。

## 架构

```
[老板] ←→ Telegram ←→ [your lead agent CONDUCTOR / opus]
                           ↓ 调度
              6个专业Agent (sub-agent)
              + 黑板系统 (共享状态)
```

## 运行模式

### 模式A: 新品上架（Full Pipeline）
老板说"评估品类X"或"上架产品Y"时触发。

### 模式B: 日常运营（Event-Driven）
PULSE检测到异常或老板说"检查产品X数据"时触发。

### 模式C: 竞品应急（Reactive）
老板说"竞品降价了"或"市场有变化"时触发。

---

## 模式A: 新品全链路 — 执行步骤

### Step 0: 初始化
1. 读取老板指定的 [品类/产品/市场方向]
2. 初始化 blackboard/ 文件（如已有内容则保留历史，追加新任务）
3. 更新 TASKS.md 中的 Target
4. 创建 output/ 目录
5. **工具健康检查**：
   ```bash
   mcporter call translate.translate_text text="test" target="zh" source="en" --timeout 15000
   ```
   记录可用/不可用工具 → 写入 blackboard/TOOLKIT-STATUS.md
6. **构建 task prompt**（关键！Sub-agent不继承skills和workspace文件）：
   Lead必须在每个agent的task prompt中注入：
   - TOOL-BOOTSTRAP.md 完整内容
   - 对应角色模板完整内容（替换 {{TARGET}} 为实际目标）
   - 健康检查结果
   - 工作目录路径
   
   **prompt拼接顺序**：
   ```
   [1] TOOL-BOOTSTRAP.md 全文
   [2] TOOLKIT-STATUS.md（本次健康检查结果）
   [3] 角色模板全文（替换{{TARGET}}后）
        ⚠️ 必须包含：🔴 红队自检 / 📊 置信度分级 / 📋 输入校验
   [4] 补充上下文（前序角色的关键产出摘要）
   ```

   **⛔ 禁止精简模板注入**：不得删减质量控制section。
   用 `read` 工具读取完整模板 → 替换变量 → 拼接到 task prompt。

7. **Spawn前置检查清单**：
   ```
   □ TOOL-BOOTSTRAP.md 全文已注入
   □ 角色模板全文已注入（含红队/置信度/输入校验）
   □ {{TARGET}} 已替换
   □ 前序产出已注入（如有依赖）
   □ blackboard/ 路径正确
   ```

### Step 1: 并行启动 RADAR + SCOUT
```
sessions_spawn (并行):
  - label: "ecom-radar"
    mode: "run"
    runTimeoutSeconds: 600
    task: [TOOL-BOOTSTRAP + templates/01-radar.md]
    
  - label: "ecom-scout"
    mode: "run"
    runTimeoutSeconds: 600
    task: [TOOL-BOOTSTRAP + templates/02-scout.md]
```

完成后 CONDUCTOR 合并产出，仲裁冲突（RADAR说红海 vs SCOUT说有机会），写入 DECISIONS.md。

### Step 2: 并行启动 FORGE + BLADE
依赖 Step 1 产出（品类确认 + 竞品数据）：
```
sessions_spawn (并行):
  - label: "ecom-forge"
    mode: "run"
    runTimeoutSeconds: 600
    task: [TOOL-BOOTSTRAP + templates/03-forge.md + Step1关键产出]
    
  - label: "ecom-blade"
    mode: "run"
    runTimeoutSeconds: 600
    task: [TOOL-BOOTSTRAP + templates/04-blade.md + Step1关键产出]
```

### Step 3: ORACLE 综合决策
依赖 Step 1 + Step 2 全部产出：
```
sessions_spawn:
  - label: "ecom-oracle"
    mode: "run"
    runTimeoutSeconds: 600
    task: [TOOL-BOOTSTRAP + templates/06-oracle.md + 全部前序产出]
```

### Step 4: CONDUCTOR 审核 + 推送
1. 读取 ORACLE 决策书
2. 交叉校验：FORGE内容策略 ↔ BLADE定价 是否一致
3. 检查 Kill Criteria 是否具体可量化
4. 生成执行摘要 → 推送老板

---

## 模式B: 日常运营

### 触发: PULSE检测异常 或 老板指令
```
Step 1: spawn PULSE → 数据采集 + 异常检测
Step 2: 根据异常类型，选择性spawn:
  - 流量异常 → RADAR（市场变化？）
  - 转化异常 → FORGE（内容问题？）+ BLADE（价格问题？）
  - 利润异常 → BLADE（成本变化？）
Step 3: spawn ORACLE → 归因 + 决策
Step 4: CONDUCTOR 推送决策给老板
```

## 模式C: 竞品应急

```
Step 1: spawn RADAR（竞品动态确认）+ BLADE（价格弹性分析）并行
Step 2: spawn ORACLE（快速决策）
Step 3: CONDUCTOR 推送应急方案
```

---

## 冲突仲裁协议

当两个Agent结论冲突时，CONDUCTOR按以下优先级裁决：

1. **数据权重**: 有量化数据支撑的结论 > 定性判断
2. **时效性**: 近期数据 > 历史数据
3. **来源可信度**: 官方数据 > 第三方报告 > 推测
4. **保守原则**: 不确定时，选择风险更低的方案
5. **记录**: 所有仲裁决定写入 DECISIONS.md，附理由

---

## 进度通知
每个Step完成后通知老板。
格式：`[Step X/4 完成] → 关键产出: XXX → 下一步: Step Y`

## 产出文件清单

| 文件 | 产出者 | 内容 |
|------|--------|------|
| output/00-executive-summary.md | CONDUCTOR | 执行摘要 |
| output/01-radar-report.md | RADAR | 市场信号报告 |
| output/02-scout-picks.md | SCOUT | 选品清单 |
| output/03-forge-content.md | FORGE | 内容资产包 |
| output/04-blade-pricing.md | BLADE | 定价方案 |
| output/05-pulse-report.md | PULSE | 数据脉搏报告 |
| output/06-oracle-decision.md | ORACLE | 执行决策书 |
