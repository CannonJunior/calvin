#!/usr/bin/env python3
"""
Batch curation of all S&P 500 companies
Handles API limits and tracks progress
"""

import json
import sys
import time
import subprocess
from datetime import datetime

def load_sp500_companies():
    """Load S&P 500 companies from JSON file"""
    with open('sp500_companies.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def load_progress():
    """Load current progress from markdown file"""
    try:
        with open('sp500_curation_progress.md', 'r') as f:
            content = f.read()
        
        completed = []
        if '- [x] **' in content:
            lines = content.split('\n')
            for line in lines:
                if '- [x] **' in line:
                    # Extract symbol from lines like "- [x] **AAPL** - Apple Inc."
                    symbol = line.split('**')[1]
                    completed.append(symbol)
        
        return completed
    except:
        return ['AAPL']  # Default to AAPL being completed

def update_progress_file(symbol, company_name, status):
    """Update the progress markdown file"""
    try:
        with open('sp500_curation_progress.md', 'r') as f:
            content = f.read()
        
        # Update completion count
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if '**Completed**:' in line:
                completed_count = len([l for l in lines if '- [x] **' in l]) + 1
                remaining_count = 503 - completed_count
                lines[i] = f'**Completed**: {completed_count}'
                lines[i+1] = f'**Remaining**: {remaining_count}'
                break
        
        # Add to completed section
        for i, line in enumerate(lines):
            if '## Completed Companies ✅' in line:
                # Find the end of completed section
                j = i + 1
                while j < len(lines) and not lines[j].startswith('## '):
                    j += 1
                
                # Insert new completion
                new_entry = f'- [x] **{symbol}** - {company_name} ({status})'
                lines.insert(j, new_entry)
                break
        
        with open('sp500_curation_progress.md', 'w') as f:
            f.write('\n'.join(lines))
            
    except Exception as e:
        print(f"Failed to update progress file: {e}")

def curate_company(symbol):
    """Curate a single company and return status"""
    print(f"\n🔄 Processing {symbol}...")
    
    try:
        result = subprocess.run(
            ['python3', 'simple_curate_stock.py', symbol],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            # Extract earnings info from output
            output = result.stdout
            if 'real +' in output:
                # Extract the earnings count line
                for line in output.split('\n'):
                    if ': ' in line and 'real +' in line and 'future earnings' in line:
                        earnings_info = line.split(': ')[1]
                        return f"✅ {earnings_info}"
            return "✅ Completed"
        else:
            print(f"❌ Error output: {result.stderr}")
            return "❌ Failed"
            
    except subprocess.TimeoutExpired:
        return "⏰ Timeout"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def main():
    """Main batch curation function"""
    print("🚀 Starting batch S&P 500 earnings curation...")
    
    # Load companies and progress
    companies = load_sp500_companies()
    completed = load_progress()
    
    print(f"📊 Total companies: {len(companies)}")
    print(f"✅ Already completed: {len(completed)}")
    print(f"🔄 Remaining: {len(companies) - len(completed)}")
    
    # Filter to pending companies
    pending_companies = [c for c in companies if c['symbol'] not in completed]
    
    if not pending_companies:
        print("🎉 All companies already completed!")
        return
    
    print(f"\n🎯 Processing {len(pending_companies)} pending companies...")
    
    success_count = 0
    error_count = 0
    api_limit_hits = 0
    
    start_time = time.time()
    
    for i, company in enumerate(pending_companies):
        symbol = company['symbol']
        company_name = company['company_name']
        
        print(f"\n📈 [{i+1}/{len(pending_companies)}] {symbol} - {company_name}")
        
        # Curate the company
        status = curate_company(symbol)
        
        # Update progress
        update_progress_file(symbol, company_name, status)
        
        if '✅' in status:
            success_count += 1
            print(f"✅ {symbol} completed: {status}")
        else:
            error_count += 1
            print(f"❌ {symbol} failed: {status}")
            
            if 'API limit' in status or 'Note' in status:
                api_limit_hits += 1
                if api_limit_hits >= 3:
                    print("\n⚠️ Multiple API limit hits detected. Stopping curation.")
                    print("API limits have been reached. Wait for reset and run script again.")
                    break
        
        # Progress update every 10 companies
        if (i + 1) % 10 == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed * 60  # companies per minute
            remaining_time = (len(pending_companies) - i - 1) / rate if rate > 0 else 0
            
            print(f"\n📊 Progress Update:")
            print(f"   Processed: {i+1}/{len(pending_companies)}")
            print(f"   Success: {success_count}, Errors: {error_count}")
            print(f"   Rate: {rate:.1f} companies/min")
            print(f"   Est. remaining time: {remaining_time:.1f} minutes")
        
        # Small delay to be respectful to APIs
        time.sleep(1)
    
    # Final summary
    total_time = time.time() - start_time
    print(f"\n🎉 Batch curation completed!")
    print(f"   Total processed: {success_count + error_count}")
    print(f"   Successful: {success_count}")
    print(f"   Errors: {error_count}")
    print(f"   Total time: {total_time/60:.1f} minutes")
    print(f"   Average rate: {(success_count + error_count)/(total_time/60):.1f} companies/min")
    
    if api_limit_hits >= 3:
        print(f"\n⚠️ Stopped due to API limits. Resume later when limits reset.")
    else:
        print(f"\n✅ All remaining companies processed!")

if __name__ == "__main__":
    main()