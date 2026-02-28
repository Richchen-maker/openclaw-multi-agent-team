# ARC Team — 武器库清单

> 最后验证: 2026-02-27 (初始化，待安装)
> 安装脚本: `scripts/install-arsenal.sh`

---

## 按角色分配的武器矩阵

### REVERSER — 逆向工程师

| 武器 | 用途 | 安装方式 | 权限级别 |
|------|------|---------|---------|
| **Frida** | 动态Hook框架，内存注入/拦截/修改运行时行为 | `pip install frida-tools frida` | 🔴 MAX |
| **radare2 (r2)** | 二进制分析/反汇编/调试，支持ARM/x86/MIPS | `brew install radare2` | 🔴 MAX |
| **Ghidra (headless)** | NSA级逆向工程套件，反编译/CFG分析 | `brew install --cask ghidra` | 🔴 MAX |
| **jadx** | Android APK/DEX反编译为Java源码 | `brew install jadx` | 🟡 HIGH |
| **apktool** | APK解包/重打包/smali编辑 | `brew install apktool` | 🟡 HIGH |
| **objection** | Frida上层自动化，快速bypass SSL pinning/root检测 | `pip install objection` | 🔴 MAX |
| **dex2jar** | DEX→JAR转换，配合JD-GUI分析 | `brew install dex2jar` | 🟡 HIGH |
| **jtool2** | macOS/iOS Mach-O二进制分析 | 手动下载 | 🟡 HIGH |
| **wxappUnpacker** | 微信小程序反编译(.wxapkg解包) | `npm install -g wxappUnpacker` 或 clone | 🟡 HIGH |
| **unveilr** | 微信小程序逆向(更现代的替代方案) | `npm install -g unveilr` | 🟡 HIGH |
| **AST Explorer** | JS AST反混淆工具链 | `npm install -g @babel/core @babel/parser @babel/traverse @babel/generator` | 🟡 HIGH |

### PHANTOM — 指纹工程师

| 武器 | 用途 | 安装方式 | 权限级别 |
|------|------|---------|---------|
| **curl-impersonate** | 伪造TLS指纹的curl（模拟Chrome/Firefox/Safari JA3） | `brew install curl-impersonate` | 🔴 MAX |
| **Playwright** | 浏览器自动化，支持CDP定制/指纹修改 | `pip install playwright && playwright install` | 🔴 MAX |
| **puppeteer-extra-stealth** | Puppeteer反检测插件集 | `npm install puppeteer puppeteer-extra puppeteer-extra-plugin-stealth` | 🔴 MAX |
| **undetected-chromedriver** | 过Cloudflare/Akamai的Selenium驱动 | `pip install undetected-chromedriver` | 🔴 MAX |
| **tls-client (Go)** | Go语言TLS指纹伪造库，支持JA3/JA4/HTTP2指纹 | `go install github.com/bogdanfinn/tls-client@latest` | 🔴 MAX |
| **ja3transport** | Go的JA3指纹伪造transport | `go get github.com/CUCyber/ja3transport` | 🟡 HIGH |
| **mitmproxy** | HTTPS中间人代理，流量拦截/修改/重放 | `brew install mitmproxy` | 🔴 MAX |
| **Charles Proxy** | GUI级HTTPS调试代理 | `brew install --cask charles` | 🟡 HIGH |
| **proxychains-ng** | 命令行代理链，多层代理跳转 | `brew install proxychains-ng` | 🟡 HIGH |
| **httpx (Python)** | 异步HTTP客户端，支持HTTP/2/自定义TLS | `pip install httpx[http2]` | 🟡 HIGH |
| **aiohttp** | 异步HTTP框架，高并发采集 | `pip install aiohttp` | 🟡 HIGH |
| **FingerprintJS** | 浏览器指纹生成/检测库（用于研究） | `npm install @fingerprintjs/fingerprintjs` | 🟢 MED |

### STRIKER — 协议攻击工程师

| 武器 | 用途 | 安装方式 | 权限级别 |
|------|------|---------|---------|
| **httpx (Go)** | 超快HTTP探测/批量请求/并发测试 | `go install github.com/projectdiscovery/httpx/cmd/httpx@latest` | 🔴 MAX |
| **nuclei** | 基于模板的漏洞扫描/协议测试 | `go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest` | 🔴 MAX |
| **ffuf** | 高速Web Fuzzer，API端点/参数爆破 | `go install github.com/ffuf/ffuf/v2@latest` | 🔴 MAX |
| **grpcurl** | gRPC协议调试，服务反射/请求构造 | `brew install grpcurl` | 🟡 HIGH |
| **h2c (HTTP/2)** | HTTP/2明文调试工具 | `go install github.com/fstab/h2c@latest` | 🟡 HIGH |
| **vegeta** | HTTP负载测试/并发压测 | `brew install vegeta` | 🔴 MAX |
| **wrk** | HTTP基准压测工具 | `brew install wrk` | 🟡 HIGH |
| **Protobuf** | Protocol Buffers编解码 | `brew install protobuf` | 🟡 HIGH |
| **protoc-gen-go** | Protobuf Go代码生成（逆向gRPC用） | `go install google.golang.org/protobuf/cmd/protoc-gen-go@latest` | 🟡 HIGH |
| **websocat** | WebSocket CLI客户端/调试 | `brew install websocat` | 🟡 HIGH |
| **xh** | 现代httpie替代，快速HTTP请求构造 | `brew install xh` | 🟢 MED |

### MIMIC — 风控逃逸工程师

| 武器 | 用途 | 安装方式 | 权限级别 |
|------|------|---------|---------|
| **PyTorch** | 验证码破解模型训练/推理 | `pip install torch torchvision` | 🔴 MAX |
| **OpenCV** | 计算机视觉，图像处理/验证码预处理 | `pip install opencv-python-headless` | 🔴 MAX |
| **ONNX Runtime** | 模型推理加速（毫秒级验证码识别） | `pip install onnxruntime` | 🔴 MAX |
| **ultralytics (YOLOv8)** | 目标检测，点选验证码元素识别 | `pip install ultralytics` | 🔴 MAX |
| **ddddocr** | 通用验证码识别（滑块/点选/OCR开箱即用）[已修复1.6.0 bug] | `pip install ddddocr` + `patch-ddddocr.sh` | 🔴 MAX |
| **captcha-recognizer** | ONNX深度学习滑块缺口检测（精度最高） | `pip install captcha-recognizer` | 🔴 MAX |
| **CapSolver SDK** | 云端API兜底(reCAPTCHA/hCaptcha/Geetest/CF) | `pip install capsolver` | 🔴 MAX |
| **captcha_solver.py** | 多引擎统一调度（5层降级，7引擎融合） | 自研，arc-team/tools/ | 🔴 MAX |
| **Tesseract** | OCR引擎，文字验证码识别 | `brew install tesseract` | 🟡 HIGH |
| **Pillow** | 图像处理基础库 | `pip install Pillow` | 🟢 MED |
| **numpy/scipy** | 轨迹生成的数学运算（贝塞尔曲线/噪声注入） | `pip install numpy scipy` | 🟢 MED |
| **Appium** | 移动设备自动化框架（群控基座） | `npm install -g appium` | 🔴 MAX |
| **scrcpy** | Android屏幕镜像/控制（低延迟群控） | `brew install scrcpy` | 🟡 HIGH |
| **Android Platform Tools** | ADB/fastboot/设备批控 | `brew install android-platform-tools` | 🟡 HIGH |

### HUNTER — 漏洞猎人

| 武器 | 用途 | 安装方式 | 权限级别 |
|------|------|---------|---------|
| **nuclei** | (共享STRIKER) 漏洞扫描 | 同上 | 🔴 MAX |
| **sqlmap** | SQL注入自动化检测/利用 | `brew install sqlmap` | 🔴 MAX |
| **Burp Suite CE** | Web安全测试代理（社区版） | `brew install --cask burp-suite` | 🔴 MAX |
| **nmap** | 网络扫描/端口枚举/服务识别 | `brew install nmap` | 🔴 MAX |
| **feroxbuster** | 高速目录/API端点暴力枚举 | `brew install feroxbuster` | 🟡 HIGH |
| **gobuster** | 目录/DNS/vhost爆破 | `brew install gobuster` | 🟡 HIGH |
| **subfinder** | 子域名发现 | `go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest` | 🟡 HIGH |
| **katana** | 深度网页爬取/JS解析/API发现 | `go install github.com/projectdiscovery/katana/cmd/katana@latest` | 🟡 HIGH |
| **dalfox** | XSS扫描（参数分析+payload生成） | `go install github.com/hahwul/dalfox/v2@latest` | 🟡 HIGH |
| **jwt-tool** | JWT令牌分析/伪造/攻击 | `pip install jwt-tool` | 🟡 HIGH |
| **Postman/httpie** | API手动测试 | `brew install httpie` | 🟢 MED |

### SHIELD — 防御分析师

| 武器 | 用途 | 安装方式 | 权限级别 |
|------|------|---------|---------|
| **Wireshark (tshark)** | 网络流量深度分析/协议解码 | `brew install wireshark` | 🔴 MAX |
| **nmap** | (共享HUNTER) 防御面扫描 | 同上 | 🔴 MAX |
| **testssl.sh** | TLS/SSL配置安全审计 | `brew install testssl` | 🟡 HIGH |
| **wafw00f** | WAF指纹识别（Akamai/CF/自研） | `pip install wafw00f` | 🟡 HIGH |
| **whatweb** | Web技术栈指纹识别 | `brew install whatweb` | 🟡 HIGH |
| **wappalyzer** | 网站技术栈深度识别 | `npm install -g wappalyzer` | 🟡 HIGH |
| **nikto** | Web服务器安全扫描 | `brew install nikto` | 🟡 HIGH |
| **ssl-scan** | SSL/TLS加密套件分析 | `brew install sslscan` | 🟡 HIGH |
| **shodan CLI** | 互联网设备搜索（暴露面发现） | `pip install shodan` | 🔴 MAX |

---

## 全角色共享武器

| 武器 | 用途 | 安装方式 |
|------|------|---------|
| **web_search** | Brave搜索（公开情报） | OpenClaw内置 |
| **web_fetch** | 网页内容抓取 | OpenClaw内置 |
| **exec** | Shell命令执行 | OpenClaw内置 |
| **read/write** | 文件读写 | OpenClaw内置 |
| **Python 3.14** | 脚本/数据处理/工具开发 | 已安装 |
| **Node.js** | JS逆向/工具链 | 已安装 |
| **Go 1.26** | 高性能工具编译 | 已安装 |
| **jq** | JSON处理 | `brew install jq` |
| **yq** | YAML处理 | `brew install yq` |
| **requests** | Python HTTP基础库 | `pip install requests` |
| **BeautifulSoup4** | HTML解析 | `pip install beautifulsoup4` |
| **Scrapy** | 分布式爬虫框架 | `pip install scrapy` |

---

## 权限级别说明

| 级别 | 含义 | 使用规则 |
|------|------|---------|
| 🔴 MAX | 最高权限，可执行实际攻防操作 | COMMANDER授权后使用 |
| 🟡 HIGH | 高权限，信息收集/分析类 | 角色自主决定 |
| 🟢 MED | 中权限，辅助工具 | 自由使用 |
