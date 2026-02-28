#!/usr/bin/env python3
"""
ARC Team — 多引擎验证码识别系统

五层引擎架构（按优先级自动降级）:
  L1: ddddocr      — 开箱即用，零训练成本（已修复import bug）
  L2: captcha-recognizer — 深度学习滑块缺口检测（ONNX，精度高）
  L3: OpenCV        — 模板匹配/边缘检测（无ML依赖，鲁棒性强）
  L4: YOLOv8        — 自定义目标检测（点选验证码，需训练）
  L5: CapSolver API — 云端兜底（reCAPTCHA/hCaptcha/Geetest/Cloudflare）

用法:
  # OCR文字验证码
  python3 captcha_solver.py ocr captcha.png

  # 滑块缺口定位（自动选最优引擎）
  python3 captcha_solver.py slide --bg bg.png [--slider slider.png]

  # 点选验证码目标检测
  python3 captcha_solver.py detect captcha.png [--model yolov8n.pt]

  # 生成贝塞尔曲线滑动轨迹
  python3 captcha_solver.py track --start 0 --end 200 [--points 30]

  # 云端API兜底（需CAPSOLVER_API_KEY）
  python3 captcha_solver.py cloud --type recaptchav2 --sitekey XXX --url https://...

  # 列出所有引擎状态
  python3 captcha_solver.py status
"""

import sys
import argparse
import json
import time
import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

import numpy as np

# ============================================================
# 引擎可用性检测
# ============================================================
ENGINES = {}

def _probe_engine(name: str, import_fn):
    try:
        import_fn()
        ENGINES[name] = True
    except Exception:
        ENGINES[name] = False

_probe_engine("ddddocr", lambda: __import__("ddddocr"))
_probe_engine("captcha_recognizer", lambda: __import__("captcha_recognizer"))
_probe_engine("cv2", lambda: __import__("cv2"))
_probe_engine("ultralytics", lambda: __import__("ultralytics"))
_probe_engine("capsolver", lambda: __import__("capsolver"))
_probe_engine("tesseract", lambda: __import__("pytesseract"))
_probe_engine("onnxruntime", lambda: __import__("onnxruntime"))


# ============================================================
# L1: ddddocr 引擎
# ============================================================
class DdddOcrEngine:
    """ddddocr — 通用验证码OCR/检测/滑块"""

    def __init__(self):
        import ddddocr
        self._ocr = ddddocr.DdddOcr(show_ad=False)
        self._det = ddddocr.DdddOcr(det=True, show_ad=False)
        self._slide = ddddocr.DdddOcr(det=False, ocr=False, show_ad=False)

    def ocr(self, image_bytes: bytes) -> str:
        return self._ocr.classification(image_bytes)

    def detect(self, image_bytes: bytes) -> list:
        return self._det.detection(image_bytes)

    def slide_match(self, target_bytes: bytes, bg_bytes: bytes) -> dict:
        result = self._slide.slide_match(target_bytes, bg_bytes, simple_target=True)
        return {"x": result.get("target", [0])[0], "confidence": 0.9, "engine": "ddddocr"}

    def slide_comparison(self, target_bytes: bytes, bg_bytes: bytes) -> dict:
        result = self._slide.slide_comparison(target_bytes, bg_bytes)
        return {"x": result.get("target", [0])[0], "confidence": 0.85, "engine": "ddddocr"}


# ============================================================
# L2: captcha-recognizer 引擎（深度学习ONNX滑块检测）
# ============================================================
class CaptchaRecognizerEngine:
    """captcha-recognizer — ONNX深度学习滑块缺口检测"""

    def __init__(self):
        from captcha_recognizer.slider import Slider
        self._slider = Slider()

    def slide_detect(self, image_path: str) -> dict:
        box, confidence = self._slider.identify(source=image_path, show=False)
        return {
            "box": box,  # [x1, y1, x2, y2]
            "x": box[0] if box else 0,
            "confidence": float(confidence),
            "engine": "captcha_recognizer"
        }

    def slide_offset(self, image_path: str) -> dict:
        offset, confidence = self._slider.identify_offset(source=image_path)
        return {
            "offset": offset,
            "confidence": float(confidence),
            "engine": "captcha_recognizer"
        }


# ============================================================
# L3: OpenCV 引擎（模板匹配 + Canny边缘检测）
# ============================================================
class OpenCVEngine:
    """OpenCV — 模板匹配/边缘检测，无ML依赖"""

    @staticmethod
    def slide_match(bg_path: str, slider_path: str) -> dict:
        import cv2
        bg = cv2.imread(bg_path, 0)
        slider = cv2.imread(slider_path, 0)
        if bg is None or slider is None:
            return {"error": "图片读取失败", "engine": "opencv"}

        # 多方法融合
        methods = [
            ("canny_template", OpenCVEngine._canny_match),
            ("gray_template", OpenCVEngine._gray_match),
            ("laplacian_template", OpenCVEngine._laplacian_match),
        ]
        results = []
        for name, fn in methods:
            try:
                x, conf = fn(bg, slider)
                results.append({"method": name, "x": int(x), "confidence": float(conf)})
            except Exception:
                pass

        if not results:
            return {"error": "所有方法均失败", "engine": "opencv"}

        # 取置信度最高的
        best = max(results, key=lambda r: r["confidence"])
        best["all_methods"] = results
        best["engine"] = "opencv"
        return best

    @staticmethod
    def _canny_match(bg, slider):
        import cv2
        bg_edge = cv2.Canny(bg, 100, 200)
        slider_edge = cv2.Canny(slider, 100, 200)
        result = cv2.matchTemplate(bg_edge, slider_edge, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        return max_loc[0], max_val

    @staticmethod
    def _gray_match(bg, slider):
        import cv2
        result = cv2.matchTemplate(bg, slider, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        return max_loc[0], max_val

    @staticmethod
    def _laplacian_match(bg, slider):
        import cv2
        bg_lap = cv2.Laplacian(bg, cv2.CV_64F)
        slider_lap = cv2.Laplacian(slider, cv2.CV_64F)
        bg_lap = np.uint8(np.absolute(bg_lap))
        slider_lap = np.uint8(np.absolute(slider_lap))
        result = cv2.matchTemplate(bg_lap, slider_lap, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        return max_loc[0], max_val

    @staticmethod
    def ocr_preprocess(image_path: str) -> str:
        """OCR预处理：灰度→二值化→降噪→Tesseract"""
        import cv2
        import pytesseract
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        kernel = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        text = pytesseract.image_to_string(cleaned, lang='eng+chi_sim', config='--psm 7 --oem 3')
        return text.strip()


# ============================================================
# L4: YOLOv8 引擎（点选验证码目标检测）
# ============================================================
class YOLOEngine:
    """YOLOv8 — 自定义目标检测，适合点选验证码"""

    def __init__(self, model_path: str = "yolov8n.pt"):
        from ultralytics import YOLO
        self._model = YOLO(model_path)

    def detect(self, image_path: str) -> list:
        results = self._model(image_path, verbose=False)
        detections = []
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detections.append({
                    "x_center": int((x1 + x2) / 2),
                    "y_center": int((y1 + y2) / 2),
                    "bbox": [int(x1), int(y1), int(x2), int(y2)],
                    "confidence": round(float(box.conf[0]), 4),
                    "class": int(box.cls[0]),
                })
        return sorted(detections, key=lambda d: d["confidence"], reverse=True)


# ============================================================
# L5: CapSolver 云端API（兜底）
# ============================================================
class CapSolverEngine:
    """CapSolver API — 云端兜底，支持reCAPTCHA/hCaptcha/Geetest/Cloudflare"""

    def __init__(self, api_key: str = None):
        import capsolver
        self._key = api_key or os.environ.get("CAPSOLVER_API_KEY", "")
        if self._key:
            capsolver.api_key = self._key

    def solve(self, task_type: str, **kwargs) -> dict:
        import capsolver
        if not self._key:
            return {"error": "CAPSOLVER_API_KEY未设置", "engine": "capsolver"}
        try:
            result = capsolver.solve({"type": task_type, **kwargs})
            result["engine"] = "capsolver"
            return result
        except Exception as e:
            return {"error": str(e), "engine": "capsolver"}


# ============================================================
# 行为轨迹生成器
# ============================================================
class TrackGenerator:
    """生成拟人化滑动轨迹"""

    @staticmethod
    def bezier(start_x: int, end_x: int, y: int = 0, points: int = 30) -> list:
        """三阶贝塞尔曲线 + 高斯噪声 + 变速时间"""
        t = np.linspace(0, 1, points)
        cp1_x = start_x + np.random.uniform(0.2, 0.4) * (end_x - start_x)
        cp2_x = start_x + np.random.uniform(0.6, 0.8) * (end_x - start_x)
        cp1_y = y + np.random.uniform(-40, 40)
        cp2_y = y + np.random.uniform(-20, 20)

        x = (1-t)**3*start_x + 3*(1-t)**2*t*cp1_x + 3*(1-t)*t**2*cp2_x + t**3*end_x
        y_arr = (1-t)**3*y + 3*(1-t)**2*t*cp1_y + 3*(1-t)*t**2*cp2_y + t**3*y

        x += np.random.normal(0, 0.5, points)
        y_arr += np.random.normal(0, 0.3, points)

        # 变速：慢启→加速→过冲→回退
        n1, n2 = points // 3, points // 3
        n3 = points - n1 - n2
        dt = np.concatenate([
            np.random.uniform(15, 35, n1),    # 起步慢
            np.random.uniform(5, 12, n2),     # 中间快
            np.random.uniform(20, 50, n3),    # 结尾慢（拟人犹豫）
        ])

        track = []
        t_acc = 0
        for i in range(points):
            t_acc += dt[i]
            track.append({"x": int(x[i]), "y": int(y_arr[i]), "t": int(t_acc)})

        # 过冲回退（20%概率）
        if np.random.random() < 0.2:
            overshoot = int(np.random.uniform(3, 8))
            track.append({"x": int(end_x) + overshoot, "y": int(y_arr[-1]), "t": int(t_acc + 30)})
            track.append({"x": int(end_x), "y": int(y_arr[-1]), "t": int(t_acc + 80)})

        return track

    @staticmethod
    def human_like(start_x: int, end_x: int, y: int = 0) -> list:
        """更真实的人类轨迹：加速度变化 + 微停顿"""
        distance = end_x - start_x
        # 根据距离自适应点数
        points = max(20, min(60, int(distance * 0.3)))
        track = TrackGenerator.bezier(start_x, end_x, y, points)

        # 随机微停顿（模拟人类犹豫）
        if len(track) > 10 and np.random.random() < 0.3:
            pause_idx = np.random.randint(len(track) // 3, 2 * len(track) // 3)
            pause_ms = int(np.random.uniform(50, 150))
            for i in range(pause_idx, len(track)):
                track[i]["t"] += pause_ms

        return track


# ============================================================
# 统一调度器
# ============================================================
class CaptchaSolver:
    """多引擎统一调度 — 自动选择最优引擎，失败自动降级"""

    def __init__(self):
        self._ddddocr = None
        self._recognizer = None
        self._yolo = None
        self._capsolver = None

    def ocr(self, image_path: str) -> dict:
        """OCR文字验证码识别"""
        start = time.time()

        # L1: ddddocr
        if ENGINES.get("ddddocr"):
            try:
                if not self._ddddocr:
                    self._ddddocr = DdddOcrEngine()
                with open(image_path, "rb") as f:
                    text = self._ddddocr.ocr(f.read())
                return {"text": text, "engine": "ddddocr", "ms": _ms(start)}
            except Exception as e:
                pass

        # L3: OpenCV + Tesseract
        if ENGINES.get("cv2") and ENGINES.get("tesseract"):
            try:
                text = OpenCVEngine.ocr_preprocess(image_path)
                return {"text": text, "engine": "opencv+tesseract", "ms": _ms(start)}
            except Exception:
                pass

        return {"error": "无可用OCR引擎", "ms": _ms(start)}

    def slide(self, bg_path: str, slider_path: str = None) -> dict:
        """滑块缺口定位 — 多引擎融合"""
        start = time.time()
        results = []

        # L2: captcha-recognizer（最优先，精度最高）
        if ENGINES.get("captcha_recognizer"):
            try:
                if not self._recognizer:
                    self._recognizer = CaptchaRecognizerEngine()
                r = self._recognizer.slide_detect(bg_path)
                if r.get("confidence", 0) > 0.5:
                    results.append(r)
            except Exception:
                pass

        # L1: ddddocr
        if ENGINES.get("ddddocr") and slider_path:
            try:
                if not self._ddddocr:
                    self._ddddocr = DdddOcrEngine()
                with open(slider_path, "rb") as f1, open(bg_path, "rb") as f2:
                    r = self._ddddocr.slide_match(f1.read(), f2.read())
                    results.append(r)
            except Exception:
                pass

        # L3: OpenCV（slider_path必须）
        if ENGINES.get("cv2") and slider_path:
            try:
                r = OpenCVEngine.slide_match(bg_path, slider_path)
                if "error" not in r:
                    results.append(r)
            except Exception:
                pass

        if not results:
            return {"error": "无可用滑块引擎或识别失败", "ms": _ms(start)}

        # 取置信度最高的结果
        best = max(results, key=lambda r: r.get("confidence", 0))
        best["all_engines"] = results
        best["ms"] = _ms(start)
        return best

    def detect(self, image_path: str, model_path: str = "yolov8n.pt") -> dict:
        """点选验证码目标检测"""
        start = time.time()

        # L1: ddddocr det模式
        if ENGINES.get("ddddocr"):
            try:
                if not self._ddddocr:
                    self._ddddocr = DdddOcrEngine()
                with open(image_path, "rb") as f:
                    boxes = self._ddddocr.detect(f.read())
                if boxes:
                    return {"detections": boxes, "engine": "ddddocr", "ms": _ms(start)}
            except Exception:
                pass

        # L4: YOLOv8
        if ENGINES.get("ultralytics"):
            try:
                if not self._yolo:
                    self._yolo = YOLOEngine(model_path)
                detections = self._yolo.detect(image_path)
                return {"detections": detections, "engine": "yolov8", "ms": _ms(start)}
            except Exception:
                pass

        return {"error": "无可用检测引擎", "ms": _ms(start)}

    def cloud(self, task_type: str, **kwargs) -> dict:
        """云端API兜底"""
        if not self._capsolver:
            self._capsolver = CapSolverEngine()
        return self._capsolver.solve(task_type, **kwargs)

    def status(self) -> dict:
        """返回所有引擎状态"""
        return {
            "engines": ENGINES,
            "priority": [
                {"level": "L1", "name": "ddddocr", "status": ENGINES.get("ddddocr"), "capability": "OCR/检测/滑块"},
                {"level": "L2", "name": "captcha-recognizer", "status": ENGINES.get("captcha_recognizer"), "capability": "滑块缺口(ONNX深度学习)"},
                {"level": "L3", "name": "OpenCV+Tesseract", "status": ENGINES.get("cv2") and ENGINES.get("tesseract"), "capability": "模板匹配/OCR"},
                {"level": "L4", "name": "YOLOv8", "status": ENGINES.get("ultralytics"), "capability": "点选目标检测"},
                {"level": "L5", "name": "CapSolver", "status": ENGINES.get("capsolver"), "capability": "云端兜底(reCAPTCHA/hCaptcha/Geetest)"},
            ],
            "capsolver_key": "已配置" if os.environ.get("CAPSOLVER_API_KEY") else "未配置",
        }


def _ms(start):
    return int((time.time() - start) * 1000)


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="ARC Team 多引擎验证码识别系统")
    sub = parser.add_subparsers(dest="cmd")

    # ocr
    p_ocr = sub.add_parser("ocr", help="OCR文字验证码")
    p_ocr.add_argument("image", help="图片路径")

    # slide
    p_slide = sub.add_parser("slide", help="滑块缺口定位")
    p_slide.add_argument("--bg", required=True, help="背景图")
    p_slide.add_argument("--slider", default=None, help="滑块图(可选)")
    p_slide.add_argument("--track", action="store_true", help="同时生成轨迹")

    # detect
    p_detect = sub.add_parser("detect", help="点选目标检测")
    p_detect.add_argument("image", help="图片路径")
    p_detect.add_argument("--model", default="yolov8n.pt", help="YOLO模型路径")

    # track
    p_track = sub.add_parser("track", help="生成滑动轨迹")
    p_track.add_argument("--start", type=int, default=0)
    p_track.add_argument("--end", type=int, required=True)
    p_track.add_argument("--points", type=int, default=30)
    p_track.add_argument("--human", action="store_true", help="更拟人化")

    # cloud
    p_cloud = sub.add_parser("cloud", help="云端API兜底")
    p_cloud.add_argument("--type", required=True, help="任务类型(如ReCaptchaV2TaskProxyLess)")
    p_cloud.add_argument("--sitekey", help="站点key")
    p_cloud.add_argument("--url", help="页面URL")

    # status
    sub.add_parser("status", help="引擎状态")

    args = parser.parse_args()
    solver = CaptchaSolver()

    if args.cmd == "ocr":
        print(json.dumps(solver.ocr(args.image), ensure_ascii=False, indent=2))

    elif args.cmd == "slide":
        result = solver.slide(args.bg, args.slider)
        if args.track and "x" in result:
            result["track"] = TrackGenerator.human_like(0, result["x"])
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif args.cmd == "detect":
        print(json.dumps(solver.detect(args.image, args.model), ensure_ascii=False, indent=2))

    elif args.cmd == "track":
        fn = TrackGenerator.human_like if args.human else TrackGenerator.bezier
        track = fn(args.start, args.end) if args.human else fn(args.start, args.end, points=args.points)
        print(json.dumps(track, indent=2))

    elif args.cmd == "cloud":
        kwargs = {}
        if args.sitekey: kwargs["websiteKey"] = args.sitekey
        if args.url: kwargs["websiteURL"] = args.url
        print(json.dumps(solver.cloud(args.type, **kwargs), ensure_ascii=False, indent=2))

    elif args.cmd == "status":
        print(json.dumps(solver.status(), ensure_ascii=False, indent=2))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
