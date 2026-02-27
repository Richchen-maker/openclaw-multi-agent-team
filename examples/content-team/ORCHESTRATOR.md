# 内容创作团队 Orchestrator 执行协议

当老板说"启动内容团队"或"帮我做一批内容"时，your lead agent作为CONDUCTOR执行以下协议。

## 架构

```
[老板] ←→ Telegram ←→ [your lead agent CONDUCTOR / opus]
                           ↓ 调度
              4个专业Agent (sub-agent)
              + 黑板系统 (共享状态)
```

## 目标平台

- 小红书（图文/视频笔记）
- 抖音（短视频脚本）
- 公众号（长文/深度内容）
- 视频号（短视频脚本，复用抖音+微信生态适配）

## 运行模式

### 模式A: 内容批量生产（Full Pipeline）
老板说"围绕话题X做一批内容"或"给品牌Y做内容规划"时触发。

### 模式B: 热点追踪（Event-Driven）
RESEARCHER发现热点或老板说"这个热点能不能蹭"时触发。

### 模式C: 内容翻新（Reactive）
老板说"这篇爆了，做一系列"或"竞品这个内容火了"时触发。

---

## 模式A: 内容全链路 — 执行步骤

### Step 0: 初始化
1. 读取老板指定的 [话题/品牌/产品/方向]
2. 初始化 blackboard/ 文件（如已有内容则保留历史，追加新任务）
3. 更新 TASKS.md 中的 Target
4. 创建 output/ 目录
5. **工具健康检查**：
   ```bash
   web_search query="test" count=1
   ```
   记录可用/不可用工具 → 写入 blackboard/ALERTS.md
6. **构建 task prompt**（关键！Sub-agent不继承skills和workspace文件）：
   Lead必须在每个agent的task prompt中注入：
   - TOOL-BOOTSTRAP.md 完整内容
   - 对应角色模板完整内容（替换 {{TARGET}} 为实际目标, {{PLATFORMS}} 为目标平台）
   - 健康检查结果
   - 工作目录路径
   
   **prompt拼接顺序**：
   ```
   [1] TOOL-BOOTSTRAP.md 全文
   [2] 角色模板全文（替换{{TARGET}}和{{PLATFORMS}}后）
        ⚠️ 必须包含：🔴 红队自检 / 📊 置信度分级 / 📋 输入校验
   [3] 补充上下文（前序角色的关键产出摘要）
   ```

   **⛔ 禁止精简模板注入**：不得删减质量控制section。
   用 `read` 工具读取完整模板 → 替换变量 → 拼接到 task prompt。

7. **Spawn前置检查清单**：
   ```
   □ TOOL-BOOTSTRAP.md 全文已注入
   □ 角色模板全文已注入（含红队/置信度/输入校验）
   □ {{TARGET}} 和 {{PLATFORMS}} 已替换
   □ 前序产出已注入（如有依赖）
   □ blackboard/ 路径正确
   ```

### Step 1: 启动 RESEARCHER
```
sessions_spawn:
  - label: "content-researcher"
    mode: "run"
    runTimeoutSeconds: 600
    task: [TOOL-BOOTSTRAP + templates/01-researcher.md]
```

完成后 CONDUCTOR 审核产出，将受众画像+话题清单写入 blackboard/AUDIENCE-INSIGHTS.md。

### Step 2: 并行启动 WRITER + EDITOR（部分并行）
依赖 Step 1 产出（受众画像 + 话题清单 + 竞品内容分析）：
```
sessions_spawn (并行):
  - label: "content-writer"
    mode: "run"
    runTimeoutSeconds: 600
    task: [TOOL-BOOTSTRAP + templates/02-writer.md + Step1关键产出]
    
  - label: "content-editor"
    mode: "run"
    runTimeoutSeconds: 600
    task: [TOOL-BOOTSTRAP + templates/03-editor.md + Step1关键产出(SEO关键词部分)]
```

**并行说明**：
- WRITER 根据研究结果创作内容草稿
- EDITOR 同时基于RESEARCHER的SEO关键词做关键词库+审核标准准备
- WRITER完成后，EDITOR在同一session中对草稿做最终审核（CONDUCTOR转交草稿）

### Step 3: EDITOR 审核 WRITER 产出
CONDUCTOR 将 WRITER 草稿注入 EDITOR 的补充任务：
```
sessions_spawn:
  - label: "content-editor-review"
    mode: "run"
    runTimeoutSeconds: 600
    task: [TOOL-BOOTSTRAP + templates/03-editor.md(审核模式) + WRITER产出全文]
```

### Step 4: PUBLISHER 平台适配 + 排期
依赖 Step 3 审核通过的内容：
```
sessions_spawn:
  - label: "content-publisher"
    mode: "run"
    runTimeoutSeconds: 600
    task: [TOOL-BOOTSTRAP + templates/04-publisher.md + EDITOR审核后的最终内容]
```

### Step 5: CONDUCTOR 审核 + 推送
1. 读取 PUBLISHER 输出（各平台适配版本 + 排期表）
2. 交叉校验：WRITER内容策略 ↔ EDITOR的SEO建议 是否一致
3. 检查各平台版本是否符合字数/格式限制
4. 生成执行摘要 → 推送老板

---

## 依赖图

```
RESEARCHER (受众画像 + 话题 + 竞品 + SEO关键词)
     │
     ├──→ WRITER (内容创作)──┐
     │                       ├──→ EDITOR (审核修改)──→ PUBLISHER (平台适配+排期)
     └──→ EDITOR (关键词库)──┘
```

**关键约束**：
- RESEARCHER 必须先完成，后续所有角色依赖其产出
- WRITER 和 EDITOR(关键词库准备) 可并行
- EDITOR(审核) 必须等 WRITER 完成
- PUBLISHER 必须等 EDITOR 审核完成

---

## 模式B: 热点追踪

```
Step 1: spawn RESEARCHER → 热点分析（时效性、契合度、风险）
Step 2: 如果热点值得追 →
  spawn WRITER（快速出稿，1-2篇）
  spawn EDITOR（快速审核）
Step 3: spawn PUBLISHER（紧急发布，优先小红书/抖音）
Step 4: CONDUCTOR 推送给老板审批
```

**热点时效约束**：全流程≤2小时内完成，否则热点过期。

## 模式C: 内容翻新

```
Step 1: spawn RESEARCHER（分析爆款原因 + 可延伸方向）
Step 2: spawn WRITER（基于爆款做系列内容 3-5篇）
Step 3: spawn EDITOR → PUBLISHER
Step 4: CONDUCTOR 推送
```

---

## 冲突仲裁协议

当两个Agent结论冲突时，CONDUCTOR按以下优先级裁决：

1. **数据权重**: 有量化数据支撑的结论 > 定性判断
2. **平台实测**: 来自实际平台数据（点赞/收藏/评论）> 理论分析
3. **受众反馈**: 用户真实反馈 > 内容创作者直觉
4. **保守原则**: 不确定时，选择风险更低的表达
5. **记录**: 所有仲裁决定写入 DECISIONS.md，附理由

---

## 进度通知
每个Step完成后通知老板。
格式：`[Step X/5 完成] → 关键产出: XXX → 下一步: Step Y`

## 产出文件清单

| 文件 | 产出者 | 内容 |
|------|--------|------|
| output/00-executive-summary.md | CONDUCTOR | 执行摘要 |
| output/01-research-report.md | RESEARCHER | 受众+话题+竞品分析报告 |
| output/02-content-drafts.md | WRITER | 内容草稿包（多篇） |
| output/03-editor-review.md | EDITOR | 审核报告+修改后终稿 |
| output/04-publish-plan.md | PUBLISHER | 平台适配版本+发布排期 |
