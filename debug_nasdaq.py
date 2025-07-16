#!/usr/bin/env python3
"""
Debug script to examine NASDAQ earnings page content
"""

import requests
from bs4 import BeautifulSoup

def debug_nasdaq_page(symbol):
    url = f"https://www.nasdaq.com/market-activity/stocks/{symbol.lower()}/earnings"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    }
    
    print(f"🌐 Fetching: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            # Save raw HTML for inspection
            debug_file = f"debug_{symbol}_earnings.html"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"💾 Saved HTML to: {debug_file}")
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for tables
            tables = soup.find_all('table')
            print(f"📋 Found {len(tables)} tables")
            
            # Look for earnings-related content
            earnings_keywords = ['earnings', 'eps', 'estimate', 'actual', 'surprise']
            
            for keyword in earnings_keywords:
                elements = soup.find_all(text=lambda text: text and keyword.lower() in text.lower())
                print(f"🔍 Found {len(elements)} elements containing '{keyword}'")
            
            # Look for specific table classes
            for i, table in enumerate(tables):
                print(f"\n📊 Table {i+1}:")
                if table.get('class'):
                    print(f"  Classes: {table.get('class')}")
                
                rows = table.find_all('tr')
                print(f"  Rows: {len(rows)}")
                
                if rows:
                    # Show first row (headers)
                    first_row = rows[0]
                    headers = [cell.get_text().strip() for cell in first_row.find_all(['th', 'td'])]
                    print(f"  Headers: {headers}")
            
            # Look for JSON data (often embedded in scripts)
            scripts = soup.find_all('script')
            print(f"\n📜 Found {len(scripts)} script tags")
            
            for i, script in enumerate(scripts):
                if script.string and ('earnings' in script.string.lower() or 'eps' in script.string.lower()):
                    print(f"🎯 Script {i+1} contains earnings data (length: {len(script.string)} chars)")
                    # Save interesting scripts
                    script_file = f"debug_{symbol}_script_{i}.js"
                    with open(script_file, 'w', encoding='utf-8') as f:
                        f.write(script.string)
                    print(f"💾 Saved script to: {script_file}")
                    
        else:
            print(f"❌ Failed to fetch page: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import sys
    symbol = sys.argv[1].upper() if len(sys.argv) > 1 else 'MSFT'
    debug_nasdaq_page(symbol)