This is a research repository.
You are not allowed to leave this directory tree to view any files.
For each element in the sp500_companies.json list, perform research on the company referred to in the <symbol> field.
Your primary research tool will be to curate data for each <symbol> here:
https://www.nasdaq.com/market-activity/stocks/<symbol>/earnings

Where if the symbol listed in sp500_companies.json is "AAPL", the URL is this:
https://www.nasdaq.com/market-activity/stocks/aapl/earnings

Create a .json file for each company. For each company research historical earnings information. Information should include:
Date of the earnings report.
Market cap of the stock the day of the earnings report.
Stock price at the close, on the day of the earnings report.
Stock price at the open, on the day after the earnings report.
Percentage change between these close and open prices.
Earnings report result (beat or miss).
Estimated earnings per share.
Reported earnings per share.
Volume the day of the earnings report.
Volume the day after the earnings report.
200-day moving average for the stock
50-day moving average for the stock.
52-week high for the stock.
52-week low for the stock.
Company name.
Market sector the company is in.
Market sub-sector the company is in.
Percentage short interest in the stock.
Dividend yield of the stock.
Ex-dividend date (closest to the earnings report).

All of this data is required for each earnings report on a stock. Each stock is expected to have a list of past earnings reports as well as future projected earnings report. Additional data can be included, as it is discovered.
