# TDD 工作流指南

## 快速开始

```bash
# 运行所有测试
python -m pytest

# 运行测试并检查覆盖率
python -m pytest --cov=src/doc_gen --cov-report=term-missing

# 运行单元测试（跳过集成测试）
python -m pytest -m unit

# 监视模式（开发时使用）
python -m pytest -f
```

## TDD 开发流程

### 1. 红-绿-重构循环

```
写测试 → 运行测试(失败/红) → 写代码 → 运行测试(通过/绿) → 重构
```

### 2. 具体步骤

#### Step 1: 编写用户故事

```markdown
作为 [角色]，我想 [功能]，以便 [价值]

例如：
作为用户，我想上传文档作为参考资料，
以便生成更准确的文档内容。
```

#### Step 2: 编写测试文件

在 `tests/` 目录创建 `test_<feature>.py`：

```python
"""测试文档上传功能"""

import pytest
from doc_gen.sources.parser import parse_document


class TestDocumentUpload:
    """文档上传功能测试"""

    def test_parse_txt_file(self, tmp_path):
        """应正确解析txt文件"""
        # Arrange
        file = tmp_path / "test.txt"
        file.write_text("Hello World")

        # Act
        result = parse_document(file)

        # Assert
        assert result.title == "test.txt"
        assert result.content == "Hello World"

    def test_parse_nonexistent_file_raises_error(self):
        """文件不存在时应抛出异常"""
        with pytest.raises(FileNotFoundError):
            parse_document("/nonexistent/file.txt")

    def test_parse_empty_file_returns_empty_content(self, tmp_path):
        """空文件应返回空内容"""
        file = tmp_path / "empty.txt"
        file.write_text("")

        result = parse_document(file)

        assert result.content == ""
```

#### Step 3: 运行测试（应该失败）

```bash
python -m pytest tests/test_document_upload.py -v
```

预期：测试失败，因为功能尚未实现。

#### Step 4: 实现功能

```python
# src/doc_gen/sources/parser.py
from pathlib import Path
from doc_gen.models.document import SourceDocument


def parse_document(file_path: str | Path) -> SourceDocument:
    """解析文档文件。"""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    content = path.read_text(encoding="utf-8")

    return SourceDocument(
        title=path.name,
        content=content,
        source_type="file"
    )
```

#### Step 5: 运行测试（应该通过）

```bash
python -m pytest tests/test_document_upload.py -v
```

预期：所有测试通过。

#### Step 6: 重构

保持测试通过的前提下优化代码：
- 移除重复代码
- 改善命名
- 优化性能

#### Step 7: 验证覆盖率

```bash
python -m pytest --cov=src/doc_gen --cov-fail-under=80
```

---

## 测试类型

### 单元测试

- 测试单个函数/类
- 使用 mocks 隔离依赖
- 快速执行 (< 50ms)

```python
def test_slugify_handles_special_chars():
    """slugify应正确处理特殊字符"""
    from doc_gen.utils.text import slugify

    assert slugify("Hello & World!") == "hello_world"
    assert slugify("C++ Programming") == "c_programming"
```

### 集成测试

- 测试模块间交互
- 标记 `@pytest.mark.integration`

```python
@pytest.mark.integration
def test_database_save_and_retrieve():
    """应能保存并检索项目"""
    from doc_gen.storage.project import ProjectStore

    store = ProjectStore()
    project = store.create(name="Test")

    retrieved = store.get(project.id)

    assert retrieved.name == "Test"
```

### 边界测试

```python
@pytest.mark.parametrize("input,expected", [
    ("", "untitled"),           # 空字符串
    ("a" * 1000, "..."),        # 超长字符串
    ("   ", "untitled"),         # 仅空白
    ("UPPER", "upper"),          # 大写
    ("Mixed123", "mixed123"),    # 混合
])
def test_slugify_edge_cases(input, expected):
    """测试边界情况"""
    result = slugify(input)
    if expected == "...":
        assert len(result) <= 100
    else:
        assert result == expected
```

---

## 测试最佳实践

### ✅ 应该做的

1. **测试先行**：先写测试，后写实现
2. **描述性命名**：`test_<action>_<expected_result>_<context>`
3. **AAA模式**：Arrange-Act-Assert
4. **独立测试**：每个测试自包含，不依赖其他测试
5. **边界覆盖**：空值、最大值、错误输入
6. **错误路径**：不只测试成功场景

### ❌ 不应该做的

```python
# 错误：测试多个行为
def test_everything():
    result = do_something()
    assert result.a == 1
    assert result.b == 2
    assert result.c == 3  # 应拆分为3个测试

# 错误：测试实现细节
def test_internal():
    obj = MyClass()
    obj._private_method()  # 测试私有方法
    assert obj._state == 1

# 错误：无描述性名称
def test1():
    assert foo() == True
```

---

## Mock 技巧

### Mock LLM 客户端

```python
from unittest.mock import Mock, patch


def test_generate_with_mock_llm():
    """使用mock测试生成逻辑"""
    mock_client = Mock()
    mock_client.generate.return_value = {
        "content": "Generated text",
        "tokens_used": 100
    }

    result = generate_content(client=mock_client, prompt="Hello")

    assert result == "Generated text"
    mock_client.generate.assert_called_once_with(prompt="Hello")
```

### Patch 环境变量

```python
@patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
def test_config_reads_env():
    """配置应从环境变量读取"""
    config = load_config()
    assert config.openai_api_key == "test-key"
```

---

## 覆盖率要求

- **目标**: 80%+ 覆盖率
- **排除**: CLI 入口、纯数据类
- **重点**: 核心业务逻辑、边界处理、错误处理

```bash
# 生成 HTML 覆盖率报告
python -m pytest --cov=src/doc_gen --cov-report=html

# 查看报告
open htmlcov/index.html
```

---

## 开发工作流

```bash
# 1. 创建功能分支
git checkout -b feature/new-feature

# 2. 编写测试
# tests/test_new_feature.py

# 3. 运行测试（红）
python -m pytest tests/test_new_feature.py

# 4. 实现功能
# src/doc_gen/core/new_feature.py

# 5. 运行测试（绿）
python -m pytest tests/test_new_feature.py

# 6. 验证覆盖率
python -m pytest --cov=src/doc_gen --cov-fail-under=80

# 7. 提交
git add .
git commit -m "feat: add new feature with tests"
```
