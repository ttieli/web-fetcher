#!/usr/bin/env python3
"""
执行SPA诊断

简化的执行入口，调用spa_diagnosis.py的主函数

Author: Cody (Full-Stack Engineer)
Date: 2025-09-30
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import and run the main diagnostic function
from diagnostics.spa_diagnosis import main

if __name__ == "__main__":
    sys.exit(main())