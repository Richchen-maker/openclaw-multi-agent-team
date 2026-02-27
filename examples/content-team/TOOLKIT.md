# 内容创作团队工具可用性报告

> 最后验证: 2026-02-26

## ✅ 可用

| 工具 | 状态 | 说明 |
|------|------|------|
| web_search | ✅ 正常 | Brave Search API，主力搜索（热点/竞品/关键词） |
| web_fetch | ✅ 正常 | 网页抓取，小红书/公众号部分页面有反爬 |
| summarize | ✅ 正常 | URL/文件摘要，适合快速提取竞品内容要点 |
| python3 | ✅ 正常 | 数据分析、关键词统计、排期计算 |
| read/write | ✅ 正常 | 文件读写 |
| xiaohongshu MCP | ✅ 正常 | 小红书内容搜索/分析（13 tools） |

## ⚠️ 受限

| 工具 | 状态 | 说明 |
|------|------|------|
| 抖音热榜 | ⚠️ 间接 | 通过 web_search 抓取第三方热榜聚合站 |
| 公众号内容 | ⚠️ 间接 | 通过 web_search site:mp.weixin.qq.com 或 sogou.com 搜索 |

## ❌ 不可用

| 工具 | 状态 | 原因 |
|------|------|------|
| Perplexity MCP | ❌ 401 | API key 无效 |
| Firecrawl MCP | ❌ 过期 | token 已失效 |

## 📝 替代方案

- 小红书数据：xiaohongshu MCP（主力）+ web_search site:xiaohongshu.com
- 抖音数据：web_search + 第三方热榜聚合站（如 tophub.today）
- 公众号数据：web_search site:mp.weixin.qq.com + sogou微信搜索
- SEO关键词：web_search + web_fetch 分析竞品内容提取高频词
