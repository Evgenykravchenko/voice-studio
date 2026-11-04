#!/usr/bin/env python3
"""Check a local port without proxying requests or trusting another project/server."""
import argparse
import json
from pathlib import Path
import socket
from urllib.request import ProxyHandler,build_opener


def matches_project(value,root):
    if not isinstance(value,dict) or value.get('status')!='ready':return False
    declared=value.get('projectRoot')
    return isinstance(declared,str) and bool(declared) and Path(declared).is_absolute() and Path(declared).resolve()==root.resolve()


def check(port,root):
    try:
        with build_opener(ProxyHandler({})).open(f'http://127.0.0.1:{port}/api/health',timeout=2) as response:
            value=json.load(response)
        if matches_project(value,root):return 0
    except (OSError,ValueError,TypeError):pass
    try:
        with socket.create_connection(('127.0.0.1',port),timeout=.5):return 2
    except OSError:return 1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,required=True)
    parser.add_argument('--root',type=Path,required=True)
    args=parser.parse_args()
    return check(args.port,args.root)


if __name__=='__main__':raise SystemExit(main())
