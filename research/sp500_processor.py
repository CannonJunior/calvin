#!/usr/bin/env python3
"""
S&P 500 Processor

Handles loading and processing S&P 500 company data for batch operations.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SP500Processor:
    """Processor for S&P 500 company data"""
    
    def __init__(self, sp500_file: str = "sp500_companies.json"):
        self.sp500_file = Path(sp500_file)
        self._companies_cache = None
        self._companies_by_symbol = None
    
    def load_sp500_companies(self) -> List[Dict[str, Any]]:
        """Load S&P 500 companies from JSON file"""
        if self._companies_cache is not None:
            return self._companies_cache
        
        try:
            if not self.sp500_file.exists():
                logger.warning(f"S&P 500 file not found: {self.sp500_file}")
                return []
            
            with open(self.sp500_file, 'r') as f:
                companies = json.load(f)
            
            self._companies_cache = companies
            
            # Create symbol lookup dictionary
            self._companies_by_symbol = {
                company['symbol']: company for company in companies
            }
            
            logger.info(f"Loaded {len(companies)} S&P 500 companies")
            return companies
            
        except Exception as e:
            logger.error(f"Error loading S&P 500 companies: {e}")
            return []
    
    def get_company_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get company information for a specific symbol"""
        if self._companies_by_symbol is None:
            self.load_sp500_companies()
        
        if self._companies_by_symbol is None:
            return None
        
        return self._companies_by_symbol.get(symbol.upper())
    
    def get_symbols_by_sector(self, sector: str) -> List[str]:
        """Get all symbols in a specific sector"""
        companies = self.load_sp500_companies()
        
        matching_symbols = []
        for company in companies:
            if company.get('gics_sector', '').lower() == sector.lower():
                matching_symbols.append(company['symbol'])
        
        return matching_symbols
    
    def get_symbols_by_industry(self, industry: str) -> List[str]:
        """Get all symbols in a specific industry"""
        companies = self.load_sp500_companies()
        
        matching_symbols = []
        for company in companies:
            if company.get('gics_sub_industry', '').lower() == industry.lower():
                matching_symbols.append(company['symbol'])
        
        return matching_symbols
    
    def get_all_symbols(self) -> List[str]:
        """Get all S&P 500 symbols"""
        companies = self.load_sp500_companies()
        return [company['symbol'] for company in companies]
    
    def get_sectors(self) -> List[str]:
        """Get all unique sectors"""
        companies = self.load_sp500_companies()
        sectors = set()
        
        for company in companies:
            sector = company.get('gics_sector')
            if sector:
                sectors.add(sector)
        
        return sorted(list(sectors))
    
    def get_industries(self) -> List[str]:
        """Get all unique industries"""
        companies = self.load_sp500_companies()
        industries = set()
        
        for company in companies:
            industry = company.get('gics_sub_industry')
            if industry:
                industries.add(industry)
        
        return sorted(list(industries))
    
    def validate_symbol(self, symbol: str) -> bool:
        """Check if a symbol is in the S&P 500"""
        if self._companies_by_symbol is None:
            self.load_sp500_companies()
        
        if self._companies_by_symbol is None:
            return False
        
        return symbol.upper() in self._companies_by_symbol
    
    def get_company_summary(self) -> Dict[str, Any]:
        """Get summary statistics about S&P 500 companies"""
        companies = self.load_sp500_companies()
        
        if not companies:
            return {}
        
        # Count by sector
        sectors = {}
        industries = {}
        
        for company in companies:
            sector = company.get('gics_sector', 'Unknown')
            industry = company.get('gics_sub_industry', 'Unknown')
            
            sectors[sector] = sectors.get(sector, 0) + 1
            industries[industry] = industries.get(industry, 0) + 1
        
        return {
            'total_companies': len(companies),
            'sectors': dict(sorted(sectors.items())),
            'industries': dict(sorted(industries.items())),
            'top_sectors': sorted(sectors.items(), key=lambda x: x[1], reverse=True)[:5],
            'top_industries': sorted(industries.items(), key=lambda x: x[1], reverse=True)[:10]
        }
    
    def create_sample_sp500_file(self):
        """Create a sample S&P 500 file if none exists"""
        if self.sp500_file.exists():
            logger.info(f"S&P 500 file already exists: {self.sp500_file}")
            return
        
        # Sample S&P 500 companies for testing
        sample_companies = [
            {
                "symbol": "AAPL",
                "company_name": "Apple Inc.",
                "gics_sector": "Information Technology",
                "gics_sub_industry": "Technology Hardware, Storage & Peripherals",
                "headquarters": "Cupertino, California",
                "date_added": "1982-12-12",
                "cik": "320193",
                "founded": "1976",
                "last_updated": "2025-07-19T00:00:00.000000"
            },
            {
                "symbol": "MSFT",
                "company_name": "Microsoft Corporation",
                "gics_sector": "Information Technology",
                "gics_sub_industry": "Systems Software",
                "headquarters": "Redmond, Washington",
                "date_added": "1994-02-28",
                "cik": "789019",
                "founded": "1975",
                "last_updated": "2025-07-19T00:00:00.000000"
            },
            {
                "symbol": "GOOGL",
                "company_name": "Alphabet Inc.",
                "gics_sector": "Communication Services",
                "gics_sub_industry": "Interactive Media & Services",
                "headquarters": "Mountain View, California",
                "date_added": "2006-04-03",
                "cik": "1652044",
                "founded": "1998",
                "last_updated": "2025-07-19T00:00:00.000000"
            },
            {
                "symbol": "AMZN",
                "company_name": "Amazon.com Inc.",
                "gics_sector": "Consumer Discretionary",
                "gics_sub_industry": "Internet & Direct Marketing Retail",
                "headquarters": "Seattle, Washington",
                "date_added": "2005-11-04",
                "cik": "1018724",
                "founded": "1994",
                "last_updated": "2025-07-19T00:00:00.000000"
            },
            {
                "symbol": "TSLA",
                "company_name": "Tesla Inc.",
                "gics_sector": "Consumer Discretionary",
                "gics_sub_industry": "Automobile Manufacturers",
                "headquarters": "Austin, Texas",
                "date_added": "2020-12-21",
                "cik": "1318605",
                "founded": "2003",
                "last_updated": "2025-07-19T00:00:00.000000"
            }
        ]
        
        try:
            with open(self.sp500_file, 'w') as f:
                json.dump(sample_companies, f, indent=2)
            
            logger.info(f"Created sample S&P 500 file: {self.sp500_file}")
            
        except Exception as e:
            logger.error(f"Error creating sample S&P 500 file: {e}")


def main():
    """Test the SP500Processor"""
    processor = SP500Processor()
    
    # Create sample file if needed
    processor.create_sample_sp500_file()
    
    # Test loading companies
    companies = processor.load_sp500_companies()
    print(f"Loaded {len(companies)} companies")
    
    if companies:
        # Test getting company info
        test_symbol = companies[0]['symbol']
        company_info = processor.get_company_info(test_symbol)
        print(f"\nCompany info for {test_symbol}:")
        print(f"Name: {company_info.get('company_name')}")
        print(f"Sector: {company_info.get('gics_sector')}")
        
        # Test getting symbols by sector
        sectors = processor.get_sectors()
        print(f"\nSectors: {sectors}")
        
        if sectors:
            first_sector = sectors[0]
            sector_symbols = processor.get_symbols_by_sector(first_sector)
            print(f"Symbols in {first_sector}: {sector_symbols}")
        
        # Test summary
        summary = processor.get_company_summary()
        print(f"\nSummary:")
        print(f"Total companies: {summary.get('total_companies')}")
        print(f"Top sectors: {summary.get('top_sectors')}")


if __name__ == "__main__":
    main()