"""Allow running as: python -m eventbus"""
from .cli import main
import sys
sys.exit(main())
