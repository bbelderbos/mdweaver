"""Pytest fixtures for mdweaver tests."""

import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_md_file(temp_dir):
    """Create a sample markdown file."""
    md_file = temp_dir / "sample.md"
    md_file.write_text("""# Sample Document

This is a sample markdown document.

## Section 1

Some content with **bold** and *italic* text.

- Item 1
- Item 2
- Item 3

## Section 2

Here's some code:

```python
def hello():
    print("Hello, World!")
```

And a table:

| Name | Value |
|------|-------|
| A    | 1     |
| B    | 2     |
""")
    return md_file


@pytest.fixture
def sample_md_dir(temp_dir):
    """Create a directory with multiple markdown files:

    ├── 01-intro.md
    ├── 02-getting-started.md
    └── advanced
        └── 03-advanced.md
    """
    docs_dir = temp_dir / "docs"
    docs_dir.mkdir()

    (docs_dir / "01-intro.md").write_text("""# Introduction

Welcome to the documentation.
""")

    (docs_dir / "02-getting-started.md").write_text("""# Getting Started

Here's how to get started.

## Installation

Run the installer.
""")

    # Nested directory
    subdir = docs_dir / "advanced"
    subdir.mkdir()
    (subdir / "03-advanced.md").write_text("""# Advanced Topics

Deep dive into advanced features.
""")

    return docs_dir


@pytest.fixture
def md_with_generics(temp_dir):
    """Create markdown with generic type syntax."""
    md_file = temp_dir / "generics.md"
    md_file.write_text("""# Generics Example

The function returns Result<T, E> for error handling.

Use `Option<String>` for optional strings.

```rust
fn example<T>(value: T) -> Result<T, Error> {
    Ok(value)
}
```
""")
    return md_file
