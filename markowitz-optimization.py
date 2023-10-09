import logging
from datetime import datetime, date
import yfinance as yf
import pandas as pd
import numpy as np
from scipy import optimize
import matplotlib.pyplot as plt
import matplotlib.ticker as mplticker
import mplcursors

#
# Overview
#

print('\n#----------------------------- Program Overview -----------------------------#\n')
print('This program performs the Markowitz Portfolio Optimization on a given set of assets.')
print('It generates the portfolio weights according to the specified constrains. (user chosen)')
print('- Sharpe Ratio: Highest relation return/risk.')
print('- Return: Lowest risk for a specified expected return.')
print('- Risk: Highest return for a specified (or lower) volatility (risk).')
print('\n#----------------------------------------------------------------------------#\n')

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
                print('The start date should be before today\'s date.')
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

    # Convert the dictionary into a DataFrame
    assets = pd.DataFrame(assets)
    return assets

# Prompt the user for the start date until a valid one is provided
while start_date is None:
    start_date = input('Please input the analysis start date (YYYY-MM-DD): ')
    if not validate_date(start_date):
        print('Invalid date. Please use YYYY-MM-DD format.')
        start_date = None

# Prompt the user for asset tickers until at least one valid one is provided
while asset_tickers is None:
    asset_tickers = input('Specify the asset ticker symbols (comma-separated): ')
    assets = validate_assets(asset_tickers, start_date)
    if assets.empty:
        print('No valid assets found. Please enter at least one valid asset ticker symbol.')
        asset_tickers = None

# Calculate log returns of assets
log_returns = np.log(assets / assets.shift(1))

# Calculate the annualized mean of log returns
log_mean = log_returns.mean() * 252

# Calculate the annualized covariance matrix of log returns
covariance = log_returns.cov() * 252

# Define the bounds for portfolio weights (between 0 and 1)
bounds = [(0, 1)] * len(assets.columns)

# Define an initial guess for portfolio weights (equal weights)
initial_guess = [(1 / len(assets.columns))] * len(assets.columns)

# Define an initial constraint that ensures the sum of weights equals 1
constraints = [{'type':'eq','fun':lambda weights: np.sum(weights) - 1}]

# Define a function to calculate portfolio metrics (returns, volatility, sharpe ratio)
def metrics(weights):
    weights = np.array(weights)
    returns = log_mean.dot(weights)
    volatility = np.sqrt(weights.T.dot(covariance.dot(weights)))
    sharpe_ratio = returns / volatility
    return [returns, volatility, sharpe_ratio]

# Find maximum return
maximum_return_weights = optimize.minimize(lambda weights: metrics(weights)[0] * -1, initial_guess, method='SLSQP', bounds=bounds, constraints=constraints).x
maximum_return = metrics(maximum_return_weights)[0]

# Find minimum risk and its return
minimum_risk_weights = optimize.minimize(lambda weights: metrics(weights)[1], initial_guess, method='SLSQP', bounds=bounds, constraints=constraints).x
minimum_risk = metrics(minimum_risk_weights)[1]
minimum_risk_return = metrics(minimum_risk_weights)[0]

# Find maximum risk
maximum_risk_weights = optimize.minimize(lambda weights: metrics(weights)[1] * -1, initial_guess, method='SLSQP', bounds=bounds, constraints=constraints).x
maximum_risk = metrics(maximum_risk_weights)[1]

# Prompt the user to choose the optimization goal: maximizing sharpe ratio, return for a given risk or minimizing risk for a given return
calculation_type = input('Choose the optimization goal ("sharpe", "risk" or "return"): ')
while calculation_type not in ['sharpe', 'risk', 'return']:
    calculation_type = input('Invalid input. Please enter either "sharpe", "risk" or "return": ')

# If calculating the portfolio maximizing return for a given risk, prompt the user for the desired risk level
if calculation_type == 'risk':
    while True:
        try:
            risk_tolerance = float(input(f'Enter your desired risk level (e.g., 0.10 for 10%) (between {minimum_risk:.2} and {maximum_risk:.2}): '))
            # Check if the risk_tolerance is within the desired range
            if minimum_risk <= risk_tolerance <= maximum_risk:
                # Break the loop if the input is successfully converted to a float and falls within the range
                break
            else:
                print(f'Risk tolerance must be between {minimum_risk:.2} and {maximum_risk:.2}.')
        except ValueError:
            print('Invalid input. Please enter a valid number for risk.')

# If calculating the portfolio minimizing risk for a given return, prompt the user for the desired return
if calculation_type == 'return':
    while True:
        try:
            expected_return = float(input(f'Enter your desired expected return (e.g., 0.10 for 10%) (between {minimum_risk_return:.2} and {maximum_return:.2}): '))
            if minimum_risk_return <= expected_return <= maximum_return:
                # Break the loop if the input is successfully converted to a float
                break
            else:
                print(f'Expected return must be between {minimum_risk_return:.2} and {maximum_return:.2}.')
        except ValueError:
            print('Invalid input. Please enter a valid number for return.')

#
# Optimization
#

# Check the type of calculation to perform
if calculation_type == 'sharpe':
    # Use the minimize function to find optimal weights that maximize Sharpe ratio (minimize sharpe_ratio * -1)
    optimal_weights = optimize.minimize(lambda weights: metrics(weights)[2] * -1, initial_guess, method='SLSQP', bounds=bounds, constraints=constraints).x

elif calculation_type == 'risk':
    # Use the minimize function to find optimal weights that maximize Sharpe ratio (minimize sharpe_ratio * -1)
    sharpe_ratio_optimal_weights = optimize.minimize(lambda weights: metrics(weights)[2] * -1, initial_guess, method='SLSQP', bounds=bounds, constraints=constraints).x
    # Define constraints for the sum of weights to be equal to 1 and risk to be less than or equal to the specified risk tolerance
    constraints.append({'type': 'ineq', 'fun': lambda weights: risk_tolerance - metrics(weights)[1]})  # Change to inequality constraint
    # Use the minimize function to find optimal weights that maximize return (minimize return * -1)
    optimal_weights = optimize.minimize(lambda weights: metrics(weights)[0] * -1, initial_guess, method='SLSQP', bounds=bounds, constraints=constraints).x


elif calculation_type == 'return':
    # Use the minimize function to find optimal weights that maximize Sharpe ratio (minimize sharpe_ratio * -1)
    sharpe_ratio_optimal_weights = optimize.minimize(lambda weights: metrics(weights)[2] * -1, initial_guess, method='SLSQP', bounds=bounds, constraints=constraints).x
    # Define constraints for the sum of weights to be equal to 1 and expected return to be equal to the specified value
    constraints.append({'type': 'eq', 'fun': lambda weights: metrics(weights)[0] - expected_return})
    # Use the minimize function to find optimal weights that minimize risk
    optimal_weights = optimize.minimize(lambda weights: metrics(weights)[1], initial_guess, method='SLSQP', bounds=bounds, constraints=constraints).x

#
# Efficient Frontier
#

# Generate a range of target returns
target_returns = np.linspace(minimum_risk_return, maximum_return, 100)

# Initialize lists to store results
efficient_frontier_volatility = []
efficient_frontier_return = []

# Calculate the efficient frontier
for target_return in target_returns:
    # Set up the optimization constraints for the target return
    constraints = [
        {'type': 'eq', 'fun': lambda weights: np.sum(weights) - 1},
        {'type': 'eq', 'fun': lambda weights: metrics(weights)[0] - target_return}
    ]
    # Optimize for minimum volatility given the target return
    result = optimize.minimize(lambda weights: metrics(weights)[1], initial_guess, method='SLSQP', bounds=bounds, constraints=constraints)
    # Add the results to the efficient frontier lists
    efficient_frontier_volatility.append(result.fun)
    efficient_frontier_return.append(target_return)

#
# Graph
#

# Set the style for the graph using a custom style file
plt.style.use('./financialgraphs.mplstyle')

# Create a subplot for the drawdown graph
markowitz_optimization, ax = plt.subplots(figsize=(14, 8))

# Plot the efficient frontier line
ax.plot(efficient_frontier_volatility, efficient_frontier_return, label='Efficient Frontier')

# Plot a point for the optimal and maximum sharpe ratio portfolios on the graph
if calculation_type == 'sharpe':
    ax.scatter(metrics(optimal_weights)[1], metrics(optimal_weights)[0], marker='o', label='Optimal Portfolio')
else:
    ax.scatter(metrics(sharpe_ratio_optimal_weights)[1], metrics(sharpe_ratio_optimal_weights)[0], marker='o', label='Max. Sharpe Ratio')
    ax.scatter(metrics(optimal_weights)[1], metrics(optimal_weights)[0], marker='o', label='Optimal Portfolio')

# Format the axis and the title
ax.xaxis.set_major_formatter(mplticker.PercentFormatter(1.0))
ax.yaxis.set_major_formatter(mplticker.PercentFormatter(1.0))
plt.xlabel('Volatility')
plt.ylabel('Return')
ax.set_title('Anual Expected Return x Volatility')

# Add a legend to the graph with the maximum drawdown values for each asset and the portfolio
legend_text = '\n'.join([f'{metric}: {metrics(optimal_weights)[i]:.2%}' for i, metric in enumerate(['Expected Return','Volatility','Sharpe Ratio'])]) + '\n\n'
legend_text = legend_text + '\n'.join([f'{asset}\'s weight: {i:.2%}' for asset, i in zip(assets.columns.tolist(), optimal_weights)]) + '\n'
plt.legend(title=f'{legend_text}')

# Enable cursor interaction on the graph
mplcursors.cursor()

# Display the graph
plt.show()
