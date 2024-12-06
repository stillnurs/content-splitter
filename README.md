# Content Splitter

A Python utility to split long contents into smaller fragments while preserving HTML structure or text formatting.

## Features

- Splits HTML content while maintaining tag hierarchy
- Splits plain text content at sentence boundaries
- Preserves Unicode characters and emojis
- Configurable maximum fragment size
- Command-line interface support
- Handles both HTML and plain text automatically

## Installation

### Using Poetry (Recommended)

#### Install Poetry

##### Linux/MacOS

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

##### Windows

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

#### PIPX

```bash
pip install pipx
pipx install poetry
```

#### Install Content Splitter

```bash
git clone
cd content-splitter
poetry install
```

### Using Pip

```bash
pip install content-splitter
```

## Usage

### Command Line

```bash
# Split a file with default max length (4096 chars)
poetry run split_msg input_file.txt

# Split with custom maximum length
poetry run split_msg --max-len 1000 input_file.html

# Read from stdin
echo "Your text here" | poetry run split_msg
```

### As a Python Module

```python
from content_splitter import split_content

# Split HTML content
html_content = "<div><p>Your long HTML content here...</p></div>"
fragments = split_content(html_content, max_length=1000)
for fragment in fragments:
    print(fragment)

# Split plain text
text_content = "Your long text content here..."
fragments = split_content(text_content, max_length=1000)
for fragment in fragments:
    print(fragment)
```

## Development

### Running Tests

```bash
poetry run pytest
```

## Requirements

- Python 3.13+
- beautifulsoup4 (for HTML parsing)
- click (for command-line interface)
- Poetry (for development)
- pytest (for running tests)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) - For HTML parsing
- [Click](https://click.palletsprojects.com/en/8.0.x/) - For command-line interface
- [Poetry](https://python-poetry.org/) - For dependency management
- [Pytest](https://docs.pytest.org/en/6.2.x/) - For testing

## Author

[Stillnurs](github.com/stillnurs)
