This is a research repository.
You are not allowed to leave this directory tree to view any files.
For each element in the sp500_companies.json list, perform research on the company referred to in the <symbol> field.
Your primary research tool will be to curate data for each <symbol> here:
https://www.nasdaq.com/market-activity/stocks/<symbol>/earnings

Where if the symbol listed in sp500_companies.json is "AAPL", the URL is this:
https://www.nasdaq.com/market-activity/stocks/aapl/earnings

Create a .json file for each company. For each company research historical earnings information. Information should resemble the <earnings_template> here:
<earnings_template>
{
	# Q2 2025 - March 29, 2025 quarter ending, reported May 1, 2025
	'symbol': 'AAPL',
	'earnings_date': '2025-05-01',  # Actual reporting date
	'quarter': 2,
	'year': 2025,
	'actual_eps': 1.65,  # From Apple press release
	'estimated_eps': 1.63,  # From search results
	'beat_miss_meet': 'BEAT',  # 1.65 > 1.63
	'surprise_percent': 1.2,  # ((1.65-1.63)/1.63)*100
	'revenue_billions': 95.4,  # From Apple press release
	'revenue_growth_percent': 5.0,  # Up 5% year over year
	'consensus_rating': 'Buy',
	'confidence_score': 1.0,  # Past data, fully verified
	'source_url': 'https://www.nasdaq.com/market-activity/stocks/aapl/earnings',
	'data_verified_date': date.today(),
	'stock_price_on_date': 213.32,  # Approximate from user info
	'announcement_time': 'AMC',
	'volume': 50000000,  # Typical volume
	'date_earnings_report':,
	'market_cap':,
	'price_at_close-earnings_report_date':,
	'price_at_open-day_after_earnings_report_date':,
	'percentage_stock_change':,
	'earnings_report_result': 'BEAT',
	'estimated_earnings_per_share':,
	'reported_earnings_per_share':,
	'volume_day_of_earnings_ report':,
	'volume_day_after_earnings_report':,
	'200-day_moving_average':,
	'50-day_moving_average':,
	'52-week_high':,
	'52-week_low':,
	'market_sector':,
	'market_ sub_sector':,
	'percentage_short_ interest':,
	'dividend_yield':,
	'Ex-dividend date': #(closest to the earnings report)
}
</earnings-template>

All of this data is required for each earnings report on a stock. Each stock is expected to have a list of past earnings reports as well as future projected earnings report. Additional data can be included, as it is discovered.
