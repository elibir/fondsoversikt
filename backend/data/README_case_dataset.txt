Fund Screener case dataset

These CSV files are curated sample data for the candidate case.
They are designed so candidates can build the app against CSV input instead of Yahoo Finance live calls.

Files
- funds.csv
- fund_metrics.csv
- fund_prices_monthly.csv
- fund_sector_exposure.csv
- fund_top_holdings.csv
- company_financials.csv

How the extra files can be used
- fund_top_holdings.csv maps each fund to representative company holdings and weights
- company_financials.csv contains curated company-level financial-report style metrics that can be used to score company quality
- candidates can derive a weighted portfolio quality score for each fund by combining holdings weights with company quality metrics

Important
- This is a curated sample dataset for the case, not live market data
- The company financials are intended for ranking and algorithm design, not for production investment decisions
