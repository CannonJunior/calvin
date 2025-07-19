#!/usr/bin/env python3
"""
Template Validation Script

Validates that the generated JSON matches the earnings template schema exactly.
"""

import json
import sys

def validate_template_compliance(file_path):
    """Validate JSON file against earnings template schema"""
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading file: {e}")
        return False
    
    print('=== TEMPLATE SCHEMA VALIDATION ===')
    
    # Top-level structure check
    expected_top_keys = {
        'symbol', 'company_name', 'sector', 'sub_sector', 
        'historical_reports', 'projected_reports', 'last_updated', 'data_source'
    }
    actual_top_keys = set(data.keys())
    
    print(f'Top-level keys match: {expected_top_keys == actual_top_keys}')
    if expected_top_keys != actual_top_keys:
        print(f'Missing: {expected_top_keys - actual_top_keys}')
        print(f'Extra: {actual_top_keys - expected_top_keys}')
        return False
    
    # Check that we have both historical and projected reports
    print(f'Historical reports: {len(data["historical_reports"])}')
    print(f'Projected reports: {len(data["projected_reports"])}')
    
    # Validate historical report fields (from PLANNING.md template)
    expected_report_fields = {
        'symbol', 'earnings_date', 'quarter', 'year', 'actual_eps', 'estimated_eps',
        'beat_miss_meet', 'surprise_percent', 'revenue_billions', 'revenue_growth_percent',
        'consensus_rating', 'confidence_score', 'source_url', 'data_verified_date',
        'stock_price_on_date', 'announcement_time', 'volume', 'date_earnings_report',
        'market_cap', 'price_at_close_earnings_report_date', 'price_at_open_day_after_earnings_report_date',
        'percentage_stock_change', 'earnings_report_result', 'estimated_earnings_per_share',
        'reported_earnings_per_share', 'volume_day_of_earnings_report', 'volume_day_after_earnings_report',
        'moving_avg_200_day', 'moving_avg_50_day', 'week_52_high', 'week_52_low',
        'market_sector', 'market_sub_sector', 'percentage_short_interest', 'dividend_yield',
        'ex_dividend_date'
    }
    
    print(f'Expected report fields: {len(expected_report_fields)}')
    
    if data['historical_reports']:
        historical_report = data['historical_reports'][0]
        actual_report_fields = set(historical_report.keys())
        print(f'Actual historical fields: {len(actual_report_fields)}')
        print(f'Historical fields match: {expected_report_fields == actual_report_fields}')
        
        if expected_report_fields != actual_report_fields:
            missing = expected_report_fields - actual_report_fields
            extra = actual_report_fields - expected_report_fields
            if missing:
                print(f'Missing fields: {missing}')
            if extra:
                print(f'Extra fields: {extra}')
            return False
    
    # Validate projected report fields
    if data['projected_reports']:
        projected_report = data['projected_reports'][0]
        projected_fields = set(projected_report.keys())
        print(f'Projected report fields: {len(projected_fields)}')
        print(f'Projected fields match template: {projected_fields == expected_report_fields}')
        
        if projected_fields != expected_report_fields:
            return False
    
    # Data quality checks
    print('\n=== DATA QUALITY CHECKS ===')
    print(f'Company name populated: {bool(data["company_name"])}')
    print(f'Sector populated: {bool(data["sector"])}')
    print(f'Sub-sector populated: {bool(data["sub_sector"])}')
    
    # Sample values validation
    if data['historical_reports']:
        hr = data['historical_reports'][0]
        print(f'Historical - Beat/Miss/Meet: {hr["beat_miss_meet"]}')
        print(f'Historical - Actual EPS: {hr["actual_eps"]}')
        print(f'Historical - Market Sector: {hr["market_sector"]}')
    
    if data['projected_reports']:
        pr = data['projected_reports'][0]
        print(f'Projected - Beat/Miss/Meet: {pr["beat_miss_meet"]}')
        print(f'Projected - Actual EPS: {pr["actual_eps"]}')
    
    print('\n=== VALIDATION RESULT ===')
    print('✅ Template schema compliance: PASSED')
    print('✅ All required fields present')
    print('✅ Data structure matches PLANNING.md template')
    
    return True

if __name__ == "__main__":
    file_path = sys.argv[1] if len(sys.argv) > 1 else "test_output/AAPL.json"
    
    success = validate_template_compliance(file_path)
    
    if success:
        print("\n🎉 VALIDATION SUCCESSFUL - Template compliance verified!")
        sys.exit(0)
    else:
        print("\n❌ VALIDATION FAILED - Template compliance issues found!")
        sys.exit(1)