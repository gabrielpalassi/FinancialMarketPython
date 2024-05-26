import logging
from datetime import datetime, date
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.ticker as mplticker
import mplcursors

#
# Overview
#

print('\n#----------------------------- Program Overview -----------------------------#\n')
print('This program downloads historical data for a given portfolio or assets and calculates their drawdowns.')
print('It then plots the drawdown graphs, allowing interactive exploration and displays the maximum drawdown.')
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

start_date = None
while start_date is None:
    start_date = input('Please input the analysis start date (YYYY-MM-DD): ')
    if not validate_date(start_date):
        print('Invalid date. Please use YYYY-MM-DD format.')
        start_date = None

drawdown_type = input('Do you want the drawdown of individual assets or of the portfolio? (assets/portfolio): ')
while drawdown_type not in ['assets', 'portfolio']:
    drawdown_type = input('Invalid input. Please enter "assets" or "portfolio": ')

asset_tickers = None
while asset_tickers is None:
    asset_tickers = input('Specify the asset ticker symbols (comma-separated): ')
    assets = validate_assets(asset_tickers, start_date)
    if not assets:
        print('No valid assets found. Please enter at least one valid asset ticker symbol.')
        asset_tickers = None

# If calculating VaR for a portfolio, gather asset weights
asset_weights = {}
if drawdown_type == 'portfolio':
    while True:
        total_weight = 0
        for ticker in assets.keys():
            while True:
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
        else:
            break

#
# Drawdown
#

# Calculate the maximum drawdown for each asset and store the results in a dictionary
max_drawdowns = {}
for ticker, asset_data in assets.items():
    asset_data_max = asset_data.cummax()
    drawdowns = (asset_data - asset_data_max) / asset_data_max
    drawdown_max = drawdowns.min()
    max_drawdowns[ticker] = drawdown_max

# Calculate the maximum drawdown of the portfolio if portfolio was selected
if drawdown_type == 'portfolio':
    combined_asset_data = None
    for ticker, asset_data in assets.items():
        weighted_asset_data = asset_data * asset_weights[ticker]
        if combined_asset_data is None:
            combined_asset_data = weighted_asset_data
        else:
            combined_asset_data += weighted_asset_data

    combined_asset_data_max = combined_asset_data.cummax()
    combined_portfolio_drawdowns = (combined_asset_data - combined_asset_data_max) / combined_asset_data_max
    max_drawdowns['Portfolio'] = combined_portfolio_drawdowns.min()

#
# Graph
#

plt.style.use('./mplstyles/financialgraphs.mplstyle')

drawdown, axes = plt.subplots(figsize=(14, 8))

if drawdown_type == 'assets':
    for ticker, asset_data in assets.items():
        drawdowns = (asset_data - asset_data.cummax()) / asset_data.cummax()
        axes.plot(drawdowns, label=ticker)
elif drawdown_type == 'portfolio':
    axes.plot(combined_portfolio_drawdowns, label='Portfolio')

axes.yaxis.set_major_formatter(mplticker.PercentFormatter(1.0))
plt.xlabel('Time')
plt.ylabel('Drawdown')
axes.set_title('Drawdown x Time')

legend_text = '\n'.join([f'{ticker}: {max_drawdown:.2%}' for ticker, max_drawdown in max_drawdowns.items()]) + '\n'
plt.legend(title=f'Max. Drawdowns:\n\n{legend_text}')

# Enable cursor interaction on the graph
cursor = mplcursors.cursor()
@cursor.connect("add")
def on_add(sel):
    sel.annotation.get_bbox_patch().set(fc='gray', alpha=0.8)
    sel.annotation.get_bbox_patch().set_edgecolor('gray')
    sel.annotation.arrow_patch.set_color('white')
    sel.annotation.arrow_patch.set_arrowstyle('-')

plt.show()
