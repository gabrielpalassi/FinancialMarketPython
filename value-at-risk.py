import logging
from datetime import datetime, date
import yfinance as yf
import numpy as np

#
# Overview
#

print('\n#----------------------------- Program Overview -----------------------------#\n')
print('This program calculates the Value at Risk (VaR) for a given portfolio or assets using historical simulation.')
print('You can choose to calculate VaR for individual assets or for a portfolio, informing the weights.')
print('It then downloads historical data for the specified assets and calculates the VaR for a given confidence level.')
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
        # Ensure the year, month, and day have the correct number of digits
        year, month, day = map(str, input_date.split('-'))
        if len(year) == 4 and len(month) == 2 and len(day) == 2:
            # Check if the parsed date is before today
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

confidence_level = None
while confidence_level is None:
    try:
        confidence_level = float(input('Please enter the confidence level (e.g., 95 for 95%): ')) / 100.0
        if confidence_level <= 0 or confidence_level >= 1:
            print('Invalid confidence level. Please enter a value between 1 and 99.')
            confidence_level = None
    except ValueError:
        print('Invalid input. Please enter a number between 1 and 99.')

calculation_type = input('Do you want to calculate VaR for individual assets or for a portfolio? (assets/portfolio): ')
while calculation_type not in ['assets', 'portfolio']:
    calculation_type = input('Invalid input. Please enter "assets" or "portfolio": ')

asset_tickers = None
while asset_tickers is None:
    asset_tickers = input('Specify the asset ticker symbols (comma-separated): ')
    assets = validate_assets(asset_tickers, start_date)
    if not assets:
        print('No valid assets found. Please enter at least one valid asset ticker symbol.')
        asset_tickers = None

# If calculating VaR for a portfolio, gather asset weights
asset_weights = {}
if calculation_type == 'portfolio':
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
# Assets
#

# Calculate the VaR for each asset if assets was selected
if calculation_type == 'assets':
    for ticker, asset_data in assets.items():
        returns = asset_data.resample('M').last().pct_change().dropna()
        ordered_returns = np.sort(returns.values)
        alpha_returns_position = int((1 - confidence_level) * len(ordered_returns))
        var = abs(ordered_returns[alpha_returns_position] * 100)
        print(f'The VaR at a {confidence_level * 100}% confidence level for {ticker} is: {var:.2f}%')

#
# Portfolio
#

# Calculate the VaR for the given portfolio if portfolio was selected
if calculation_type == 'portfolio':
    combined_asset_data = None
    for ticker, asset_data in assets.items():
        weighted_asset_data = asset_data * asset_weights[ticker]
        if combined_asset_data is None:
            combined_asset_data = weighted_asset_data
        else:
            combined_asset_data += weighted_asset_data
    returns = combined_asset_data.resample('M').last().pct_change().dropna()
    ordered_returns = np.sort(returns.values)
    alpha_returns_position = int((1 - confidence_level) * len(ordered_returns))
    var = abs(ordered_returns[alpha_returns_position] * 100)
    print(f'The VaR at a {confidence_level * 100}% confidence level for the given portfolio is: {var:.2f}%')
