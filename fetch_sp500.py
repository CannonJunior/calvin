#!/usr/bin/env python3
"""
Fetch S&P 500 companies data from Wikipedia and save to JSON
"""

import requests
import pandas as pd
import json
from datetime import datetime


def fetch_sp500_from_wikipedia():
    """Fetch S&P 500 companies list from Wikipedia"""
    
    # Wikipedia URL for S&P 500 companies list
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    
    try:
        # Read HTML tables from Wikipedia
        tables = pd.read_html(url)
        
        # The first table contains the current S&P 500 companies
        sp500_table = tables[0]
        
        # Clean and standardize column names
        sp500_table.columns = sp500_table.columns.str.strip()
        
        print(f"Found {len(sp500_table)} S&P 500 companies")
        print("Columns:", list(sp500_table.columns))
        
        # Convert to list of dictionaries
        companies_data = []
        
        for _, row in sp500_table.iterrows():
            company_data = {
                'symbol': str(row.get('Symbol', '')).strip(),
                'company_name': str(row.get('Security', '')).strip(),
                'gics_sector': str(row.get('GICS Sector', '')).strip(),
                'gics_sub_industry': str(row.get('GICS Sub-Industry', '')).strip(),
                'headquarters': str(row.get('Headquarters Location', '')).strip(),
                'date_added': str(row.get('Date added', '')).strip(),
                'cik': str(row.get('CIK', '')).strip(),
                'founded': str(row.get('Founded', '')).strip() if 'Founded' in row else '',
                'last_updated': datetime.now().isoformat()
            }
            companies_data.append(company_data)
        
        return companies_data
        
    except Exception as e:
        print(f"Error fetching data from Wikipedia: {e}")
        return None


def save_to_json(data, filename='sp500_companies.json'):
    """Save company data to JSON file"""
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully saved {len(data)} companies to {filename}")
        return True
        
    except Exception as e:
        print(f"Error saving to JSON: {e}")
        return False


def main():
    """Main function to fetch and save S&P 500 data"""
    
    print("Fetching S&P 500 companies from Wikipedia...")
    
    # Fetch data from Wikipedia
    companies_data = fetch_sp500_from_wikipedia()
    
    if companies_data is None:
        print("Failed to fetch company data")
        return
    
    # Save to JSON file
    if save_to_json(companies_data):
        print("✅ S&P 500 data successfully fetched and saved!")
        
        # Print some sample data
        print("\nSample companies:")
        for i, company in enumerate(companies_data[:5]):
            print(f"{i+1}. {company['symbol']} - {company['company_name']} ({company['gics_sector']})")
        
        print(f"\nTotal companies: {len(companies_data)}")
        
        # Count by sector
        sectors = {}
        for company in companies_data:
            sector = company['gics_sector']
            sectors[sector] = sectors.get(sector, 0) + 1
        
        print("\nCompanies by sector:")
        for sector, count in sorted(sectors.items()):
            print(f"  {sector}: {count} companies")
    
    else:
        print("❌ Failed to save company data")


if __name__ == "__main__":
    main()