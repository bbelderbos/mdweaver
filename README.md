# mdweaver

Weave markdown files into beautifully formatted PDFs and EPUBs.

`mdweaver` is a command-line tool that converts your Markdown documentation into professional-looking PDF and EPUB files. It handles syntax highlighting, recursive file discovery, common rendering issues, and sensible default exclusions automatically.

## Features

- **Multiple Formats**: Generate PDF, EPUB, or both simultaneously.
- **Recursive Processing**: Convert a single file or an entire directory of documentation.
- **Default Exclusions**: Skips common “noise” directories by default:
  - `.git`, `.venv` / `venv`, `node_modules`, `__pycache__`, `.pytest_cache`, `output`
- **Syntax Highlighting**: Includes Pygments support (Monokai theme) for code blocks.
- **Smart Preprocessing**: Automatically fixes common Markdown issues like:
  - Escaping generic type parameters (e.g., `Result<T, E>`).
  - Correcting list spacing for proper rendering.
- **Customization**:
  - Add watermarks to PDFs (e.g., `"DRAFT"`).
  - Set custom document titles and author metadata.
  - Exclude additional paths via glob patterns.
- **Clean Typography**: Uses optimized CSS for print (A4) and e-reader layouts.

## Prerequisites

For PDF generation, `mdweaver` relies on **WeasyPrint**, which requires system libraries (Pango, Cairo, etc.) to be installed. EPUB generation works without these dependencies.

**macOS:**
```bash
brew install pango
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt install libpango-1.0-0 libpangoft2-1.0-0
```

See the WeasyPrint documentation for other platforms: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html

## Installation

This project is managed with [`uv`](https://github.com/astral-sh/uv).

```bash
# Install dependencies
uv sync
```

Or using pip:

```bash
pip install mdweaver
```

### macOS (Homebrew / Apple Silicon) – WeasyPrint dylib lookup

If `import weasyprint` fails with a `libgobject-2.0-0` / `gobject` missing error on macOS, install the native deps with Homebrew and expose Homebrew’s lib directory to the dynamic loader:

```bash
brew install glib pango cairo gdk-pixbuf libffi
export DYLD_FALLBACK_LIBRARY_PATH="$(brew --prefix)/lib:${DYLD_FALLBACK_LIBRARY_PATH}"
uv run python -c "import weasyprint; print(weasyprint.__version__)"
```

You can add the `export DYLD_FALLBACK_LIBRARY_PATH=...` line to your shell config (typically `~/.zshrc` on macOS; or `~/.bashrc`) to make it persistent across sessions.

## CLI Usage

The basic syntax is `mdweaver <input> [options]`.

### Examples

**Convert a single file:**
```bash
mdweaver document.md
```

**Convert a directory (recursively), with defaults excluded:**
```bash
mdweaver ./docs
```

**Exclude additional paths (repeatable):**
```bash
mdweaver ./docs --exclude "**/dist/**" --exclude "**/build/**"
```

**Generate EPUB with metadata:**
```bash
mdweaver ./content -f epub -t "My Book" -a "Author Name"
```

**Generate PDF with a watermark:**
```bash
mdweaver ./content -f pdf -w "DRAFT" -o ./build
```

**Generate both formats:**
```bash
mdweaver ./content -f both
```

### Options

- `input`: Markdown file or directory to process.
- `-o, --output`: Output directory (default: `./output`).
- `-f, --format`: Output format: `pdf`, `epub`, or `both` (default: `pdf`).
- `-t, --title`: Document title (default: derived from filename/path).
- `-a, --author`: Author name (for EPUB metadata).
- `-w, --watermark`: Watermark text to display diagonally across PDF pages.
- `--exclude`: Glob pattern to exclude (repeatable), e.g. `--exclude "**/dist/**"`.

### Default excludes

When scanning directories recursively, `mdweaver` excludes these patterns by default:

- `**/.git/**`
- `**/.venv/**`
- `**/venv/**`
- `**/node_modules/**`
- `**/__pycache__/**`
- `**/.pytest_cache/**`
- `**/output/**`

You can add more exclusions using `--exclude`.

## Project Structure

```text
mdweaver/
├── src/mdweaver/
│   ├── __init__.py
│   └── generate_pdf.py   # Core logic
├── tests/
│   ├── conftest.py
│   └── test_mdweaver.py
├── pyproject.toml        # Dependencies and metadata
└── README.md
```

## Development

### Running Tests

```bash
uv run pytest
```

*Note: You might see a skipped test for PDF generation if the system dependencies (WeasyPrint libs) are not installed.*
