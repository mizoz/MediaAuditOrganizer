# BUILD_REPORT.pdf Conversion Instructions

The comprehensive build report (`BUILD_REPORT.md`) can be converted to PDF using one of the following methods:

## Option 1: WeasyPrint (Recommended)

```bash
# Navigate to project directory
cd /home/az/.openclaw/workspace/AZ_Projects/MediaAuditOrganizer

# Create virtual environment and install WeasyPrint
python3 -m venv .venv
source .venv/bin/activate
pip install WeasyPrint==62.2

# Convert to PDF
weasyprint BUILD_REPORT.md BUILD_REPORT.pdf

# Expected output: ~40-50 page PDF
```

**Note:** WeasyPrint requires system dependencies (Pango, Cairo). If installation fails:
- **Mac:** `brew install pango cairo glib`
- **Linux:** `sudo apt install libpango-1.0-0 libcairo2 libglib2.0-0`

## Option 2: Pandoc + xelatex

```bash
# Install xelatex (LaTeX)
# Mac: brew install mactex-no-gui
# Linux: sudo apt install texlive-xetex

# Convert to PDF
pandoc BUILD_REPORT.md -o BUILD_REPORT.pdf --pdf-engine=xelatex
```

## Option 3: Browser Print to PDF

1. Convert Markdown to HTML first:
   ```bash
   # Using pandoc
   pandoc BUILD_REPORT.md -o BUILD_REPORT.html
   ```

2. Open `BUILD_REPORT.html` in Chrome/Firefox/Safari

3. Press `Ctrl+P` (or `Cmd+P` on Mac)

4. Select "Save as PDF" as destination

5. Click Save

## Option 4: Use Online Converter

Upload `BUILD_REPORT.md` to:
- https://pandoc.org/try/
- https://markdowntopdf.com/
- https://www.markdown.topdf.com/

## Expected PDF Specifications

- **Pages:** 40-50 pages
- **File Size:** ~2-5 MB
- **Format:** A4 or Letter (depending on converter)
- **Fonts:** System defaults (sans-serif recommended)

---

**Quick Command (if WeasyPrint already installed):**
```bash
weasyprint BUILD_REPORT.md BUILD_REPORT.pdf
```
