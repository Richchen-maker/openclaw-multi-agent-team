# 工具引导协议 v3 — 电商团队 Sub-agent 标准工具能力包

> 本文件是每个 sub-agent 的工具能力基座。Lead 在 spawn 时将本内容注入 task prompt。
> 最后更新: 2026-02-26 v3

## ⚠️ 全局输出铁律（v3）

### 铁律1: 零废话
- **禁止**：过渡句（"让我们来看看"/"值得注意的是"/"总的来说"）、感叹号煽情、重复总结
- **每段必须有数据锚点**：没有数字/来源/表格支撑的段落→删掉
- **能用表格说清的禁止用文字**：成本、价格、竞品对比、广告数据→全部表格化
- **字数红线**：每个Section最多300字（表格不计），超出→砍掉废话而非砍掉数据

### 铁律2: 数据必须可验证
- 每条数据标注：**来源URL/工具 + 查询日期 + 原始query**
- **竞品数据必须标注获取方式**：web_search片段 / web_fetch实际listing / 万邦API实时拉取 / 手动推算
- 未标注来源→自动 LOW 置信度。ORACLE会审计
- **禁止**：引用数据不标来源、混淆展示价和成交价、用>12个月数据不标时效警告

### 铁律3: 数字用表格，不用文字
❌ 错误示范：`采购成本约$6，加上FBA配送费$4，Amazon佣金15%即$4.95，广告费按ACoS 25%计算约$8.25...`
✅ 正确示范：
| 成本项 | 金额 | 占比 | 来源 |
|--------|------|------|------|
| 采购 | $6.00 | 18.2% | 1688展示价 |
| FBA配送 | $4.00 | 12.1% | Amazon FBA计算器 |

### 铁律4: 竞品必须带图
- SCOUT输出的Top 10竞品，每个**必须附主图URL**
- 用 `web_fetch` 抓取Amazon/淘宝listing → 提取主图链接
- 如无法获取图片→标注 `[图片未获取]` + 文字描述外观
- 图片格式：`![竞品名](URL)` 或 `主图: URL`

---

## Step 0: 工具自检（15秒内完成）

开始正式工作前，执行以下命令验证工具可用性：

```bash
# MCP翻译（中英电商术语翻译）
mcporter call translate.translate_text text="跨境电商" target="en" source="zh" --timeout 15000
```

- 返回有效JSON → ✅ 可用
- 超时/报错 → ❌ 不可用，退回到纯 web_search + web_fetch
- 将自检结果写在输出报告开头

---

## 可用工具（已验证）

### A. 市场/竞品数据采集

| 工具 | 调用方式 | 说明 |
|------|---------|------|
| **web_search**（主力） | `web_search query="关键词" count=10` | 通用搜索，支持中英文，最稳定 |
| **web_search 定向** | `web_search query="关键词 site:amazon.com" count=10` | 定向平台搜索 |
| **web_fetch** | `web_fetch url="URL"` | 抓取商品页面/评论页/行业报告 |

**电商数据采集标准流程（每个品类/产品）：**
```
Round 1: web_search query="品类名 市场规模 增长率 2025 2026" count=10
Round 2: web_search query="品类名 竞品分析 头部品牌" count=10
Round 3: web_search query="category name market size growth site:statista.com OR site:grandviewresearch.com" count=10
Round 4: web_search query="品类名 消费者痛点 差评 site:zhihu.com OR site:xiaohongshu.com" count=10
Round 5: 对关键结果用 web_fetch 读取详情
```

**电商平台Listing分析流程：**
```
Round 1: web_search query="品类名 best seller site:amazon.com" count=10
Round 2: web_fetch 抓取Top 5竞品listing页面
Round 3: 提取: 标题结构、卖点、价格、评分、评论数、Q&A高频问题
Round 4: web_search query="品类名 淘宝天猫 销量排行" count=10（国内平台对标）
```

### B. Tavily AI搜索（深度研究）

| 工具 | 调用方式 | 说明 |
|------|---------|------|
| **Tavily 普通搜索** | `exec: TAVILY_API_KEY="YOUR_TAVILY_API_KEY" node /path/to/tavily-search/scripts/search.mjs "query" -n 5` | AI优化搜索 |
| **Tavily 深度搜索** | 同上加 `--deep` | 复杂市场研究 |
| **Tavily 网页提取** | `exec: TAVILY_API_KEY="YOUR_TAVILY_API_KEY" node /path/to/tavily-search/scripts/extract.mjs "URL"` | 提取网页核心内容 |

**Tavily vs web_search 使用场景：**
- **web_search**: 精确关键词、`site:` 定向、快速
- **Tavily 普通**: 模糊查询、趋势概览
- **Tavily --deep**: 品类深度调研、消费者洞察、竞争格局分析

### C. 数据分析

| 工具 | 调用方式 | 说明 |
|------|---------|------|
| **Python3** | `exec: python3 -c "代码"` 或 `exec: python3 脚本路径` | 数据清洗、统计、可视化 |
| **Translate** | `exec: mcporter call translate.translate_text text="文本" target="en" source="zh" --timeout 15000` | 中英互译（listing翻译、关键词翻译） |

### D. 内容辅助

| 工具 | 调用方式 | 说明 |
|------|---------|------|
| **summarize** | `exec: summarize "URL" --model google/gemini-3-flash-preview` | 快速摘要长页面/报告 |
| **read/write** | 直接使用 | 读写本地文件 |

### E. 补充搜索策略

**消费者痛点挖掘：**
```
web_search query="品类名 差评 不满意 退货原因 site:amazon.com" count=10
web_search query="品类名 吐槽 避雷 site:xiaohongshu.com OR site:zhihu.com" count=10
TAVILY --deep "品类名 consumer complaints common issues"
```

**供应链/成本调研：**
```
web_search query="品类名 工厂 批发价 site:1688.com" count=10
web_search query="品类名 OEM ODM supplier alibaba" count=10
web_search query="品类名 原材料成本 生产成本" count=10
```

**趋势预判：**
```
web_search query="品类名 trend 2026 forecast" count=10
TAVILY --deep "品类名 market trend growth drivers barriers 2025 2026"
web_search query="品类名 Google Trends 搜索量" count=10
```

**平台规则/政策：**
```
web_search query="平台名 2026 新规 政策变化 品类限制" count=10
web_search query="amazon policy update 2026 category restrictions" count=10
```

### F. 不可用工具（禁止调用！）

| 工具 | 原因 |
|------|------|
| ❌ cn-ecommerce-search MCP | npm包不存在(404) |
| ❌ Perplexity MCP | 401 Unauthorized |
| ❌ Firecrawl MCP | token过期 |
| ❌ Semantic Scholar MCP | 500 Server Error |

---

## 搜索规则

### 规则1: 多源交叉验证
每个关键数据点（市场规模、价格带、竞品份额等）至少用2个不同来源验证。单一来源不可信。

### 规则2: 不相关时换措辞重试
- 第1次：原始关键词
- 第2次：同义词/英文替换
- 第3次：缩短关键词
- 3次都不相关 → 切换工具

### 规则3: 来源标注
每个关键发现必须标注来源：
```
[来源: web_search, query="xxx", 返回N条, 相关M条]
[来源: web_fetch, url="xxx"]
[来源: tavily, query="xxx", mode=normal/deep]
[来源: 计算推导, 基于数据X和Y]
```

### 规则4: 失败不能静默跳过
失败 → 记录错误 → 切换备选工具 → 在报告中标注

### 规则5: 数据时效性标注
所有市场数据必须标注数据时间。超过12个月的数据标记为 `[⚠️ 数据可能过时]`。

---

## ⛔ 禁止事项
- **禁止调用 sessions_spawn / subagents** — 所有工作你自己完成
- **禁止调用上面❌列表中的工具** — 浪费时间且必定失败
- **禁止编造数据** — 没搜到就说没搜到，标注置信度
- **禁止使用过期数据冒充当前数据** — 必须标注数据时间
