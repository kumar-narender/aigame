#!/usr/bin/env python3
"""
Main entry point for the Web Scraping and Newsletter Generation Application.
"""

import asyncio
import argparse
import os
from datetime import datetime
from typing import List

from src.agents import ScraperAgent
from src.newsletter import NewsletterGenerator
from src.utils import Config


async def main(urls: List[str], output_format: str = "html", output_dir: str = "output"):
    """
    Main application logic.

    Args:
        urls: List of URLs to scrape
        output_format: Output format (html, markdown, text)
        output_dir: Output directory for generated newsletters
    """
    print("=" * 80)
    print("Web Scraping and Newsletter Generation Application".center(80))
    print("=" * 80)
    print()

    # Load configuration
    config = Config()
    print(f"Configuration loaded: {config}")
    print()

    # Initialize scraper agent
    print("Initializing Scraper Agent...")
    scraper_config = config.get_scraper_config()
    scraper = ScraperAgent(config=scraper_config)
    print(f"Scraper Agent initialized: {scraper}")
    print()

    # Scrape URLs
    print(f"Starting to scrape {len(urls)} URLs...")
    print("-" * 80)
    for idx, url in enumerate(urls, 1):
        print(f"{idx}. {url}")
    print("-" * 80)
    print()

    scraped_data = await scraper.execute(urls)

    successful_scrapes = sum(1 for item in scraped_data if item.get("success", False))
    print(f"Scraping completed: {successful_scrapes}/{len(urls)} successful")
    print()

    # Generate newsletter
    print("Generating newsletter...")
    newsletter_config = config.get_newsletter_config()
    newsletter_config["template_style"] = output_format

    generator = NewsletterGenerator(config=newsletter_config)

    newsletter_title = "Weekly Tech Newsletter"
    newsletter_subtitle = f"Curated content from {len(urls)} sources - {datetime.now().strftime('%B %d, %Y')}"

    newsletter_content = generator.generate(
        scraped_data,
        title=newsletter_title,
        subtitle=newsletter_subtitle
    )
    print("Newsletter generated successfully!")
    print()

    # Save newsletter
    os.makedirs(output_dir, exist_ok=True)

    # Determine file extension
    ext_map = {"html": "html", "markdown": "md", "text": "txt"}
    extension = ext_map.get(output_format, "html")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"newsletter_{timestamp}.{extension}")

    generator.save_to_file(newsletter_content, output_file)
    print(f"Newsletter saved to: {output_file}")
    print()

    print("=" * 80)
    print("Application completed successfully!".center(80))
    print("=" * 80)


def parse_arguments():
    """
    Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Web Scraping and Newsletter Generation Application"
    )

    parser.add_argument(
        "urls",
        nargs="+",
        help="URLs to scrape"
    )

    parser.add_argument(
        "-f", "--format",
        choices=["html", "markdown", "text"],
        default="html",
        help="Output format for the newsletter (default: html)"
    )

    parser.add_argument(
        "-o", "--output",
        default="output",
        help="Output directory for generated newsletters (default: output)"
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    asyncio.run(main(args.urls, args.format, args.output))
