#!/usr/bin/env python3
"""Repair previously installed optional runtimes after moving/updating the project."""
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from voice_cloner import runtimes


def repair(root=ROOT):
    for name in runtimes.SPECS:
        folder=runtimes.python_for(name,root).parent.parent
        if folder.is_dir() and not runtimes.ready(name,root):
            print(f'Подготавливаем установленное окружение {name}…',flush=True)
            runtimes.install(name,root)


if __name__=='__main__':repair()
