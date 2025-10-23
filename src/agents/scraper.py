"""Web Scraper Agent for extracting content from websites"""

import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from .base_agent import BaseAgent


class ScraperAgent(BaseAgent):
    """
    Agent responsible for scraping content from websites.
    """

    def __init__(self, name: str = "ScraperAgent", config: Dict[str, Any] = None):
        """
        Initialize the scraper agent.

        Args:
            name: Name of the agent
            config: Configuration dictionary containing:
                - timeout: Request timeout in seconds (default: 30)
                - max_retries: Maximum number of retries (default: 3)
                - user_agent: User agent string to use
        """
        super().__init__(name, config)
        self.timeout = self.config.get("timeout", 30)
        self.max_retries = self.config.get("max_retries", 3)
        self.user_agent = self.config.get(
            "user_agent",
            "Mozilla/5.0 (compatible; NewsletterBot/1.0)"
        )

    async def execute(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        Execute scraping on multiple URLs.

        Args:
            urls: List of URLs to scrape

        Returns:
            List of dictionaries containing scraped data
        """
        self.status = "running"
        results = []

        async with aiohttp.ClientSession() as session:
            tasks = [self._scrape_url(session, url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        self.status = "completed"
        return [r for r in results if not isinstance(r, Exception)]

    async def _scrape_url(
        self,
        session: aiohttp.ClientSession,
        url: str
    ) -> Dict[str, Any]:
        """
        Scrape a single URL.

        Args:
            session: aiohttp session
            url: URL to scrape

        Returns:
            Dictionary containing scraped data
        """
        headers = {"User-Agent": self.user_agent}

        for attempt in range(self.max_retries):
            try:
                async with session.get(
                    url,
                    headers=headers,
                    timeout=self.timeout
                ) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self._parse_content(url, html)
                    else:
                        print(f"Failed to fetch {url}: Status {response.status}")

            except Exception as e:
                print(f"Error scraping {url} (attempt {attempt + 1}): {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

        return {"url": url, "error": "Failed to scrape after retries"}

    def _parse_content(self, url: str, html: str) -> Dict[str, Any]:
        """
        Parse HTML content and extract relevant information.

        Args:
            url: Source URL
            html: HTML content

        Returns:
            Dictionary containing parsed data
        """
        soup = BeautifulSoup(html, 'html.parser')

        # Extract title
        title = soup.find('title')
        title_text = title.get_text().strip() if title else "No title"

        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc.get('content', '') if meta_desc else ''

        # Extract main content (this is a simple heuristic)
        # Remove script and style elements
        for script in soup(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()

        # Get text content
        text = soup.get_text(separator=' ', strip=True)

        # Extract headings
        headings = [h.get_text().strip() for h in soup.find_all(['h1', 'h2', 'h3'])]

        # Extract links
        links = [a.get('href') for a in soup.find_all('a', href=True)]

        return {
            "url": url,
            "title": title_text,
            "description": description,
            "content": text[:5000],  # Limit content length
            "headings": headings[:10],  # Limit number of headings
            "links": links[:20],  # Limit number of links
            "success": True
        }
