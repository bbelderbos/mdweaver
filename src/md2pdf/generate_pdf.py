#!/usr/bin/env python3
"""
Generate nicely formatted PDF and EPUB from markdown files.

Usage:
    python generate_pdf.py document.md
    python generate_pdf.py ./docs --format epub
    python generate_pdf.py ./content --format both
    ...
"""

import argparse
import datetime
import re
import sys
from pathlib import Path

import markdown
from ebooklib import epub
from pygments.formatters import HtmlFormatter
from weasyprint import HTML, CSS

# Attribution for PDF/EPUB copyright and author metadata
AUTHOR_ATTRIBUTION = "Jim Hodapp / Pybites"


def get_export_version() -> str:
    """Read export version from EXPORT_VERSION file."""
    version_file = Path(__file__).parent / "EXPORT_VERSION"
    if version_file.exists():
        return version_file.read_text().strip()
    return "0.0"


def preprocess_markdown(md_content: str) -> str:
    """Preprocess markdown to fix rendering issues.

    Fixes:
    1. Escape angle brackets in Rust generics (e.g., Result<T, E>) outside of
       code blocks/backticks so they render correctly instead of being stripped
       as HTML tags.
    2. Add blank line before bullet/numbered lists when missing, as markdown
       requires blank lines before lists for proper rendering.
    """
    lines = md_content.split("\n")
    in_code_block = False
    processed_lines = []

    for i, line in enumerate(lines):
        # Track fenced code blocks
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            processed_lines.append(line)
            continue

        if not in_code_block:
            # Fix 1: Escape < and > in Rust generics outside of backticks
            # Split line by backtick-delimited code spans and only process non-code parts
            result = []
            parts = re.split(r"(`[^`]+`)", line)
            for part in parts:
                if part.startswith("`") and part.endswith("`"):
                    # Inside backticks - keep as is
                    result.append(part)
                else:
                    # Outside backticks - escape angle brackets in type parameters
                    # Matches patterns like <T>, <T, E>, <String>, etc.
                    part = re.sub(r"<([A-Z][^>]*)>", r"&lt;\1&gt;", part)
                    result.append(part)
            line = "".join(result)

            # Fix 2: Add blank line before bullet/numbered lists if missing
            # Only add if previous line exists, is non-empty, and is not a list item or header
            if i > 0 and (line.startswith("- ") or re.match(r"^\d+\. ", line)):
                prev_line = processed_lines[-1] if processed_lines else ""
                if (
                    prev_line.strip()
                    and not prev_line.startswith("- ")
                    and not re.match(r"^\d+\. ", prev_line)
                    and not prev_line.startswith("#")
                ):
                    processed_lines.append("")

        processed_lines.append(line)

    return "\n".join(processed_lines)


def get_md_files(path: Path, recursive: bool = True) -> list[Path]:
    """Get all markdown files from a file or directory.

    Args:
        path: A markdown file or directory containing markdown files
        recursive: If True, search directories recursively

    Returns:
        List of markdown file paths, sorted by full path
    """
    if path.is_file():
        if path.suffix.lower() == ".md":
            return [path]
        return []

    pattern = "**/*.md" if recursive else "*.md"
    md_files = sorted(path.glob(pattern))
    return [f for f in md_files if f.is_file()]


def convert_md_to_html(md_content: str) -> str:
    """Convert markdown to HTML with syntax highlighting."""
    # Preprocess to fix angle brackets and list formatting
    md_content = preprocess_markdown(md_content)

    md = markdown.Markdown(
        extensions=[
            "fenced_code",
            "codehilite",
            "tables",
            "toc",
        ],
        extension_configs={
            "codehilite": {
                "css_class": "highlight",
                "guess_lang": False,
            }
        },
    )
    return md.convert(md_content)


def get_css_styles(version: str, watermark: str | None = None) -> str:
    """Generate CSS styles including Pygments syntax highlighting.

    Args:
        version: Version string to display in footer
        watermark: Optional watermark text to display diagonally across pages
    """
    # Get Pygments CSS for code highlighting (using a nice theme)
    pygments_css = HtmlFormatter(style="monokai").get_style_defs(".highlight")

    current_year = datetime.datetime.now().year

    # Build watermark CSS only if watermark text is provided
    watermark_css = ""
    if watermark:
        watermark_css = f"""
    /* Subtle diagonal watermark */
    body::before {{
        content: "{watermark}";
        position: fixed;
        top: 45%;
        left: 50%;
        transform: translate(-50%, -50%) rotate(-45deg);
        font-family: 'Helvetica', sans-serif;
        font-size: 60pt;
        color: rgba(0, 0, 0, 0.03);
        white-space: nowrap;
        pointer-events: none;
        z-index: -1;
    }}
    """

    return f"""
    @page {{
        size: A4;
        margin: 2cm;
        @bottom-left {{
            content: "(C) {current_year} {AUTHOR_ATTRIBUTION} | v{version}";
            font-family: 'Helvetica', sans-serif;
            font-size: 8pt;
            color: #999;
        }}
        @bottom-center {{
            content: counter(page);
            font-family: 'Helvetica', sans-serif;
            font-size: 10pt;
            color: #666;
        }}
        @bottom-right {{
            content: "Exclusive cohort materials - Please do not share";
            font-family: 'Helvetica', sans-serif;
            font-size: 8pt;
            color: #999;
        }}
    }}
    {watermark_css}

    body {{
        font-family: 'Georgia', 'Times New Roman', serif;
        font-size: 11pt;
        line-height: 1.6;
        color: #333;
        max-width: 100%;
    }}

    h1 {{
        font-family: 'Helvetica', 'Arial', sans-serif;
        font-size: 24pt;
        color: #2c3e50;
        border-bottom: 3px solid #3498db;
        padding-bottom: 10px;
        margin-top: 0;
        margin-bottom: 20px;
    }}

    h2 {{
        font-family: 'Helvetica', 'Arial', sans-serif;
        font-size: 18pt;
        color: #34495e;
        margin-top: 30px;
        margin-bottom: 15px;
        border-bottom: 1px solid #bdc3c7;
        padding-bottom: 5px;
    }}

    h3 {{
        font-family: 'Helvetica', 'Arial', sans-serif;
        font-size: 14pt;
        color: #7f8c8d;
        margin-top: 25px;
        margin-bottom: 10px;
    }}

    h4 {{
        font-family: 'Helvetica', 'Arial', sans-serif;
        font-size: 12pt;
        color: #95a5a6;
        margin-top: 20px;
        margin-bottom: 10px;
    }}

    p {{
        margin-bottom: 12px;
        text-align: justify;
    }}

    /* Inline code */
    code {{
        font-family: 'Menlo', 'Monaco', 'Consolas', monospace;
        font-size: 9.5pt;
        background-color: #f4f4f4;
        padding: 2px 6px;
        border-radius: 3px;
        color: #c0392b;
    }}

    /* Code blocks */
    .highlight {{
        background-color: #272822;
        border-radius: 6px;
        padding: 15px;
        margin: 15px 0;
        overflow-x: auto;
    }}

    .highlight pre {{
        margin: 0;
        padding: 0;
        background: transparent;
        font-family: 'Menlo', 'Monaco', 'Consolas', monospace;
        font-size: 9pt;
        line-height: 1.4;
        white-space: pre-wrap;
        word-wrap: break-word;
    }}

    .highlight code {{
        background: transparent;
        padding: 0;
        color: #f8f8f2;
        font-size: 9pt;
    }}

    /* Lists */
    ul, ol {{
        margin-bottom: 12px;
        padding-left: 25px;
    }}

    li {{
        margin-bottom: 6px;
    }}

    /* Nested lists */
    li > ul, li > ol {{
        margin-top: 6px;
        margin-bottom: 6px;
    }}

    /* Strong and emphasis */
    strong {{
        color: #2c3e50;
    }}

    em {{
        color: #555;
    }}

    /* Tables */
    table {{
        border-collapse: collapse;
        width: 100%;
        margin: 15px 0;
    }}

    th, td {{
        border: 1px solid #ddd;
        padding: 10px;
        text-align: left;
    }}

    th {{
        background-color: #3498db;
        color: white;
        font-family: 'Helvetica', 'Arial', sans-serif;
    }}

    tr:nth-child(even) {{
        background-color: #f9f9f9;
    }}

    /* Blockquotes */
    blockquote {{
        border-left: 4px solid #3498db;
        margin: 15px 0;
        padding: 10px 20px;
        background-color: #f9f9f9;
        font-style: italic;
        color: #555;
    }}

    /* Links */
    a {{
        color: #3498db;
        text-decoration: none;
    }}

    /* Page break for each lesson */
    .lesson {{
        page-break-before: always;
    }}

    .lesson:first-child {{
        page-break-before: avoid;
    }}

    /* Horizontal rules */
    hr {{
        border: none;
        border-top: 2px solid #eee;
        margin: 30px 0;
    }}

    /* Pygments syntax highlighting */
    {pygments_css}
    """


def get_epub_css() -> str:
    """Generate CSS styles for EPUB (simplified for e-readers)."""
    return """
    body {
        font-family: Georgia, serif;
        font-size: 1em;
        line-height: 1.6;
        color: #333;
    }

    h1 {
        font-size: 1.8em;
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 8px;
        margin-top: 0;
    }

    h2 {
        font-size: 1.4em;
        color: #34495e;
        margin-top: 1.5em;
        border-bottom: 1px solid #bdc3c7;
        padding-bottom: 4px;
    }

    h3 {
        font-size: 1.2em;
        color: #7f8c8d;
        margin-top: 1.2em;
    }

    code {
        font-family: monospace;
        font-size: 0.9em;
        background-color: #f4f4f4;
        padding: 2px 4px;
    }

    pre {
        background-color: #272822;
        color: #f8f8f2;
        padding: 12px;
        overflow-x: auto;
        font-size: 0.85em;
        line-height: 1.4;
        border-radius: 4px;
    }

    pre code {
        background: transparent;
        padding: 0;
        color: inherit;
    }

    blockquote {
        border-left: 3px solid #3498db;
        margin: 1em 0;
        padding: 0.5em 1em;
        background-color: #f9f9f9;
        font-style: italic;
    }

    table {
        border-collapse: collapse;
        width: 100%;
        margin: 1em 0;
    }

    th, td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
    }

    th {
        background-color: #3498db;
        color: white;
    }

    .copyright {
        margin-top: 2em;
        padding-top: 1em;
        border-top: 1px solid #eee;
        font-size: 0.8em;
        color: #999;
        text-align: center;
    }
    """


def generate_epub(input_path: Path, output_dir: Path, title: str | None = None) -> Path:
    """Generate EPUB from markdown file(s).

    Args:
        input_path: Path to a markdown file or directory containing markdown files
        output_dir: Directory to write the output file
        title: Optional title for the EPUB (defaults to input path name)
    """
    version = get_export_version()

    if not input_path.exists():
        print(f"Error: Path not found: {input_path}")
        sys.exit(1)

    md_files = get_md_files(input_path)

    if not md_files:
        print(f"Error: No markdown files found in {input_path}")
        sys.exit(1)

    # Derive name from input path
    name = input_path.stem if input_path.is_file() else input_path.name
    doc_title = title or name.replace("-", " ").replace("_", " ").title()

    print(f"Found {len(md_files)} markdown file(s) in {input_path} (v{version})")

    # Create EPUB book
    book = epub.EpubBook()

    # Set metadata
    book.set_identifier(f"md2pdf-{name}-v{version}")
    book.set_title(doc_title)
    book.set_language("en")
    book.add_author(AUTHOR_ATTRIBUTION)

    # Add CSS
    css = epub.EpubItem(
        uid="style",
        file_name="style/main.css",
        media_type="text/css",
        content=get_epub_css(),
    )
    book.add_item(css)

    # Copyright notice
    current_year = datetime.datetime.now().year
    copyright_html = f"""
    <div class="copyright">
        <p>&copy; {current_year} {AUTHOR_ATTRIBUTION} | v{version}</p>
        <p>Exclusive cohort materials - Please do not share</p>
    </div>
    """

    # Create chapters from markdown files
    chapters = []
    for i, md_file in enumerate(md_files):
        print(f"  Processing: {md_file.name}")

        md_content = md_file.read_text(encoding="utf-8")
        html_content = convert_md_to_html(md_content)

        # Extract title from first h1 or use filename
        title = md_file.stem.split("-", 1)[-1].replace("-", " ").title()
        h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", html_content)
        if h1_match:
            # Unescape HTML entities for cleaner TOC display
            title = h1_match.group(1).replace("&lt;", "<").replace("&gt;", ">")

        # Create chapter
        chapter = epub.EpubHtml(
            title=title,
            file_name=f"chapter_{i + 1:02d}.xhtml",
            lang="en",
        )
        chapter.content = f"<html><body>{html_content}{copyright_html}</body></html>"
        chapter.add_item(css)

        book.add_item(chapter)
        chapters.append(chapter)

    # Define table of contents and spine
    book.toc = chapters
    book.spine = ["nav"] + chapters

    # Add navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write EPUB file
    output_file = output_dir / f"{name}_v{version}.epub"
    print(f"\nGenerating EPUB: {output_file}")

    epub.write_epub(output_file, book)

    print(f"EPUB generated successfully: {output_file}")
    return output_file


def generate_pdf(
    input_path: Path,
    output_dir: Path,
    title: str | None = None,
    watermark: str | None = None,
) -> Path:
    """Generate PDF from markdown file(s).

    Args:
        input_path: Path to a markdown file or directory containing markdown files
        output_dir: Directory to write the output file
        title: Optional title for the PDF (defaults to input path name)
        watermark: Optional watermark text to display diagonally across pages
    """
    version = get_export_version()

    if not input_path.exists():
        print(f"Error: Path not found: {input_path}")
        sys.exit(1)

    md_files = get_md_files(input_path)

    if not md_files:
        print(f"Error: No markdown files found in {input_path}")
        sys.exit(1)

    # Derive name from input path
    name = input_path.stem if input_path.is_file() else input_path.name
    doc_title = title or name.replace("-", " ").replace("_", " ").title()

    print(f"Found {len(md_files)} markdown file(s) in {input_path} (v{version})")

    # Convert each markdown file to HTML
    html_sections = []
    for i, md_file in enumerate(md_files):
        print(f"  Processing: {md_file.name}")
        md_content = md_file.read_text(encoding="utf-8")
        html_content = convert_md_to_html(md_content)

        # Wrap in a div with lesson class for page breaks
        css_class = "lesson"
        html_sections.append(f'<div class="{css_class}">\n{html_content}\n</div>')

    # Combine all sections
    combined_html = "\n".join(html_sections)

    # Create full HTML document
    full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{doc_title}</title>
</head>
<body>
{combined_html}
</body>
</html>
"""

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate PDF
    output_file = output_dir / f"{name}_v{version}.pdf"
    print(f"\nGenerating PDF: {output_file}")

    css = CSS(string=get_css_styles(version, watermark))
    HTML(string=full_html).write_pdf(output_file, stylesheets=[css])

    print(f"PDF generated successfully: {output_file}")
    return output_file


def main():
    parser = argparse.ArgumentParser(
        description="Generate PDF and/or EPUB from markdown files"
    )
    parser.add_argument(
        "input",
        help="Markdown file or directory containing markdown files (searched recursively)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="output",
        help="Output directory (default: output)",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["pdf", "epub", "both"],
        default="pdf",
        help="Output format: pdf, epub, or both (default: pdf)",
    )
    parser.add_argument(
        "-t",
        "--title",
        help="Document title (default: derived from input path)",
    )
    parser.add_argument(
        "-w",
        "--watermark",
        help="Optional watermark text to display diagonally across PDF pages",
    )

    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_dir = Path(args.output)

    if args.format in ("pdf", "both"):
        generate_pdf(input_path, output_dir, args.title, args.watermark)

    if args.format in ("epub", "both"):
        generate_epub(input_path, output_dir, args.title)


if __name__ == "__main__":
    main()
