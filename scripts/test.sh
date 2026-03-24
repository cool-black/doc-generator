#!/bin/bash
# TDD测试脚本

echo "=== DocGen Test Suite ==="

# 显示帮助
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "用法: ./scripts/test.sh [选项]"
    echo ""
    echo "选项:"
    echo "  (无)      运行所有测试"
    echo "  --cov     运行测试并检查80%覆盖率"
    echo "  --watch   监视模式，文件变化自动运行"
    echo "  --unit    仅运行单元测试"
    echo "  --int     仅运行集成测试"
    echo ""
    exit 0
fi

# 带覆盖率的测试
if [ "$1" = "--cov" ]; then
    echo "Running tests with 80% coverage check..."
    python -m pytest \
        --cov=src/doc_gen \
        --cov-report=term-missing \
        --cov-report=html \
        --cov-fail-under=80 \
        tests/
    exit $?
fi

# 监视模式
if [ "$1" = "--watch" ]; then
    echo "Starting watch mode..."
    python -m pytest -f tests/
    exit $?
fi

# 仅单元测试
if [ "$1" = "--unit" ]; then
    echo "Running unit tests only..."
    python -m pytest -m unit tests/
    exit $?
fi

# 仅集成测试
if [ "$1" = "--int" ]; then
    echo "Running integration tests only..."
    python -m pytest -m integration tests/
    exit $?
fi

# 默认：运行所有测试
echo "Running all tests..."
python -m pytest tests/
