import logging
from datetime import datetime, date
from bcb import sgs
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import mplcursors

#
# Overview
#

print('\n#----------------------------- Program Overview -----------------------------#\n')
print('The model reinvest the entirety of the hypothetical value on the first day of each month based on metrics from the previous month(s).')
print('- CDI (Certificado de Depósito Interbancário): CDI is an important interest rate benchmark in Brazil.')
print('- IBOV (Ibovespa): IBOV is the benchmark stock index of the São Paulo Stock Exchange (B3).')
print('- Previous Month Performance Method: Invests in IBOV if it outperformed CDI last month, and vice-versa.')
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

start_date = None
while start_date is None:
    start_date = input('Please input the analysis start date (YYYY-MM-DD): ')
    if not validate_date(start_date):
        print('Invalid date. Please use YYYY-MM-DD format.')
        start_date = None

#
# CDI
#

# Fetch historical CDI data
cdi_data = sgs.get({'CDI': 11}, start=start_date)
cdi_data = cdi_data['CDI']

# Convert CDI rates to decimal form (dividing by 100)
cdi_daily_returns = cdi_data / 100

cdi_cumulative_daily_returns = (1 + cdi_daily_returns).cumprod()
cdi_month_closing = cdi_cumulative_daily_returns.resample('M').last()
cdi_returns = cdi_cumulative_daily_returns.resample('M').last().pct_change().dropna()

# Calculate returns for the first month (missing previously)
cdi_month_opening = cdi_cumulative_daily_returns.resample('M').first()
first_month_cdi_returns = (cdi_month_closing.iloc[0] - cdi_month_opening.iloc[0]) / cdi_month_opening.iloc[0]

#
# IBOV
#

# Download historical data for the Bovespa index (^BVSP)
ibov_data = yf.download('^BVSP', start=start_date)
ibov = ibov_data['Adj Close']

# Convert the index to datetime and sort the data by date in ascending order for all DataFrames
ibov.index = pd.to_datetime(ibov.index)
ibov = ibov.sort_index(ascending=True)

ibov_month_closing = ibov.resample('M').last()
ibov_returns = ibov.resample('M').last().pct_change().dropna()

# Calculate returns for the first month (missing previously)
ibov_month_opening = ibov.resample('M').first()
first_month_ibov_returns = (ibov_month_closing.iloc[0] - ibov_month_opening.iloc[0]) / ibov_month_opening.iloc[0]

#
# Model
#

returns = pd.DataFrame(columns=['CDI', 'IBOV', 'Last Month Perf. Method'], index=ibov_returns.index)
returns['CDI'] = cdi_returns
returns['IBOV'] = ibov_returns

choices = pd.DataFrame(columns=['Last Month Perf. Method'], index=ibov_returns.index)

for index, date in enumerate(ibov_returns.index):
    if index < len(ibov_returns.index):
        if index > 0:
            if ibov_returns.iloc[index - 1] > cdi_returns.iloc[index - 1]:
                lm_returns = ibov_returns.iloc[index]
                lm_choice = 'IBOV'
            else:
                lm_returns = cdi_returns.iloc[index]
                lm_choice = 'CDI'
        else:
            if first_month_ibov_returns > first_month_cdi_returns:
                lm_returns = ibov_returns.iloc[index]
                lm_choice = 'IBOV'
            else:
                lm_returns = cdi_returns.iloc[index]
                lm_choice = 'CDI'

        returns.loc[date, 'Last Month Perf. Method'] = lm_returns
        choices.loc[date, 'Last Month Perf. Method'] = lm_choice

cumulative_returns = (1 + returns).cumprod() - 1

#
# Graph
#

plt.style.use('./mplstyles/financialgraphs.mplstyle')

performance, axes = plt.subplots(figsize=(14, 8))

axes.plot(cumulative_returns['CDI'], label='CDI')
axes.plot(cumulative_returns['IBOV'], label='IBOV')
axes.plot(cumulative_returns['Last Month Perf. Method'], label='Last Month Perf. Method')

axes.yaxis.set_major_formatter(ticker.PercentFormatter(1.0))
plt.xlabel('Time')
plt.ylabel('Performance')
axes.set_title('Performance x Time')
plt.legend(title=f'LMP current investment: {choices["Last Month Perf. Method"].iloc[len(ibov_returns.index) - 1]}')

# Add hover tooltips using mplcursors
cursor = mplcursors.cursor()
@cursor.connect("add")
def on_add(sel):
    sel.annotation.get_bbox_patch().set(fc='gray', alpha=0.8)
    sel.annotation.get_bbox_patch().set_edgecolor('gray')
    sel.annotation.arrow_patch.set_color('white')
    sel.annotation.arrow_patch.set_arrowstyle('-')

plt.show()
