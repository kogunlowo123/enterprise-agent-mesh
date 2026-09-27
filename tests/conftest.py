"""Test configuration and fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

# Add service source directories to Python path
_PROJECT_ROOT = Path(__file__).parent.parent

sys.path.insert(0, str(_PROJECT_ROOT / "services" / "api" / "src"))
sys.path.insert(0, str(_PROJECT_ROOT / "services" / "agent-runtime" / "src"))
sys.path.insert(0, str(_PROJECT_ROOT / "services" / "rag-core" / "src"))
