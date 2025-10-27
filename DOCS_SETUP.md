# MkDocs Documentation Setup

This document provides instructions for building and serving the Clearstone SDK documentation website.

## Prerequisites

The documentation dependencies are included in the dev requirements:

```bash
pip install -e ".[dev]"
```

This installs:
- `mkdocs>=1.5.0` - The static site generator
- `mkdocs-material>=9.0.0` - The Material theme

## Documentation Structure

```
docs/
├── index.md                    # Home page (from README.md)
├── guide/
│   ├── getting-started.md     # 5-minute quickstart
│   ├── writing-policies.md    # Policy writing guide
│   └── developer-toolkit.md   # Developer tools overview
├── api/
│   └── index.md               # Complete API reference
├── about/
│   ├── contributing.md        # Contributing guidelines
│   └── license.md             # MIT license
└── assets/
    ├── logo.svg               # Site logo
    └── favicon.ico            # Site favicon
```

## Building the Documentation

### Serve Locally (Development)

To preview the documentation with live-reload:

```bash
mkdocs serve
```

Then open http://127.0.0.1:8000 in your browser.

The site will automatically reload when you edit any Markdown files.

### Build Static Site

To build the static HTML site:

```bash
mkdocs build
```

This creates a `site/` directory with the complete static website.

## Features

The documentation site includes:

✅ **Material Design Theme** - Modern, responsive design  
✅ **Dark/Light Mode** - Toggle between themes  
✅ **Search** - Full-text search across all pages  
✅ **Code Highlighting** - Syntax highlighting with copy buttons  
✅ **Navigation** - Tabbed navigation with sections  
✅ **Mobile Responsive** - Works on all devices  
✅ **GitHub Integration** - Links to repository and edit pages  

## Deploying to GitHub Pages

To deploy the documentation to GitHub Pages:

1. Build the site:
```bash
mkdocs gh-deploy
```

This command will:
- Build the static site
- Create/update the `gh-pages` branch
- Push to GitHub
- Your site will be available at: `https://your-repo.github.io/clearstone-sdk/`

## Customization

### Updating the Theme

Edit `mkdocs.yml` to customize:
- Colors (`theme.palette`)
- Logo and favicon (`theme.logo`, `theme.favicon`)
- Navigation structure (`nav`)
- Features (`theme.features`)

### Adding Pages

1. Create a new Markdown file in the appropriate directory
2. Add it to the `nav` section in `mkdocs.yml`

Example:
```yaml
nav:
  - 'Home': 'index.md'
  - 'User Guide':
    - 'Getting Started': 'guide/getting-started.md'
    - 'Your New Page': 'guide/new-page.md'  # Add this
```

### Updating Content

Simply edit the Markdown files in the `docs/` directory. The syntax is standard Markdown with some extensions:

- **Code blocks with highlighting**: ` ```python `
- **Admonitions (notes/warnings)**: `!!! note` or `!!! warning`
- **Tables of contents**: Automatically generated
- **Code annotations**: Inline comments in code blocks

## Markdown Extensions

The following extensions are enabled:

- `pymdownx.highlight` - Syntax highlighting
- `pymdownx.inlinehilite` - Inline code highlighting
- `pymdownx.snippets` - Include file snippets
- `pymdownx.superfences` - Advanced code blocks
- `admonition` - Note/warning boxes
- `toc` - Table of contents with permalinks

## Troubleshooting

### Port Already in Use

If port 8000 is already in use:

```bash
mkdocs serve --dev-addr=127.0.0.1:8001
```

### Build Errors

Check that all files referenced in `mkdocs.yml` exist:

```bash
find docs -name "*.md" | sort
```

### Missing Dependencies

Reinstall the dev dependencies:

```bash
pip install -e ".[dev]" --force-reinstall
```

## Next Steps

1. Customize the logo and favicon in `docs/assets/`
2. Update the repository URLs in `mkdocs.yml`
3. Add more content to the guide pages
4. Deploy to GitHub Pages with `mkdocs gh-deploy`

For more information, see:
- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)

