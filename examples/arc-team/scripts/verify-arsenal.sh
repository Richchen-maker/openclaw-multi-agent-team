#!/bin/bash
# ARC Team — 武器库状态验证
set -uo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

ok() { echo -e "  ${GREEN}✅${NC} $1"; }
fail() { echo -e "  ${RED}❌${NC} $1"; }

check_cmd() {
    if command -v "$1" &>/dev/null; then ok "$1 — $2"; return 0
    else fail "$1 — $2 (未安装)"; return 1; fi
}

check_py() {
    if python3 -c "import $1" 2>/dev/null; then ok "py:$1 — $2"; return 0
    else fail "py:$1 — $2 (未安装)"; return 1; fi
}

TOTAL=0; PASS=0

t() { TOTAL=$((TOTAL+1)); }
p() { PASS=$((PASS+1)); }

echo "=== REVERSER 逆向工程师 ==="
t; check_cmd frida "动态Hook" && p
t; check_cmd r2 "二进制分析(radare2)" && p
t; (check_cmd ghidraRun "反编译套件" || check_cmd ghidra "反编译套件") && p
t; check_cmd jadx "APK反编译" && p
t; check_cmd apktool "APK解包" && p
t; check_cmd objection "Frida自动化" && p
t; check_py frida "Frida Python绑定" && p

echo ""
echo "=== PHANTOM 指纹工程师 ==="
t; (check_cmd curl-impersonate "TLS指纹伪造(Go)" || check_cmd curl-impersonate-chrome "TLS指纹伪造" || check_cmd curl_chrome116 "TLS指纹伪造") && p
t; check_py playwright "Playwright浏览器" && p
t; check_py undetected_chromedriver "反检测Chrome" && p
t; check_cmd mitmproxy "HTTPS代理" && p
t; check_cmd mitmdump "HTTPS代理CLI" && p
t; check_py httpx "异步HTTP/2客户端" && p
t; check_py aiohttp "异步HTTP框架" && p
t; check_cmd proxychains4 "代理链" && p

echo ""
echo "=== STRIKER 协议攻击工程师 ==="
t; check_cmd httpx "HTTP探测(Go)" && p
t; check_cmd nuclei "漏洞扫描" && p
t; check_cmd ffuf "Web Fuzzer" && p
t; check_cmd grpcurl "gRPC调试" && p
t; check_cmd vegeta "HTTP压测" && p
t; check_cmd wrk "HTTP基准测试" && p
t; check_cmd protoc "Protobuf编译器" && p
t; check_cmd websocat "WebSocket CLI" && p

echo ""
echo "=== MIMIC 风控逃逸工程师 ==="
t; check_py torch "PyTorch" && p
t; check_py cv2 "OpenCV" && p
t; check_py onnxruntime "ONNX推理" && p
t; check_py ultralytics "YOLOv8" && p
t; check_py ddddocr "通用验证码识别" && p
t; check_cmd tesseract "OCR引擎" && p
t; check_cmd adb "Android调试桥" && p
t; check_cmd scrcpy "Android屏幕控制" && p

echo ""
echo "=== HUNTER 漏洞猎人 ==="
t; check_cmd nmap "网络扫描" && p
t; check_cmd sqlmap "SQL注入" && p
t; check_cmd feroxbuster "目录爆破" && p
t; check_cmd gobuster "目录/DNS爆破" && p
t; check_cmd subfinder "子域名发现" && p
t; check_cmd katana "深度爬取" && p
t; check_cmd dalfox "XSS扫描" && p
t; check_cmd http "httpie" && p

echo ""
echo "=== SHIELD 防御分析师 ==="
t; check_cmd tshark "流量分析(Wireshark CLI)" && p
t; check_cmd testssl.sh "TLS审计" || check_cmd testssl.sh "TLS审计" && p
t; check_py wafw00f "WAF识别" && p
t; check_cmd whatweb "技术栈识别" && p
t; check_cmd nikto "Web扫描" && p
t; check_cmd sslscan "SSL扫描" && p
t; check_py shodan "Shodan搜索" && p

echo ""
echo "=== 共享基础 ==="
t; check_py requests "HTTP基础库" && p
t; check_py bs4 "HTML解析" && p
t; check_py scrapy "爬虫框架" && p
t; check_py numpy "数值计算" && p
t; check_cmd jq "JSON处理" && p
t; check_cmd python3 "Python" && p
t; check_cmd node "Node.js" && p
t; check_cmd go "Go" && p

echo ""
echo "========================================="
echo -e "  武器就绪: ${GREEN}${PASS}${NC} / ${TOTAL}"
echo "========================================="
