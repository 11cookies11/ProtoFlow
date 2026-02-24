from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dsl_runtime.engine.runner import run_dsl


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="ProtoFlow DSL 执行入口")
    parser.add_argument("script", help="DSL YAML 文件路径")
    args = parser.parse_args(argv)
    return run_dsl(args.script)


if __name__ == "__main__":
    sys.exit(main())
