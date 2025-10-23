#!/bin/bash

# Example script to demonstrate the newsletter generator

echo "========================================="
echo "Web Scraping Newsletter Generator Demo"
echo "========================================="
echo ""

# Install dependencies
echo "Step 1: Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "Step 2: Running scraper with example URLs..."
echo ""

# Run the scraper with some example URLs
python main.py \
  -f html \
  -o output \
  https://example.com \
  https://httpbin.org/html

echo ""
echo "========================================="
echo "Done! Check the 'output' directory for your newsletter."
echo "========================================="
