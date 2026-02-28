# 工具引导协议 — 数据采集团队 Sub-agent 标准工具能力包

> 本文件是每个sub-agent的工具能力基座。DISPATCHER在spawn时将本内容+角色模板注入task prompt。

## ⚠️ 全局铁律

### 铁律1: 数据必须可追溯
- 每份采集数据标注：来源平台、采集时间、采集方式、原始URL
- 清洗后数据保留原始数据引用（raw文件路径）
- 未标注来源的数据 → 废弃

### 铁律2: 安全第一
- 每次请求间隔≥3秒（写入代码的sleep，不可省略）
- 单次采集不超过50页
- 检测到验证码/风控 → 立即停止 → 写INCIDENTS.md
- 绝不存储账号密码

### 铁律3: 幂等性
- 同一任务重复执行 → 结果一致（不产生重复数据）
- 中断恢复：从上次断点继续，不从头开始

### 铁律4: 产出规范
- 原始数据 → warehouse/raw/{platform}/{YYYY-MM-DD}/{task_id}.json
- 清洗数据 → warehouse/cleaned/{platform}/{YYYY-MM-DD}/{task_id}.csv
- 所有CSV用UTF-8 BOM编码（Excel中文兼容）
- JSON用pretty print（2空格缩进）

---

## Step 0: 工具自检（DISPATCHER执行，结果注入sub-agent）

```bash
# 1. 网络
web_search query="test" count=1

# 2. Tavily
exec: TAVILY_API_KEY="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" node /Users/rich/.openclaw/workspace/skills/tavily-search/scripts/search.mjs "test" -n 1

# 3. Chrome浏览器状态
browser action=status

# 4. 生意参谋登录态
browser action=navigate targetUrl="https://sycm.taobao.com" profile=chrome
browser action=snapshot → 登录页=❌ / 数据页=✅

# 5. Python3
exec: python3 --version

# 6. SQLite
exec: python3 -c "import sqlite3; print('OK')"

# 7. translate MCP
exec: mcporter call translate.translate_text text="test" target="zh" source="en" --timeout 15000

# 8. 磁盘空间
exec: df -h /Users/rich → 可用>10GB=✅

# 9. warehouse目录
exec: ls warehouse/ → 存在且可写=✅
```

结果写入 `blackboard/TOOLKIT-STATUS.md`

---

## 可用工具清单

### A. 搜索采集类

| 工具 | 调用方式 | 适用角色 |
|------|---------|---------|
| web_search | `web_search query="关键词" count=10` | MAPPER, SPIDER, SENTINEL |
| web_search定向 | `web_search query="关键词 site:1688.com"` | MAPPER, SPIDER |
| web_fetch | `web_fetch url="URL"` | MAPPER, SPIDER, SENTINEL |
| Tavily普通 | `exec: TAVILY_API_KEY="..." node .../search.mjs "query" -n 5` | MAPPER |
| Tavily深度 | 同上加 `--deep` | MAPPER |

### B. 浏览器自动化类

| 工具 | 调用方式 | 适用角色 |
|------|---------|---------|
| browser(openclaw) | `browser action=snapshot/navigate/act` | SPIDER, MAPPER |
| browser(chrome relay) | `browser action=snapshot profile=chrome` | SPIDER |
| SYCM Pro Extension | Chrome插件，自动拦截API数据 | SPIDER |
| SYCM Extension自动采集 | 插件内「自动采集」功能 | SPIDER |

**Chrome Relay使用前提**：
1. 用户已在Chrome中登录目标平台
2. OpenClaw Browser Relay toolbar按钮已点击（badge ON）
3. 使用 `profile=chrome` 参数

### C. 数据处理类

| 工具 | 调用方式 | 适用角色 |
|------|---------|---------|
| Python3 | `exec: python3 -c "代码"` 或 `exec: python3 脚本路径` | REFINER, WAREHOUSE, SPIDER |
| jq | `exec: echo '{}' \| jq '.field'` | REFINER, WAREHOUSE |
| SQLite | `exec: python3 tools/scripts/db.py [command]` | REFINER, WAREHOUSE, SENTINEL |
| translate MCP | `exec: mcporter call translate.translate_text ...` | MAPPER, REFINER |
| 指数还原 | `exec: python3 tools/scripts/index_restore.py [value]` | REFINER |
| 数据校验 | `exec: python3 tools/scripts/validator.py [file]` | REFINER, WAREHOUSE |

### D. 存储输出类

| 工具 | 调用方式 | 适用角色 |
|------|---------|---------|
| read/write | 直接使用 | 全部角色（按权限） |
| feishu_doc | `feishu_doc action=create/append` | DISPATCHER |
| message(telegram) | `message action=send` | DISPATCHER, SENTINEL |
| cron | `cron action=add/list` | DISPATCHER, SENTINEL |

### E. 辅助工具

| 工具 | 调用方式 | 适用角色 |
|------|---------|---------|
| summarize | `exec: summarize "URL"` | MAPPER |
| image | `image` | MAPPER（页面结构截图分析） |

---

## ⛔ 禁止事项

- **禁止调用 sessions_spawn / subagents** — sub-agent不能再spawn子agent
- **禁止存储任何账号密码** — 登录态通过Chrome cookie管理
- **禁止绕过频率限制** — sleep(3)是最低要求
- **禁止修改非warehouse目录的文件** — 除blackboard外不碰其他团队文件
- **禁止调用已标记❌的工具**：cn-ecommerce-search, Perplexity, Firecrawl, Semantic Scholar, xiaohongshu-mcp

---

## 搜索策略

### 生意参谋数据采集
```
1. 确认Chrome登录态有效
2. 通过browser(chrome)导航到目标页面
3. SYCM Pro Extension自动拦截API数据
4. 如需自动翻页 → 使用插件的「自动采集」功能
5. 导出JSON → 存入warehouse/raw/sycm/
```

### 1688供应商数据
```
1. web_search query="产品名 工厂 批发 site:1688.com" count=10
2. web_fetch 抓取搜索结果页（注意：listing详情页反爬严格，可能失败）
3. 失败 → 退回到web_search提取片段信息
4. 存入warehouse/raw/alibaba1688/
```

### 抖音电商趋势
```
1. 使用douyin-hot-trend skill获取热榜
2. web_search query="产品名 抖音 销量 趋势" count=10
3. 存入warehouse/raw/douyin/
```

---

## 文件路径规范

```
warehouse/
├── raw/{platform}/{YYYY-MM-DD}/{task_id}.json     ← 原始数据
├── cleaned/{platform}/{YYYY-MM-DD}/{task_id}.csv   ← 清洗数据
├── archive/{platform}/{YYYY-MM}/                    ← 月度归档
├── INDEX.md                                         ← 数据资产目录
└── warehouse.db                                     ← SQLite数据库
```

task_id命名：`{数据类型}-{类目简称}-{时间戳}`
示例：`search-rank-fishing-20260227-143000`
