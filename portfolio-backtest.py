import logging
from datetime import datetime, date
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.ticker as mplticker
import mplcursors
import pandas as pd

#
# Overview
#

print('\n#----------------------------- Program Overview -----------------------------#\n')
print('This program downloads historical data for a given portfolio and calculates its returns.')
print('It then plots the cumulative returns of the portfolio and its assets over time.')
print('Important: If an asset in the portfolio was created after the start date, its returns')
print('will be set to 0 for the period before its inception, and the portfolio returns will be')
print('adjusted accordingly.')
print('\n#----------------------------------------------------------------------------#\n')

#
# Inputs
#

# Set the logging level for yfinance to CRITICAL to reduce noise
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

def validate_date(input_date):
    try:
        # Check if the input matches the desired format (YYYY-MM-DD)
        parsed_date = datetime.strptime(input_date, '%Y-%m-%d')
        year, month, day = map(str, input_date.split('-'))
        if len(year) == 4 and len(month) == 2 and len(day) == 2:
            if parsed_date.date() < date.today():
                return True
            else:
                print('The start date should be before today\'s date.')
                return False
        else:
            return False
    except:
        return False

def validate_assets(asset_inputs, start_date):
    assets = {}
    asset_tickers = asset_inputs.split(',')
    for ticker in asset_tickers:
        # Remove leading/trailing spaces
        ticker = ticker.strip() 
        # Download asset data using yfinance
        asset_data = yf.download(ticker, start_date)['Adj Close']
        if len(asset_data) > 0:
            # Store asset data if successfully downloaded
            assets[ticker] = asset_data
    return assets

def clear_weights(asset_weights, assets):
    asset_weights.clear()
    for ticker in assets.keys():
        asset_weights[ticker] = None
    return 0

start_date = None
while start_date is None:
    start_date = input('Please input the analysis start date (YYYY-MM-DD): ')
    if not validate_date(start_date):
        print('Invalid date. Please use YYYY-MM-DD format.')
        start_date = None

asset_tickers = None
while asset_tickers is None:
    asset_tickers = input('Specify the asset ticker symbols (comma-separated): ')
    assets = validate_assets(asset_tickers, start_date)
    if not assets:
        print('No valid assets found. Please enter at least one valid asset ticker symbol.')
        asset_tickers = None

asset_weights = {}
total_weight = clear_weights(asset_weights, assets)
while total_weight != 100:
    for ticker in assets.keys():
        while asset_weights[ticker] is None:
            try:
                weight = float(input(f'Enter the weight (as a percentage) of asset {ticker} in the portfolio: '))
                if weight < 0 or weight > 100:
                    print('Invalid weight. Please enter a value between 0 and 100.')
                else:
                    asset_weights[ticker] = weight
                    total_weight += weight
                    break
            except ValueError:
                print('Invalid input. Please enter a valid number.')
    if total_weight != 100:
        print(f'Total weight is {total_weight}, but it should be 100. Please re-enter the weights.')
        total_weight = clear_weights(asset_weights, assets)

#
# Calculate Cumulative Returns
#

# Align all assets data by reindexing them to the same dates
all_dates = pd.date_range(start=min([data.index.min() for data in assets.values()]), end=date.today())
aligned_assets = {ticker: data.reindex(all_dates).ffill() for ticker, data in assets.items()}

# Calculate cumulative returns for each asset
asset_cumulative_returns = {}
for ticker, data in aligned_assets.items():
    # Calculate daily returns
    daily_returns = data.pct_change().fillna(0)
    # Create a mask for the period the asset exists
    asset_exists_mask = data.notna().astype(float)
    # Calculate weighted daily returns
    weighted_returns = daily_returns * (asset_weights[ticker] / 100) * asset_exists_mask
    # Calculate cumulative returns
    asset_cumulative_returns[ticker] = (1 + daily_returns).cumprod() - 1

# Calculate cumulative returns for the portfolio
portfolio_returns = sum([data.pct_change().fillna(0) * (asset_weights[ticker] / 100) * data.notna().astype(float) for ticker, data in aligned_assets.items()])
cumulative_portfolio_returns = (1 + portfolio_returns).cumprod() - 1

#
# Graph
#

plt.style.use('./mplstyles/financialgraphs.mplstyle')

# Plot the cumulative returns
plt.figure(figsize=(14, 8))

# Plot portfolio cumulative returns
plt.plot(cumulative_portfolio_returns.index, cumulative_portfolio_returns, label='Portfolio', linewidth=2)

# Plot cumulative returns for each asset
for ticker, cum_returns in asset_cumulative_returns.items():
    plt.plot(cum_returns.index, cum_returns, label=f'{ticker}', linestyle='--')

plt.xlabel('Date')
plt.ylabel('Cumulative Returns')
plt.title('Portfolio and Asset Cumulative Returns Over Time')
plt.legend()
plt.grid(True)

# Format the x-axis to show dates clearly
plt.gca().xaxis.set_major_locator(mplticker.MaxNLocator(10))
plt.gcf().autofmt_xdate()

# Enable cursor interaction on the graph
cursor = mplcursors.cursor()
@cursor.connect("add")
def on_add(sel):
    sel.annotation.get_bbox_patch().set(fc='gray', alpha=0.8)
    sel.annotation.get_bbox_patch().set_edgecolor('gray')
    sel.annotation.arrow_patch.set_color('white')
    sel.annotation.arrow_patch.set_arrowstyle('-')

# Show the plot
plt.show()
