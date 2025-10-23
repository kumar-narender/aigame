#!/usr/bin/env python3
"""
Example usage of the Web Scraping and Newsletter Generator library.
This demonstrates how to use the library programmatically.
"""

import asyncio
from src.agents import ScraperAgent
from src.newsletter import NewsletterGenerator


async def example_basic():
    """Basic example: scrape and generate HTML newsletter"""
    print("=" * 80)
    print("Example 1: Basic HTML Newsletter")
    print("=" * 80)
    print()

    # Initialize the scraper agent
    scraper = ScraperAgent(config={
        "timeout": 30,
        "max_retries": 3
    })

    # URLs to scrape
    urls = [
        "https://example.com",
        "https://httpbin.org/html"
    ]

    print(f"Scraping {len(urls)} URLs...")
    scraped_data = await scraper.execute(urls)
    print(f"Scraped {len(scraped_data)} items")
    print()

    # Generate HTML newsletter
    generator = NewsletterGenerator(config={
        "template_style": "html",
        "max_items": 10
    })

    newsletter = generator.generate(
        scraped_data,
        title="My First Newsletter",
        subtitle="Generated with Python!"
    )

    # Save to file
    generator.save_to_file(newsletter, "output/example_basic.html")
    print("Newsletter saved to: output/example_basic.html")
    print()


async def example_markdown():
    """Example: generate Markdown newsletter"""
    print("=" * 80)
    print("Example 2: Markdown Newsletter")
    print("=" * 80)
    print()

    scraper = ScraperAgent()

    urls = ["https://example.com"]

    scraped_data = await scraper.execute(urls)

    # Generate Markdown newsletter
    generator = NewsletterGenerator(config={
        "template_style": "markdown"
    })

    newsletter = generator.generate(
        scraped_data,
        title="Tech News",
        subtitle="Weekly Digest"
    )

    generator.save_to_file(newsletter, "output/example_markdown.md")
    print("Markdown newsletter saved to: output/example_markdown.md")
    print()


async def example_multiple_formats():
    """Example: generate newsletter in all formats"""
    print("=" * 80)
    print("Example 3: Generate Multiple Formats")
    print("=" * 80)
    print()

    scraper = ScraperAgent()
    urls = ["https://example.com"]

    print("Scraping URLs...")
    scraped_data = await scraper.execute(urls)
    print()

    formats = {
        "html": "output/example_all.html",
        "markdown": "output/example_all.md",
        "text": "output/example_all.txt"
    }

    for format_type, filename in formats.items():
        generator = NewsletterGenerator(config={
            "template_style": format_type
        })

        newsletter = generator.generate(
            scraped_data,
            title="Multi-Format Newsletter"
        )

        generator.save_to_file(newsletter, filename)
        print(f"{format_type.upper()} newsletter saved to: {filename}")

    print()


async def main():
    """Run all examples"""
    import os
    os.makedirs("output", exist_ok=True)

    await example_basic()
    await example_markdown()
    await example_multiple_formats()

    print("=" * 80)
    print("All examples completed! Check the 'output' directory.")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
