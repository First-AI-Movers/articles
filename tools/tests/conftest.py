#!/usr/bin/env python3
"""pytest configuration for tools/tests/."""

import sys
from pathlib import Path

# Add tools/ to path so test modules can import production modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
