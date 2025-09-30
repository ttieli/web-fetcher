#!/usr/bin/env python3
"""Debug ContentFilter issue with React.dev"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium_fetcher import SeleniumFetcher
from bs4 import BeautifulSoup
from webfetcher import ContentFilter

# Get HTML
fetcher = SeleniumFetcher()
fetcher.connect_to_chrome()
html, _ = fetcher.fetch_html_selenium('https://react.dev/')
fetcher.cleanup()

# Create soup
soup = BeautifulSoup(html, 'html.parser')

# Check before filtering
main_before = soup.find('main')
article_before = soup.find('article')

print("BEFORE FILTERING:")
print(f"  Main tag exists: {main_before is not None}")
print(f"  Article tag exists: {article_before is not None}")

if main_before:
    # Check if main has any children that might be removed
    children_count = len(list(main_before.children))
    print(f"  Main has {children_count} children")

# Apply safe filter step by step
filter = ContentFilter('safe')

# Step 1: Remove scripts and styles
filter._remove_scripts_and_styles(soup)
main_after_scripts = soup.find('main')
print("\nAfter removing scripts/styles:")
print(f"  Main still exists: {main_after_scripts is not None}")

# Step 2: Remove hidden elements
filter._remove_hidden_elements(soup)
main_after_hidden = soup.find('main')
print("\nAfter removing hidden elements:")
print(f"  Main still exists: {main_after_hidden is not None}")

# Step 3: Remove ads
filter._remove_ads_and_popups(soup)
main_after_ads = soup.find('main')
print("\nAfter removing ads/popups:")
print(f"  Main still exists: {main_after_ads is not None}")

# Check article too
article_final = soup.find('article')
print(f"  Article still exists: {article_final is not None}")

# If they're gone, find out why
if not main_after_ads:
    print("\n⚠️  MAIN TAG WAS REMOVED!")
    print("Checking removed elements around the time it disappeared...")
    for elem in filter.removed_elements[-10:]:
        print(f"  - {elem}")

# Check if it's a cascading effect
print("\nChecking for cascading removal (parent removed)...")
body = soup.find('body')
if body:
    # Try to find any remaining major containers
    divs_with_id = soup.find_all('div', id=True)
    print(f"Divs with ID remaining: {len(divs_with_id)}")
    if len(divs_with_id) < 5:
        print("Very few divs with IDs remain - possible over-filtering!")