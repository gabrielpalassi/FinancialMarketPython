from datetime import datetime, date
from bcb import sgs
from dateutil.relativedelta import relativedelta
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
print('- Currencies: The program also tracks the exchange rates of USD and EUR against the Brazilian Real (BRL).')
print('- IPCA (Índice Nacional de Preços ao Consumidor Amplo): IPCA represents the official inflation index in Brazil.')
print('- IGP-M (Índice Geral de Preços do Mercado): IGP-M is another important inflation index in Brazil.')
print('\n#----------------------------------------------------------------------------#\n')

#
# Inputs
#

start_date = None

def validate_date(input_date):
    try:
        # Check if the input matches the desired format (YYYY-MM-DD)
        parsed_date = datetime.strptime(input_date, '%Y-%m-%d')
        year, month, day = map(str, input_date.split('-'))
        if len(year) == 4 and len(month) == 2 and len(day) == 2:
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

while start_date is None:
    start_date = input('Please input the analysis start date (YYYY-MM-DD): ')
    if not validate_date(start_date):
        print('Invalid date. Please use YYYY-MM-DD format.')
        start_date = None

#
# Data
#

# Get data
selic = sgs.get({'Selic': 432}, start=start_date)
currencies = currency.get(['USD', 'EUR'], start=start_date, end=date.today(), side='ask')
ipca = sgs.get({'IPCA': 433}, start=start_date)
igpm = sgs.get({'IGP-M': 189}, start=start_date)

# Convert the start_date to a datetime object and subtract 11 months from the date
inflation_12m_start_date = datetime.strptime(start_date, "%Y-%m-%d")
inflation_12m_start_date = inflation_12m_start_date - relativedelta(months=11)
# Calculate the 12-month rolling inflation rates using a moving window approach and the previousl calculated inflation_12m_start_date.
ipca_12m = sgs.get({'IPCA': 433}, start=inflation_12m_start_date)
ipca_12m = ipca_12m.rolling(12).apply(lambda x: (1 + x / 100).prod() - 1).dropna() * 100
igpm_12m = sgs.get({'IGP-M': 189}, start=inflation_12m_start_date)
igpm_12m = igpm_12m.rolling(12).apply(lambda x: (1 + x / 100).prod() - 1).dropna() * 100

#
# Graph
#

plt.style.use('./mplstyles/financialgraphs.mplstyle')

graphs, axes = plt.subplots(4, figsize=(14, 8), sharex='col')

axes[0].plot(selic, label='Selic')
axes[0].yaxis.set_major_formatter(ticker.PercentFormatter())
axes[0].set_ylabel('Selic')
axes[0].legend(title=f'Current Selic: {selic["Selic"].iloc[-1]}')

def brl_formatter(x, pos):
    return f'R${x:.2f}'

axes[1].plot(currencies['USD'], label='USD')
axes[1].plot(currencies['EUR'], label='EUR')
axes[1].yaxis.set_major_formatter(brl_formatter)
axes[1].set_ylabel('Currencies')
axes[1].legend(title=f'Last USD: R$ {currencies["USD"].iloc[-1]:.2f}\nLast EUR: R$ {currencies["EUR"].iloc[-1]:.2f}')

axes[2].plot(ipca, label='IPCA')
axes[2].plot(igpm, label='IGP-M')
axes[2].yaxis.set_major_formatter(ticker.PercentFormatter())
axes[2].set_ylabel('Monthly Inflation')
axes[2].legend(title=f'Last IPCA: {ipca["IPCA"].iloc[-1]:.2f}\nLast IGP-M: {igpm["IGP-M"].iloc[-1]:.2f}')

axes[3].plot(ipca_12m, label='IPCA')
axes[3].plot(igpm_12m, label='IGP-M')
axes[3].yaxis.set_major_formatter(ticker.PercentFormatter())
axes[3].set_ylabel('12-month Rolling Inflation')
axes[3].legend(title=f'Last IPCA: {ipca_12m["IPCA"].iloc[-1]:.2f}\nLast IGP-M: {igpm_12m["IGP-M"].iloc[-1]:.2f}')

# Add interactive annotations with cursor functionality
cursor = mplcursors.cursor()
@cursor.connect("add")
def on_add(sel):
    sel.annotation.get_bbox_patch().set(fc='gray', alpha=0.8)
    sel.annotation.get_bbox_patch().set_edgecolor('gray')
    sel.annotation.arrow_patch.set_color('white')
    sel.annotation.arrow_patch.set_arrowstyle('-')

plt.show()
