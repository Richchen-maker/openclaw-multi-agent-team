# 🔧 Installation Guide — From Zero to Running

This guide gets you from a **fresh machine** to running multi-agent teams. Follow the sections for the teams you want to deploy.

---

## Table of Contents

- [Base Requirements (ALL teams)](#base-requirements-all-teams)
- [E-commerce Team](#-e-commerce-team)
- [Data Collection Team](#-data-collection-team)
- [ARC Team (Anti-Risk Control)](#️-arc-team-anti-risk-control)
- [Verify Installation](#-verify-installation)

---

## Base Requirements (ALL teams)

Every team needs OpenClaw + an LLM API key + web search.

### 1. System Dependencies

```bash
# macOS (Homebrew)
brew install node git jq yq

# Linux (Ubuntu/Debian) — Node.js v22+
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs git jq
sudo snap install yq

# Windows → use WSL2: wsl --install, then follow Linux steps
```

> ⚠️ **Node.js v22.12+ is required.** Check with `node -v`.

### 2. OpenClaw

```bash
npm install -g openclaw
openclaw setup          # interactive wizard — sets up LLM key + workspace
openclaw gateway start  # starts the daemon
```

### 3. LLM API Key

You need **one** of these:

| Provider | Get Key | Recommended Model |
|----------|---------|-------------------|
| **Anthropic** (recommended) | [console.anthropic.com](https://console.anthropic.com/) | Claude Sonnet 4 |
| OpenAI | [platform.openai.com](https://platform.openai.com/) | GPT-4o |
| Google | [aistudio.google.com](https://aistudio.google.com/) | Gemini 2.5 Pro |

### 4. Web Search API

Agents need web search to function. Without this, research agents return empty results.

```bash
# Brave Search (required) — 2,000 queries/month free
# Get key at: https://brave.com/search/api/
openclaw config set braveApiKey YOUR_BRAVE_KEY
```

### 5. Messaging Channel (optional but recommended)

Connect Telegram/Discord/Slack so you can dispatch teams from your phone:

```bash
# Telegram example — see OpenClaw docs for Discord/Slack
# 1. Create bot via @BotFather → get bot token
# 2. Add to openclaw.json:
#    channels.telegram.botToken = "YOUR_TOKEN"
#    channels.telegram.dmPolicy = "allowlist"
#    channels.telegram.allowFrom = ["YOUR_CHAT_ID"]
```

### 6. Deploy Teams to Workspace

```bash
git clone https://github.com/Richchen-maker/openclaw-multi-agent-team.git
cd openclaw-multi-agent-team

# Copy the teams you want:
cp -r examples/ecommerce-team ~/.openclaw/workspace/
cp -r examples/data-collection-team ~/.openclaw/workspace/
cp -r examples/arc-team ~/.openclaw/workspace/
cp -r examples/content-team ~/.openclaw/workspace/

# Copy framework docs (needed for multi-team routing):
cp -r framework ~/.openclaw/workspace/
```

---

## 🛒 E-commerce Team

**Zero extra dependencies.** This team uses only OpenClaw built-in tools (web_search, web_fetch, exec) and optional ClawHub skills.

### Optional Enhancements

```bash
# ClawHub skills for deeper research
npm install -g clawhub
clawhub install cn-ecommerce-search    # Search Taobao/JD/1688/PDD
clawhub install tavily-search          # AI-powered deep research
clawhub install summarize              # Summarize URLs/PDFs
```

### Test

```
Tell OpenClaw: "启动电商团队，评估品类：蓝牙耳机"
```

---

## 📡 Data Collection Team

### Python Environment

```bash
# Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create venv in team directory
cd ~/.openclaw/workspace/data-collection-team
uv venv .venv --python 3.12   # 3.11+ works
source .venv/bin/activate

# Install Python dependencies
uv pip install \
  requests \
  beautifulsoup4 \
  scrapy \
  httpx[http2] \
  aiohttp \
  lxml
```

### Optional: Database Tools

The team uses SQLite by default (zero-config). For the warehouse scripts:

```bash
# Already included in Python stdlib — no install needed
python -c "import sqlite3; print('SQLite OK')"
```

### Test

```
Tell OpenClaw: "启动数据采集团队，采集目标：竞品分析 蓝牙耳机 淘宝前20"
```

---

## 🛡️ ARC Team (Anti-Risk Control)

> ⚠️ This team has the most dependencies. Install in stages — start with Core, add roles as needed.

### Stage 1: Core (required)

```bash
# Python venv
cd ~/.openclaw/workspace/arc-team
uv venv .venv --python 3.12
source .venv/bin/activate

# Core Python packages
uv pip install \
  requests \
  httpx[http2] \
  aiohttp \
  beautifulsoup4 \
  numpy \
  Pillow

# Go (needed for several tools)
# macOS:
brew install go
# Linux:
# Download from https://go.dev/dl/
```

### Stage 2: REVERSER — Reverse Engineering

```bash
# Binary analysis
brew install radare2 jadx apktool

# Ghidra (NSA reverse engineering suite)
brew install --cask ghidra
# Or download from https://ghidra-sre.org/

# Frida (dynamic instrumentation)
uv pip install frida-tools frida

# objection (Frida automation)
uv pip install objection

# JS deobfuscation
npm install -g @babel/core @babel/parser @babel/traverse @babel/generator

# WeChat mini-program reverse
npm install -g unveilr
```

### Stage 3: PHANTOM — Fingerprint Engineering

```bash
# Browser automation
uv pip install playwright undetected-chromedriver
playwright install chromium

# TLS fingerprint spoofing — Option A: build from source (recommended for Apple Silicon)
cd ~/.openclaw/workspace/arc-team/tools
go build -o /usr/local/bin/curl-impersonate curl-impersonate.go

# TLS fingerprint spoofing — Option B: pre-built (x86_64 Linux/macOS only)
# brew install curl-impersonate

# HTTPS proxy
brew install mitmproxy proxychains-ng

# Puppeteer stealth (Node.js)
npm install puppeteer puppeteer-extra puppeteer-extra-plugin-stealth
```

### Stage 4: STRIKER — Protocol Testing

```bash
# Go tools (install to ~/go/bin/)
go install github.com/projectdiscovery/httpx/cmd/httpx@latest
go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
go install github.com/ffuf/ffuf/v2@latest

# Brew tools
brew install grpcurl vegeta wrk websocat protobuf xh
```

### Stage 5: MIMIC — CAPTCHA & Risk Control

```bash
# CAPTCHA multi-engine system
uv pip install \
  torch torchvision \
  opencv-python-headless \
  onnxruntime \
  ultralytics \
  ddddocr \
  captcha-recognizer \
  capsolver

# Tesseract OCR
brew install tesseract

# Fix ddddocr 1.6.0 upstream bug (required if using ddddocr)
bash ~/.openclaw/workspace/arc-team/scripts/patch-ddddocr.sh

# Mobile device control (optional — for device farm scenarios)
brew install scrcpy android-platform-tools
npm install -g appium
```

### Stage 6: HUNTER — Vulnerability Scanning

```bash
# Network scanning
brew install nmap

# Web vulnerability tools
brew install feroxbuster nikto
uv pip install sqlmap

# Subdomain & crawler
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install github.com/projectdiscovery/katana/cmd/katana@latest

# XSS scanner
go install github.com/hahwul/dalfox/v2@latest

# HTTP client
uv pip install httpie
```

### Stage 7: SHIELD — Defense Analysis

```bash
# Traffic analysis
brew install wireshark   # includes tshark CLI

# TLS/SSL auditing
brew install testssl sslscan

# WAF & tech stack identification
uv pip install wafw00f shodan

# WhatWeb (requires Ruby)
brew install ruby whatweb

# Web server scanning
brew install nikto
```

### One-Shot Install Script

If you want everything at once:

```bash
cd ~/.openclaw/workspace/arc-team
bash scripts/install-arsenal.sh
```

### Verify Arsenal

```bash
bash scripts/verify-arsenal.sh
```

This checks all 54 weapons and reports status.

### Test

```
Tell OpenClaw: "ARC团队，Mode B防御评估，目标：example.com"
```

---

## ✅ Verify Installation

### Quick Health Check

```bash
# Base
node -v                    # v22.12+
openclaw --version         # v0.9+

# Python (if using data-collection or arc team)
python3 --version          # 3.11+

# Go (if using arc team)
go version                 # 1.21+

# Teams are in workspace
ls ~/.openclaw/workspace/*-team/
```

### Per-Team Verification

```bash
# E-commerce — just needs OpenClaw
openclaw gateway status

# Data Collection — needs Python
source ~/.openclaw/workspace/data-collection-team/.venv/bin/activate
python3 -c "import requests, bs4, scrapy; print('✅ Data Collection deps OK')"

# ARC — full arsenal check
source ~/.openclaw/workspace/arc-team/.venv/bin/activate
python3 ~/.openclaw/workspace/arc-team/tools/captcha_solver.py status
bash ~/.openclaw/workspace/arc-team/scripts/verify-arsenal.sh
```

---

## Dependency Summary

| Team | Python | Go | Brew | npm | Total Packages |
|------|--------|----|------|-----|---------------|
| E-commerce | 0 | 0 | 0 | 0 (optional ClawHub skills) | ~0 |
| Data Collection | ~6 | 0 | 0 | 0 | ~6 |
| ARC (full) | ~25 | ~8 | ~18 | ~5 | ~56 |
| **ARC (core only)** | **~8** | **0** | **0** | **0** | **~8** |

> 💡 **Start small.** Deploy e-commerce team first (zero deps). Add data-collection when you need scraping. Add ARC roles one stage at a time — you don't need all 54 weapons on day one.

---

## Platform Notes

### macOS (Apple Silicon / M1-M4)

- All tools tested on arm64. No Rosetta needed.
- `curl-impersonate`: official binary is x86_64-only. Use the Go wrapper in `arc-team/tools/curl-impersonate.go` instead.
- PyTorch supports MPS (Apple GPU) acceleration: `torch.backends.mps.is_available() == True`

### macOS (Intel)

- All tools work natively. `curl-impersonate` official binary also works: `brew install curl-impersonate`

### Linux (x86_64)

- All tools work. Use `apt`/`dnf` instead of `brew` where applicable.
- `curl-impersonate` official binary available: https://github.com/lwthiker/curl-impersonate/releases

### Linux (arm64 / Raspberry Pi)

- Most tools work. Some Go tools may need source compilation.
- PyTorch: use CPU-only build (`pip install torch --index-url https://download.pytorch.org/whl/cpu`)

### Windows

- **Use WSL2.** Native Windows is not tested and will likely have path/permission issues.
- Inside WSL2, follow Linux instructions.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `pip install ddddocr` fails on Python 3.13+ | Use Python 3.12 venv, or run `patch-ddddocr.sh` after install |
| Go tools fail with "module requires Go 1.XX" | Update Go: `brew upgrade go` |
| `ghidra_headless: command not found` | Symlink: `ln -s /path/to/ghidra/support/analyzeHeadless /usr/local/bin/ghidra_headless` |
| `whatweb` errors about Ruby | Install brew Ruby: `brew install ruby`, then `export PATH="/opt/homebrew/opt/ruby/bin:$PATH"` |
| `nuclei` fails to install via `go install` | Use `brew install nuclei` instead |
| CAPTCHA solver shows engine "false" | Install the missing package for that engine (see Stage 5) |
| Apple Silicon: `curl-impersonate` binary fails | Use the Go wrapper: `cd arc-team/tools && go build -o /usr/local/bin/curl-impersonate curl-impersonate.go` |

---

---

## Stage 8: Cross-Team Event Bus (Optional)

Cross-team auto-collaboration engine. Teams trigger each other automatically through file-based events.

### Install

```bash
pip install pyyaml
mkdir -p events/{pending,processing,resolved,failed}
```

### Verify

```bash
python -m eventbus status
```

Expected output:
```
Event Bus Status
────────────────
  pending:    0
  processing: 0
  resolved:   0
  failed:     0
```

### Start

```bash
python -m eventbus run
```

For details: [Cross-Team Guide](docs/CROSS-TEAM-GUIDE.md) | [Event Bus README](framework/eventbus/README.md)

---

## Event Bus Configuration

跨团队自动协作引擎配置。

### 1. 创建配置文件

```bash
cd ~/.openclaw/workspace
cat > eventbus.yaml << 'EOF'
workspace_dir: "."
poll_interval: 60              # 轮询间隔（秒）
max_chain_depth: 5             # 事件链最大深度（防无限递归）
dedup_window: 3600             # 去重窗口（秒）
processing_timeout: 1800       # processing超时标记failed
resolved_retention: 7          # resolved保留天数
dispatch_mode: "cron"          # cron=Watchdog消费 | live=直接spawn | default=dry-run
dispatch_timeout: 300          # sub-agent超时
bus_mode: "cron"               # cron | daemon
EOF
```

### 2. 初始化事件目录

```bash
mkdir -p events/{pending,processing,resolved,failed}
```

### 3. 验证

```bash
PYTHONPATH=framework python3 -m eventbus status
```

预期输出：
```
Event Bus Status
────────────────
  pending:    0
  processing: 0
  resolved:   0
  failed:     0
```

### 4. 可选：团队能力扫描

```bash
PYTHONPATH=framework python3 -m eventbus registry --scan
```

### 5. 默认配置项说明

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `poll_interval` | 60 | EventBus轮询间隔（秒） |
| `max_chain_depth` | 5 | 事件链最大递归深度 |
| `dedup_window` | 3600 | 去重窗口（秒） |
| `processing_timeout` | 1800 | processing超时（秒） |
| `dispatch_mode` | cron | cron/live/default |
| `bus_mode` | cron | cron跳过BUS_DOWN检查 |

详见 [Event Bus详解](framework/EVENT-BUS.md) | [跨团队协作指南](docs/CROSS-TEAM-GUIDE.md)

---

## License

MIT — use it however you want.
