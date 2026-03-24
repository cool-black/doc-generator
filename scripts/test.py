#!/usr/bin/env python3
"""TDD测试运行脚本

用法:
    python scripts/test.py          # 运行所有测试
    python scripts/test.py --cov    # 运行测试并检查80%覆盖率
    python scripts/test.py --watch  # 监视模式，自动重跑
    python scripts/test.py --unit   # 仅单元测试
    python scripts/test.py --int    # 仅集成测试
    python scripts/test.py -v       # 详细输出
"""

import sys
import subprocess


def run_tests():
    args = sys.argv[1:]

    # 帮助
    if "--help" in args or "-h" in args:
        print(__doc__)
        return 0

    cmd = ["python", "-m", "pytest"]

    # 带覆盖率检查
    if "--cov" in args:
        cmd.extend([
            "--cov=src/doc_gen",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-fail-under=80",
        ])
        args.remove("--cov")

    # 监视模式
    if "--watch" in args or "-f" in args:
        cmd.append("-f")
        if "--watch" in args:
            args.remove("--watch")

    # 单元测试
    if "--unit" in args:
        cmd.extend(["-m", "unit"])
        args.remove("--unit")

    # 集成测试
    if "--int" in args:
        cmd.extend(["-m", "integration"])
        args.remove("--int")

    # 添加剩余参数
    cmd.extend(args)

    # 默认添加 tests/ 目录
    if not any(a.endswith(".py") or a.startswith("tests/") for a in args if not a.startswith("-")):
        cmd.append("tests/")

    print(f"=== DocGen Test Suite ===")
    print(f"Command: {' '.join(cmd)}\n")

    return subprocess.call(cmd)


if __name__ == "__main__":
    sys.exit(run_tests())
