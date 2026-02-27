# 电商团队工具可用性报告

> 最后验证: 2026-02-25

## ✅ 可用

| 工具 | 状态 | 说明 |
|------|------|------|
| web_search | ✅ 正常 | Brave Search API，主力搜索 |
| web_fetch | ✅ 正常 | 网页抓取，部分站点有反爬 |
| Tavily | ✅ 正常 | AI搜索，普通+深度模式 |
| translate (MCP) | ✅ 正常 | 中英翻译 |
| summarize | ✅ 正常 | URL/文件摘要 |
| python3 | ✅ 正常 | 数据分析、计算 |
| read/write | ✅ 正常 | 文件读写 |

## ❌ 不可用

| 工具 | 状态 | 原因 |
|------|------|------|
| cn-ecommerce-search MCP | ❌ 不存在 | npm包404，clawhub skill包名虚构/已下架 |
| Perplexity MCP | ❌ 401 | API key 无效 |
| Firecrawl MCP | ❌ 过期 | token 已失效 |
| Semantic Scholar MCP | ❌ 500 | 服务端错误 |

## 📝 替代方案

电商数据采集通过 `web_search site:平台域名` + `web_fetch` + 已有xiaohongshu MCP(13 tools) 覆盖。
如需结构化电商API，需接入淘宝开放平台/京东宙斯等（需商家资质）。
