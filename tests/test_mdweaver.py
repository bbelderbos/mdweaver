"""Tests for mdweaver core functionality."""

import pytest

from mdweaver.generate_pdf import (
    DEFAULT_EXCLUDES,
    WEASYPRINT_AVAILABLE,
    convert_md_to_html,
    generate_epub,
    generate_pdf,
    get_md_files,
    preprocess_markdown,
)


class TestGetMdFiles:
    """Tests for get_md_files function."""

    def test_single_md_file(self, sample_md_file):
        """Should return single file when given a markdown file path."""
        files = get_md_files(sample_md_file)
        assert len(files) == 1
        assert files[0] == sample_md_file

    def test_non_md_file_returns_empty(self, temp_dir):
        """Should return empty list for non-markdown files."""
        txt_file = temp_dir / "test.txt"
        txt_file.write_text("not markdown")
        files = get_md_files(txt_file)
        assert files == []

    def test_directory_recursive(self, sample_md_dir):
        """Should find all markdown files recursively in directory."""
        files = get_md_files(sample_md_dir, recursive=True)
        assert len(files) == 3
        names = [f.name for f in files]
        assert "01-intro.md" in names
        assert "02-getting-started.md" in names
        assert "03-advanced.md" in names

    def test_directory_non_recursive(self, sample_md_dir):
        """Should find only top-level markdown files when not recursive."""
        files = get_md_files(sample_md_dir, recursive=False)
        assert len(files) == 2
        names = [f.name for f in files]
        assert "01-intro.md" in names
        assert "02-getting-started.md" in names
        assert "03-advanced.md" not in names

    def test_empty_directory(self, temp_dir):
        """Should return empty list for directory with no markdown files."""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()
        files = get_md_files(empty_dir)
        assert files == []

    def test_files_are_sorted(self, sample_md_dir):
        """Should return files sorted by path."""
        files = get_md_files(sample_md_dir, recursive=True)
        paths = [str(f) for f in files]
        assert paths == sorted(paths)

    def test_directory_recursive_with_exclude_file_pattern(self, sample_md_dir):
        """Should exclude matching markdown files when exclude patterns are provided."""
        files = get_md_files(
            sample_md_dir, recursive=True, exclude=["**/03-advanced.md"]
        )
        names = [f.name for f in files]
        assert len(files) == 2
        assert "03-advanced.md" not in names

    def test_directory_default_excludes_skip_output_dir(self, sample_md_dir):
        """Should skip markdown files under default excluded dirs (e.g. output/)."""
        output_dir = sample_md_dir / "output"
        output_dir.mkdir()
        (output_dir / "ignored.md").write_text("# Ignored\n", encoding="utf-8")

        files = get_md_files(sample_md_dir, recursive=True, exclude=DEFAULT_EXCLUDES)
        paths = [str(f) for f in files]
        assert not any("output/ignored.md" in p.replace("\\", "/") for p in paths)

    def test_multiple_exclude_patterns(self, sample_md_dir):
        """Should exclude files matching any of multiple exclude patterns."""
        # create two extra markdown files we want to ignore
        (sample_md_dir / "README.md").write_text("# Readme\n", encoding="utf-8")
        (sample_md_dir / "EXERCISE_SPECS.md").write_text("# Specs\n", encoding="utf-8")

        files = get_md_files(
            sample_md_dir,
            recursive=True,
            exclude=["**/README.md", "**/EXERCISE_SPECS.md"],
        )
        names = {f.name for f in files}
        assert "README.md" not in names
        assert "EXERCISE_SPECS.md" not in names


class TestPreprocessMarkdown:
    """Tests for preprocess_markdown function."""

    def test_escapes_generic_types(self):
        """Should escape angle brackets in generic type syntax."""
        md = "The function returns Result<T, E> for errors."
        result = preprocess_markdown(md)
        assert "&lt;T, E&gt;" in result
        assert "<T, E>" not in result

    def test_preserves_backtick_code(self):
        """Should not escape generics inside backticks."""
        md = "Use `Result<T, E>` for error handling."
        result = preprocess_markdown(md)
        assert "`Result<T, E>`" in result

    def test_preserves_code_blocks(self):
        """Should not escape generics inside code blocks."""
        md = """Some text.

```rust
fn example<T>(value: T) -> Result<T, Error> {
    Ok(value)
}
```
"""
        result = preprocess_markdown(md)
        assert "Result<T, Error>" in result  # Inside code block, unchanged

    def test_adds_blank_line_before_list(self):
        """Should add blank line before bullet list when missing."""
        md = """Some paragraph text.
- Item 1
- Item 2"""
        result = preprocess_markdown(md)
        lines = result.splitlines()
        # Find the line before "- Item 1"
        for i, line in enumerate(lines):
            if line == "- Item 1" and i > 0:
                assert lines[i - 1] == "", "Expected blank line before list"

    def test_adds_blank_line_before_numbered_list(self):
        """Should add blank line before numbered list when missing."""
        md = """Some paragraph text.
1. First item
2. Second item"""
        result = preprocess_markdown(md)
        lines = result.splitlines()
        for i, line in enumerate(lines):
            if line == "1. First item" and i > 0:
                assert lines[i - 1] == "", "Expected blank line before numbered list"

    def test_no_extra_blank_after_header(self):
        """Should not add extra blank line when list follows header."""
        md = """## Header
- Item 1"""
        result = preprocess_markdown(md)
        # Should not have double blank lines
        assert "\n\n\n" not in result


class TestConvertMdToHtml:
    """Tests for convert_md_to_html function."""

    def test_basic_conversion(self):
        """Should convert basic markdown to HTML."""
        md = "# Hello\n\nThis is a paragraph."
        html = convert_md_to_html(md)
        assert "<h1" in html  # h1 tag may have attributes like id
        assert "Hello" in html
        assert "<p>" in html

    def test_code_blocks_highlighted(self):
        """Should apply syntax highlighting to code blocks."""
        md = """```python
def hello():
    print("Hello")
```"""
        html = convert_md_to_html(md)
        assert 'class="highlight"' in html

    def test_tables_converted(self):
        """Should convert markdown tables to HTML."""
        md = """| A | B |
|---|---|
| 1 | 2 |"""
        html = convert_md_to_html(md)
        assert "<table>" in html
        assert "<th>" in html
        assert "<td>" in html

    def test_inline_code(self):
        """Should convert inline code."""
        md = "Use `print()` function."
        html = convert_md_to_html(md)
        assert "<code>" in html
        assert "print()" in html

    def test_bold_and_italic(self):
        """Should convert bold and italic text."""
        md = "This is **bold** and *italic*."
        html = convert_md_to_html(md)
        assert "<strong>" in html or "<b>" in html
        assert "<em>" in html or "<i>" in html


class TestGenerateFunctions:
    """Tests for generate_pdf and generate_epub (integration tests)."""

    @pytest.mark.skipif(
        not WEASYPRINT_AVAILABLE, reason="WeasyPrint system dependencies not available"
    )
    def test_generate_pdf_creates_file(self, sample_md_file, temp_dir):
        """Should create a PDF file from markdown."""
        output_dir = temp_dir / "output"
        result = generate_pdf(sample_md_file, output_dir)
        assert result.exists()
        assert result.suffix == ".pdf"

    def test_generate_epub_creates_file(self, sample_md_file, temp_dir):
        """Should create an EPUB file from markdown."""
        output_dir = temp_dir / "output"
        result = generate_epub(sample_md_file, output_dir)
        assert result.exists()
        assert result.suffix == ".epub"

    def test_generate_with_custom_title(self, sample_md_file, temp_dir):
        """Should use custom title when provided."""
        output_dir = temp_dir / "output"
        result = generate_epub(sample_md_file, output_dir, title="Custom Title")
        assert result.exists()

    def test_generate_from_directory(self, sample_md_dir, temp_dir):
        """Should generate from directory with multiple files."""
        output_dir = temp_dir / "output"
        result = generate_epub(sample_md_dir, output_dir)
        assert result.exists()
        assert result.name == "docs.epub"
