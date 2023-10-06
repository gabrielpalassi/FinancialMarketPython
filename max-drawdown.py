import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime, date
import matplotlib.ticker as mplticker
import mplcursors
import logging

#
# Overview
#

print('\n#------------------------ Program Overview ------------------------#\n')
print('- This program downloads historical data for a given portfolio or individual assets and calculates their drawdowns.')
print('- It then plots the drawdown graphs, allowing interactive exploration.')
print('- The maximum drawdown values are also displayed.')
print('\n#------------------------------------------------------------------#\n')

#
# Inputs
#

# Set the logging level for yfinance to CRITICAL to reduce noise
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

# Initialize variables for start date and asset tickers
start_date = None
asset_tickers = None

# Function to validate starting date input
def validate_date(input_date):
    try:
        # Check if the input matches the desired format (YYYY-MM-DD)
        parsed_date = datetime.strptime(input_date, '%Y-%m-%d')
        # Ensure the year, month, and day have the correct number of digits
        year, month, day = map(str, input_date.split('-'))
        if len(year) == 4 and len(month) == 2 and len(day) == 2:
            # Check if the parsed date is before today
            if parsed_date.date() < date.today():
                return True
            else:
                print("The start date should be before today's date.")
                return False
        else:
            return False
    except:
        return False

# Function to validate and download asset data
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

# Prompt the user for the start date until a valid one is provided
while start_date is None:
    start_date = input('Please input the analysis start date (YYYY-MM-DD): ')
    if not validate_date(start_date):
        print('Invalid date. Please use YYYY-MM-DD format.')
        start_date = None

# Ask the user whether they want drawdown of individual assets or of the portfolio
drawdown_type = input('Do you want the drawdown of individual assets or of the portfolio? (assets/portfolio): ')
while drawdown_type not in ['assets', 'portfolio']:
    drawdown_type = input('Invalid input. Please enter "assets" or "portfolio": ')

# Prompt the user for asset tickers until at least one valid one is provided
while asset_tickers is None:
    asset_tickers = input('Specify the asset ticker symbols (comma-separated): ')
    assets = validate_assets(asset_tickers, start_date)
    if not assets:
        print('No valid assets found. Please enter at least one valid asset ticker symbol.')
        asset_tickers = None

# Initialize a dictionary to store asset weights for the portfolio
asset_weights = {}

# If calculating drawdown_type for a portfolio, gather asset weights
if drawdown_type == 'portfolio':
    while True:
        # Initialize a variable to keep track of the total weight
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
# Assets
#

# Calculate the maximum drawdown for each asset and store the results in a dictionary
max_drawdowns = {}
for ticker, asset_data in assets.items():
    asset_data_max = asset_data.cummax()
    drawdowns = (asset_data - asset_data_max) / asset_data_max
    drawdown_max = drawdowns.min()
    max_drawdowns[ticker] = drawdown_max

#
# Portfolio
#

# Calculate the maximum drawdown of the portfolio if portfolio was selected
if drawdown_type == 'portfolio':
    # Initialize combined_drawdowns
    combined_drawdowns = None
    for ticker, asset_data in assets.items():
        weighted_asset_data = asset_data * asset_weights[ticker]
        if combined_drawdowns is None:
            combined_drawdowns = weighted_asset_data
        else:
            combined_drawdowns += weighted_asset_data

    combined_drawdowns_max = combined_drawdowns.cummax()
    combined_portfolio_drawdowns = (combined_drawdowns - combined_drawdowns_max) / combined_drawdowns_max
    # Add the maximum drawdown of the portfolio to the max_drawdowns dictionary
    max_drawdowns['Portfolio'] = combined_portfolio_drawdowns.min()

#
# Graph
#

# Set the style for the graph using a custom style file
plt.style.use('./financialgraphs.mplstyle')

# Create a subplot for the drawdown graph
drawdown, ax = plt.subplots(figsize=(14, 8))

# Plot the drawdown data for each asset on the graph if individual assets selected
if drawdown_type == 'assets':
    for ticker, asset_data in assets.items():
        drawdowns = (asset_data - asset_data.cummax()) / asset_data.cummax()
        ax.plot(drawdowns, label=ticker)

# Calculate and plot the drawdown of the portfolio if selected
elif drawdown_type == 'portfolio':
    ax.plot(combined_portfolio_drawdowns, label='Portfolio')

# Format the y-axis as a percentage
ax.yaxis.set_major_formatter(mplticker.PercentFormatter(1.0))

# Set title for the graph
ax.set_title('Drawdown x Time')

# Add a legend to the graph with the maximum drawdown values for each asset and the portfolio
legend_text = "\n".join([f"{ticker}: {max_drawdown:.2%}" for ticker, max_drawdown in max_drawdowns.items()])
plt.legend(title=f'Max Drawdowns:\n{legend_text}')

# Enable cursor interaction on the graph
mplcursors.cursor()

# Display the graph
plt.show()
