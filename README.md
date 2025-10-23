# Web Scraping & Newsletter Generator

A Python-based application with intelligent agents that scrape websites and automatically generate beautiful newsletters from the collected content.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run a simple example
python main.py https://example.com

# 3. Or try the interactive examples
python example_usage.py
```

Your newsletter will be saved in the `output/` directory!

## Features

- **Asynchronous Web Scraping**: Fast, concurrent scraping of multiple URLs
- **Smart Content Extraction**: Automatically extracts titles, descriptions, and main content
- **Multiple Output Formats**: Generate newsletters in HTML, Markdown, or plain text
- **Agent-Based Architecture**: Modular design with specialized agents for different tasks
- **Configurable**: Easy configuration through JSON files or programmatic API
- **Robust Error Handling**: Retry logic and graceful error handling

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd aigame
```

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Scrape websites and generate an HTML newsletter:

```bash
python main.py https://example.com https://another-site.com
```

### Specify Output Format

Generate a Markdown newsletter:

```bash
python main.py -f markdown https://example.com https://another-site.com
```

Generate a plain text newsletter:

```bash
python main.py -f text https://example.com https://another-site.com
```

### Specify Output Directory

```bash
python main.py -o my_newsletters https://example.com
```

### Full Example

```bash
python main.py \
  -f html \
  -o newsletters \
  https://techcrunch.com \
  https://news.ycombinator.com \
  https://dev.to
```

## Project Structure

```
aigame/
├── src/
│   ├── __init__.py
│   ├── agents/              # Agent modules
│   │   ├── __init__.py
│   │   ├── base_agent.py    # Base agent class
│   │   └── scraper.py       # Web scraping agent
│   ├── newsletter/          # Newsletter generation
│   │   ├── __init__.py
│   │   └── generator.py     # Newsletter generator
│   └── utils/               # Utility modules
│       ├── __init__.py
│       └── config.py        # Configuration management
├── main.py                  # Main entry point
├── requirements.txt         # Python dependencies
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Architecture

### Agents

The application uses an agent-based architecture:

- **BaseAgent**: Abstract base class for all agents
- **ScraperAgent**: Responsible for scraping web content
  - Concurrent URL processing
  - Retry logic with exponential backoff
  - Content parsing with BeautifulSoup

### Newsletter Generator

The `NewsletterGenerator` class supports multiple output formats:

- **HTML**: Beautiful, responsive HTML newsletters
- **Markdown**: Clean, readable Markdown format
- **Text**: Plain text for maximum compatibility

### Configuration

The `Config` class manages application settings:

```python
from src.utils import Config

config = Config()
config.set('scraper.timeout', 60)
config.set('newsletter.max_items', 20)
```

## Programmatic Usage

You can also use the library programmatically:

```python
import asyncio
from src.agents import ScraperAgent
from src.newsletter import NewsletterGenerator

async def create_newsletter():
    # Initialize scraper
    scraper = ScraperAgent(config={
        "timeout": 30,
        "max_retries": 3
    })

    # Scrape URLs
    urls = ["https://example.com", "https://another-site.com"]
    scraped_data = await scraper.execute(urls)

    # Generate newsletter
    generator = NewsletterGenerator(config={
        "template_style": "html",
        "max_items": 10
    })

    newsletter = generator.generate(
        scraped_data,
        title="My Newsletter",
        subtitle="Latest updates"
    )

    # Save to file
    generator.save_to_file(newsletter, "my_newsletter.html")

asyncio.run(create_newsletter())
```

## Configuration File

You can create a `config.json` file to customize behavior:

```json
{
  "scraper": {
    "timeout": 30,
    "max_retries": 3,
    "user_agent": "Mozilla/5.0 (compatible; NewsletterBot/1.0)"
  },
  "newsletter": {
    "template_style": "html",
    "max_items": 10,
    "include_images": false
  },
  "output": {
    "directory": "output",
    "filename_template": "newsletter_{date}.{ext}"
  }
}
```

## Dependencies

- **aiohttp**: Async HTTP client for web scraping
- **beautifulsoup4**: HTML parsing and content extraction
- **lxml**: Fast XML and HTML parser

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License

## Future Enhancements

- [ ] Image extraction and inclusion in newsletters
- [ ] AI-powered content summarization
- [ ] Email delivery integration
- [ ] RSS feed support
- [ ] Custom CSS templates
- [ ] Content filtering and categorization
- [ ] Scheduled scraping
- [ ] Web UI for configuration
