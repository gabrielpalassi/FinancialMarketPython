from datetime import datetime, date
from bcb import sgs
from bcb import currency
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import mplcursors

#
# Overview
#

print('\n#----------------------------- Program Overview -----------------------------#\n')
print('This program retrieves and graphs hirstorical financial data from the Brazilian Central Bank (BCB).')
print('- Selic (Sistema Especial de Liquidação e Custódia): Selic is the Brazilian Central Bank\'s benchmark interest rate.')
print('- IPCA (Índice Nacional de Preços ao Consumidor Amplo): IPCA represents the official inflation index in Brazil.')
print('- IGP-M (Índice Geral de Preços do Mercado): IGP-M is another important inflation index in Brazil.')
print('- Currencies: The program also tracks the exchange rates of USD and EUR against the Brazilian Real (BRL).')
print('\n#----------------------------------------------------------------------------#\n')

#
# Inputs
#

# Initialize start_date variable for input
start_date = None

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
                print('Downloading data...')
                return True
            else:
                print('The start date should be before today\'s date.')
                return False
        else:
            return False
    except:
        return False

# Loop to get valid start_date input
while start_date is None:
    start_date = input('Please input the analysis start date (YYYY-MM-DD): ')
    if not validate_date(start_date):
        print('Invalid date. Please use YYYY-MM-DD format.')
        start_date = None

#
# Data
#

# Get Selic data
selic = sgs.get({'Selic': 432}, start=start_date)
# Get IPCA and IGP-M inflation data
inflation = sgs.get({'IPCA': 433, 'IGP-M': 189}, start=start_date)
# Get currency exchange rates for USD and EUR
currencies = currency.get(['USD', 'EUR'], start=start_date, end=date.today(), side='ask')

#
# Graph
#

# Use a custom Matplotlib style from 'financialgraphs.mplstyle'
plt.style.use('./mplstyles/financialgraphs.mplstyle')

# Create a subplot with three axes for different financial data
graphs, axes = plt.subplots(nrows=3, figsize=(14, 8), sharex=True)

# Plot Selic data on the first subplot
axes[0].plot(selic, label='Selic')
axes[0].yaxis.set_major_formatter(ticker.PercentFormatter())
axes[0].set_ylabel('Selic')
axes[0].legend(title=f'Current Selic: {selic["Selic"].iloc[-1]}')

# Plot IPCA and IGP-M inflation data on the second subplot
axes[1].plot(inflation['IPCA'], label='IPCA')
axes[1].plot(inflation['IGP-M'], label='IGP-M')
axes[1].yaxis.set_major_formatter(ticker.PercentFormatter())
axes[1].set_ylabel('Monthly Inflation Rate')
axes[1].legend(title=f'Last IPCA: {inflation["IPCA"].iloc[-2]}\nLast IGP-M: {inflation["IGP-M"].iloc[-1]}')

# Define a custom formatter for currency data
def brl_formatter(x, pos):
    return f'R${x:.2f}'

# Plot currency exchange rates for USD and EUR on the third subplot
axes[2].plot(currencies['USD'], label='USD')
axes[2].plot(currencies['EUR'], label='EUR')
axes[2].yaxis.set_major_formatter(brl_formatter)
axes[2].set_ylabel('Currencies')
axes[2].legend(title=f'Last USD: R$ {currencies["USD"].iloc[-1]:.2f}\nLast EUR: R$ {currencies["EUR"].iloc[-1]:.2f}')

# Add interactive annotations with cursor functionality
cursor = mplcursors.cursor()
@cursor.connect("add")
def on_add(sel):
    sel.annotation.get_bbox_patch().set(fc='gray', alpha=0.8)
    sel.annotation.get_bbox_patch().set_edgecolor('gray')
    sel.annotation.arrow_patch.set_color('white')
    sel.annotation.arrow_patch.set_arrowstyle('-')

# Display the plot
plt.show()
