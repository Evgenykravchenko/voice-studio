#!/usr/bin/env python3
"""A dependency-free check used before launching an installed or moved studio."""
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from voice_cloner.runtimes import interpreter_local

if __name__=='__main__':
    raise SystemExit(0 if interpreter_local('mlx-speech',ROOT) else 1)
