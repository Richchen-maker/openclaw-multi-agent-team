#!/bin/bash
# Hotfix: ddddocr 1.6.0 import bug
# 问题: 1.6.0重构core.py→core/、utils.py→utils/，但__init__.py仍引用旧导出名
# 修法: 在新package的__init__.py中桥接旧文件的导出
set -euo pipefail

DDDDOCR_PKG="${1:-$(python3 -c 'import ddddocr; import os; print(os.path.dirname(ddddocr.__file__))' 2>/dev/null || echo '')}"
if [ -z "$DDDDOCR_PKG" ] || [ ! -d "$DDDDOCR_PKG/core" ]; then
    echo "❌ ddddocr not found or no core/ directory"
    exit 1
fi

echo "Patching $DDDDOCR_PKG ..."

# Check if already patched
if grep -q "_core_legacy" "$DDDDOCR_PKG/core/__init__.py" 2>/dev/null; then
    echo "✅ Already patched"
    exit 0
fi

# Patch core/__init__.py
cat > "$DDDDOCR_PKG/core/__init__.py" << 'PYEOF'
from .base import BaseEngine
from .ocr_engine import OCREngine
from .detection_engine import DetectionEngine
from .slide_engine import SlideEngine
import importlib.util as _ilu, os as _os, sys as _sys
_p = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), "core.py")
_s = _ilu.spec_from_file_location("ddddocr._core_legacy", _p)
_m = _ilu.module_from_spec(_s); _sys.modules["ddddocr._core_legacy"] = _m
_s.loader.exec_module(_m); DdddOcr = _m.DdddOcr
del _ilu, _os, _sys, _s, _m, _p
__all__ = ['BaseEngine','OCREngine','DetectionEngine','SlideEngine','DdddOcr']
PYEOF

# Patch utils/__init__.py
cat > "$DDDDOCR_PKG/utils/__init__.py" << 'PYEOF'
from .image_io import base64_to_image, get_img_base64, png_rgba_black_preprocess
from .exceptions import DDDDOCRError, ModelLoadError, ImageProcessError
from .validators import validate_image_input, validate_model_config
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_IMAGE_SIDE = 4096
ALLOWED_IMAGE_FORMATS = {"png","jpg","jpeg","gif","bmp","tif","tiff","webp"}
class TypeError(Exception): pass
class DdddOcrInputError(TypeError): pass
class InvalidImageError(DdddOcrInputError): pass
from typing import Union
def _coerce_bool(v, f): return v if isinstance(v,bool) else str(v).lower() in ('true','1','yes')
def _coerce_int(v, f): return v if isinstance(v,int) else int(v)
def _coerce_positive_int(v, f):
    r = _coerce_int(v,f)
    if r <= 0: raise ValueError(f)
    return r
def _ensure_file_exists(p, d):
    import os
    if not os.path.isfile(p): raise FileNotFoundError(f"{d}: {p}")
PYEOF

find "$DDDDOCR_PKG" -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
echo "✅ ddddocr 1.6.0 patched"
