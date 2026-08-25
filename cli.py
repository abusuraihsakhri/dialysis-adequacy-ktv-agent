#!/usr/bin/env python3
"""
CLI for Dialysis Adequacy Kt/V Calculator.
Delegates to ktv_sentinel.py for all calculations.
"""
import sys
from ktv_sentinel import main

if __name__ == "__main__":
    sys.exit(main())
