#!/bin/bash
# ARC Team — 武器库一键安装脚本
# 运行: bash arc-team/scripts/install-arsenal.sh [--all|--reverser|--phantom|--striker|--mimic|--hunter|--shield|--shared]
# 默认: --all

set -uo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[ARC]${NC} $1"; }
warn() { echo -e "${YELLOW}[ARC]${NC} $1"; }
err() { echo -e "${RED}[ARC]${NC} $1"; }

ROLE="${1:---all}"
ARC_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$ARC_DIR/.venv"

# ============================================================
# Python venv (uv优先)
# ============================================================
setup_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        log "创建Python虚拟环境: $VENV_DIR"
        if command -v uv &>/dev/null; then
            uv venv "$VENV_DIR"
        else
            python3 -m venv "$VENV_DIR"
        fi
    fi
    source "$VENV_DIR/bin/activate"
    log "Python venv已激活: $(which python3)"
}

pip_install() {
    if command -v uv &>/dev/null; then
        uv pip install "$@"
    else
        pip3 install "$@"
    fi
}

# ============================================================
# 共享基础武器
# ============================================================
install_shared() {
    log "=== 安装共享基础武器 ==="
    pip_install requests beautifulsoup4 scrapy lxml numpy scipy pandas || true
    brew install jq yq 2>/dev/null || true
    log "✅ 共享基础武器安装完成"
}

# ============================================================
# REVERSER — 逆向工程师
# ============================================================
install_reverser() {
    log "=== 安装 REVERSER 武器 ==="

    # Frida动态Hook框架
    pip_install frida-tools frida || warn "⚠️ Frida安装失败（可能需要匹配设备架构）"

    # 二进制分析
    brew install radare2 2>/dev/null || true
    brew install --cask ghidra 2>/dev/null || true

    # Android逆向
    brew install jadx apktool dex2jar 2>/dev/null || true

    # Frida自动化
    pip_install objection || true

    # 小程序逆向
    npm install -g unveilr 2>/dev/null || true

    # JS AST反混淆
    npm install -g @babel/core @babel/parser @babel/traverse @babel/generator 2>/dev/null || true

    log "✅ REVERSER 武器安装完成"
}

# ============================================================
# PHANTOM — 指纹工程师
# ============================================================
install_phantom() {
    log "=== 安装 PHANTOM 武器 ==="

    # TLS指纹伪造
    brew install curl-impersonate 2>/dev/null || warn "⚠️ curl-impersonate需手动安装: https://github.com/lwthiker/curl-impersonate"

    # 浏览器自动化
    pip_install playwright && python3 -m playwright install chromium || true
    pip_install undetected-chromedriver selenium || true

    # Node浏览器自动化
    npm install -g puppeteer puppeteer-extra puppeteer-extra-plugin-stealth 2>/dev/null || true

    # HTTP客户端
    pip_install "httpx[http2]" aiohttp || true

    # HTTPS代理
    brew install mitmproxy 2>/dev/null || true
    brew install --cask charles 2>/dev/null || true

    # 代理链
    brew install proxychains-ng 2>/dev/null || true

    # TLS Go库
    go install github.com/bogdanfinn/tls-client@latest 2>/dev/null || true

    log "✅ PHANTOM 武器安装完成"
}

# ============================================================
# STRIKER — 协议攻击工程师
# ============================================================
install_striker() {
    log "=== 安装 STRIKER 武器 ==="

    # ProjectDiscovery全家桶
    go install github.com/projectdiscovery/httpx/cmd/httpx@latest 2>/dev/null || true
    go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest 2>/dev/null || true
    go install github.com/ffuf/ffuf/v2@latest 2>/dev/null || true
    go install github.com/projectdiscovery/katana/cmd/katana@latest 2>/dev/null || true

    # 协议工具
    brew install grpcurl protobuf websocat wrk vegeta xh 2>/dev/null || true

    # Protobuf Go支持
    go install google.golang.org/protobuf/cmd/protoc-gen-go@latest 2>/dev/null || true

    log "✅ STRIKER 武器安装完成"
}

# ============================================================
# MIMIC — 风控逃逸工程师
# ============================================================
install_mimic() {
    log "=== 安装 MIMIC 武器 ==="

    # CV/ML框架
    pip_install torch torchvision --index-url https://download.pytorch.org/whl/cpu || warn "⚠️ PyTorch安装失败"
    pip_install opencv-python-headless || true
    pip_install onnxruntime || true
    pip_install ultralytics || true

    # 验证码识别
    pip_install ddddocr || true
    brew install tesseract 2>/dev/null || true
    pip_install pytesseract Pillow || true

    # 移动设备控制
    npm install -g appium 2>/dev/null || true
    brew install scrcpy android-platform-tools 2>/dev/null || true

    log "✅ MIMIC 武器安装完成"
}

# ============================================================
# HUNTER — 漏洞猎人
# ============================================================
install_hunter() {
    log "=== 安装 HUNTER 武器 ==="

    # 扫描工具
    brew install nmap sqlmap nikto 2>/dev/null || true
    brew install --cask burp-suite 2>/dev/null || warn "⚠️ Burp Suite需手动下载"

    # 目录/端点爆破
    brew install feroxbuster gobuster 2>/dev/null || true
    go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest 2>/dev/null || true
    go install github.com/hahwul/dalfox/v2@latest 2>/dev/null || true

    # API测试
    brew install httpie 2>/dev/null || true
    pip_install PyJWT 2>/dev/null || true

    log "✅ HUNTER 武器安装完成"
}

# ============================================================
# SHIELD — 防御分析师
# ============================================================
install_shield() {
    log "=== 安装 SHIELD 武器 ==="

    # 流量分析
    brew install wireshark 2>/dev/null || true

    # TLS/SSL审计
    brew install testssl sslscan 2>/dev/null || true

    # WAF/技术栈识别
    pip_install wafw00f || true
    brew install whatweb 2>/dev/null || true
    npm install -g wappalyzer 2>/dev/null || true

    # Web扫描
    brew install nikto 2>/dev/null || true

    # 互联网搜索
    pip_install shodan || true

    log "✅ SHIELD 武器安装完成"
}

# ============================================================
# 主入口
# ============================================================
main() {
    log "🐊 ARC Team 武器库安装 — 角色: $ROLE"
    log "环境: macOS $(sw_vers -productVersion) | Python $(python3 --version | awk '{print $2}') | Go $(go version | awk '{print $3}') | Node $(node --version)"
    echo ""

    setup_venv

    case "$ROLE" in
        --all)
            install_shared
            install_reverser
            install_phantom
            install_striker
            install_mimic
            install_hunter
            install_shield
            ;;
        --shared)    install_shared ;;
        --reverser)  install_shared && install_reverser ;;
        --phantom)   install_shared && install_phantom ;;
        --striker)   install_shared && install_striker ;;
        --mimic)     install_shared && install_mimic ;;
        --hunter)    install_shared && install_hunter ;;
        --shield)    install_shared && install_shield ;;
        *)
            err "未知角色: $ROLE"
            echo "用法: $0 [--all|--reverser|--phantom|--striker|--mimic|--hunter|--shield|--shared]"
            exit 1
            ;;
    esac

    echo ""
    log "🎯 安装完成。运行 'bash arc-team/scripts/verify-arsenal.sh' 验证武器状态"
    log "⚠️ Python工具需在venv中使用: source $VENV_DIR/bin/activate"
}

main
