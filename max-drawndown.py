import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib.ticker as ticker
import mplcursors
import logging

#
# Overview
#

print('\n#------------------------ Program Overview ------------------------#\n')
print('- The program will download historical data for the asset and calculate its drawdown.')
print('- It then plots the drawdown graph, allowing interactive exploration.')
print('- The maximum drawdown value is displayed on the graph.')
print('\n#------------------------------------------------------------------#\n')

#
# Inputs
#

# Initialize variables for start date and asset ticker
start_date = None
asset_ticker = None

# Set the logging level for yfinance to CRITICAL to reduce noise
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

# Function to validate date format (YYYY-MM-DD)
def validate_date(input_date):
    try:
        # Check if the input matches the desired format (YYYY-MM-DD)
        datetime.strptime(input_date, '%Y-%m-%d')
        # Ensure the year, month, and day have the correct number of digits
        year, month, day = map(str, input_date.split('-'))
        if len(year) == 4 and len(month) == 2 and len(day) == 2:
            return True
        else:
            return False
    except:
        return False

# Function to validate and download asset data
def validate_asset(asset_input, start_date):
    try:
        print('\n')
        # Download asset data using yfinance
        asset = yf.download(asset_input, start_date)['Adj Close']
        if len(asset) > 0:
            return asset  # Return asset data if successfully downloaded
    except:
        return False

# Prompt the user for the start date until a valid one is provided
while start_date is None:
    start_date = input('Please input the analysis start date (YYYY-MM-DD): ')
    if not validate_date(start_date):
        print('Invalid date format. Please use YYYY-MM-DD format.')
        start_date = None

# Prompt the user for the asset ticker symbol until a valid one is provided
while asset_ticker is None:
    asset_ticker = input('Specify the asset ticker symbol: ')
    asset_data = validate_asset(asset_ticker, start_date)
    if asset_data is None:
        print('Invalid input. Please enter a valid asset ticker symbol.')
        asset_ticker = None 

#
# Asset
#

# Calculate the maximum drawdown of the asset
asset_data_max = asset_data.cummax()
drawdowns = (asset_data - asset_data_max) / asset_data_max
drawdown_max = drawdowns.min()  # Find the smallest value of drawdowns, which represents the maximum drawdown

#
# Graph
#

# Set the style for the graph using a custom style file
plt.style.use('./financialgraphs.mplstyle')

# Create a subplot for the drawdown graph
drawdown, ax = plt.subplots(figsize=(14, 8))

# Plot the drawdown data on the graph
ax.plot(drawdowns, label=asset_ticker)

# Format the y-axis as a percentage
ax.yaxis.set_major_formatter(ticker.PercentFormatter(1.0))

# Set labels and title for the graph
ax.set_xlabel('Date')
ax.set_ylabel('Drawdown')
ax.set_title('Drawdown x Time')

# Add a legend to the graph with the maximum drawdown value
plt.legend(title=f'Max Drawdown: {drawdown_max:.2%}')

# Enable cursor interaction on the graph
mplcursors.cursor()

# Display the graph
plt.show()