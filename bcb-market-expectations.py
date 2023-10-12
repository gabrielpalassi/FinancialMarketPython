from bcb import Expectativas
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import mplcursors

#
# Overview
#

print('\n#----------------------------- Program Overview -----------------------------#\n')
print('This program retrieves and graphs market expectations from the Brazilian Central Bank (BCB).')
print('- Selic (Sistema Especial de Liquidação e Custódia): Selic is the Brazilian Central Bank\'s benchmark interest rate.')
print('- IPCA (Índice Nacional de Preços ao Consumidor Amplo): IPCA represents the official inflation index in Brazil.')
print('- IGP-M (Índice Geral de Preços do Mercado): IGP-M is another important inflation index in Brazil.')
print('- Dolar (USD): Brazilian Real (BRL) x American Dolar (USD) exchange rate.')
print('\n#----------------------------------------------------------------------------#\n')

#
# Data
#

print('Downloading data...')

# Retrieve endpoint related to Selic interest rate expectations
selic_expectations = Expectativas().get_endpoint('ExpectativasMercadoSelic')

# Retrieve monthly market expectations data endpoint
monthly_expectations = Expectativas().get_endpoint('ExpectativaMercadoMensais')

# Query and filter data for Selic interest rate
selic = (selic_expectations.query()
         .filter(selic_expectations.baseCalculo == '1')
         .select(selic_expectations.Data, selic_expectations.Reuniao, selic_expectations.Mediana)
         .orderby(selic_expectations.Data.asc())
         .collect())

# Query and filter data for IPCA inflation index
ipca = (monthly_expectations.query()
        .filter(monthly_expectations.Indicador == 'IPCA', monthly_expectations.baseCalculo == '1')
        .select(monthly_expectations.Data, monthly_expectations.DataReferencia, monthly_expectations.Mediana)
        .orderby(monthly_expectations.Data.asc())
        .collect())

# Query and filter data for IGP-M inflation index
igpm = (monthly_expectations.query()
        .filter(monthly_expectations.Indicador == 'IGP-M', monthly_expectations.baseCalculo == '1')
        .select(monthly_expectations.Data, monthly_expectations.DataReferencia, monthly_expectations.Mediana)
        .orderby(monthly_expectations.Data.asc())
        .collect())

# Query and filter data for USD exchange rate
dolar = (monthly_expectations.query()
         .filter(monthly_expectations.Indicador == 'Câmbio', monthly_expectations.baseCalculo == '1')
         .select(monthly_expectations.Data, monthly_expectations.DataReferencia, monthly_expectations.Mediana)
         .orderby(monthly_expectations.Data.asc())
         .collect())

# Function to format Selic expectations data
def format_selic_expectations(data):
    # Create a DataFrame from the input data
    dataframe = pd.DataFrame(data)
    # Find the latest expectation date in the 'Data' column
    lastest_expectation_date = dataframe['Data'].iloc[-1]
    # Filter the DataFrame to only include data for the latest expectation date
    dataframe = dataframe[dataframe['Data'] == lastest_expectation_date]
    # Split the 'Reuniao' column into two separate columns: 'ReuniaoNumber' and 'ReuniaoYear'
    dataframe[['ReuniaoNumber', 'ReuniaoYear']] = dataframe['Reuniao'].str.split('/', expand=True)
    # Remove the 'R' character and convert 'ReuniaoNumber' to integers
    dataframe['ReuniaoNumber'] = dataframe['ReuniaoNumber'].str.replace('R', '').astype(int)
    # Create a new 'DataReferencia' (copom meetings happen every 45 days and the first one is on the 31st of january)
    dataframe['DataReferencia'] = pd.to_datetime(dataframe['ReuniaoYear'] + '-01-31') + pd.to_timedelta((dataframe['ReuniaoNumber'] - 1) * 45, unit='D')
    # Create a copy of the DataFrame and adjust 'DataReferencia' by adding a time offset (selic should remain the same until next meeting)
    dataframe_copy = dataframe.copy()
    dataframe_copy['DataReferencia'] = dataframe_copy['DataReferencia'] + pd.to_timedelta(45, unit='D')
    # Adjust 'DataReferencia' to replace the day with 31 if the month is january (first meeting is always on the 31st of january)
    dataframe_copy['DataReferencia'] = dataframe_copy['DataReferencia'].apply(lambda x: x.replace(day=31) if x.month == 1 else x)
    # Adjust the DataFrame's indices to create alternating rows (doubling the index)
    dataframe.index = dataframe.index * 2
    dataframe_copy.index = (dataframe_copy.index * 2) + 1
    # Concatenate the original and adjusted DataFrames to create a single DataFrame
    dataframe = pd.concat([dataframe, dataframe_copy])
    # Sort the DataFrame by index and set 'DataReferencia' as the new index
    dataframe = dataframe.sort_index()
    dataframe = dataframe.set_index('DataReferencia')
    # Drop unnecessary columns and return the formatted DataFrame
    return dataframe.drop(columns=['Data', 'Reuniao', 'ReuniaoNumber', 'ReuniaoYear'])


# Function to format monthly expectations data
def format_monthly_expectations(data):
    # Create a DataFrame from the input data
    dataframe = pd.DataFrame(data)
    # Find the latest expectation date in the 'Data' column
    lastest_expectation_date = dataframe['Data'].iloc[-1]
    # Filter the DataFrame to only include data for the latest expectation date
    dataframe = dataframe[dataframe['Data'] == lastest_expectation_date]
    # Convert the 'DataReferencia' column to datetime using the specified format (month/year)
    dataframe['DataReferencia'] = pd.to_datetime(dataframe['DataReferencia'], format='%m/%Y')
    # Set the 'DataReferencia' column as the index of the DataFrame
    dataframe = dataframe.set_index('DataReferencia')
    # Drop the 'Data' column and return the formatted DataFrame
    return dataframe.drop(columns=['Data'])


# Apply formatting functions to the retrieved data
selic = format_selic_expectations(selic)
ipca = format_monthly_expectations(ipca)
igpm = format_monthly_expectations(igpm)
dolar = format_monthly_expectations(dolar)

#
# Graph
#

# Use a custom style for the graphs
plt.style.use('./mplstyles/financialgraphs.mplstyle')

# Create subplots for different graphs
graphs, axes = plt.subplots(nrows=3, figsize=(14, 8), sharex=True)

# Plot Selic interest rate data
axes[0].plot(selic, label='Selic')
axes[0].yaxis.set_major_formatter(ticker.PercentFormatter())
axes[0].set_ylabel('Selic')
axes[0].legend()

# Plot IPCA and IGP-M inflation data
axes[1].plot(ipca, label='IPCA')
axes[1].plot(igpm, label='IGP-M')
axes[1].yaxis.set_major_formatter(ticker.PercentFormatter(decimals=2))
axes[1].set_ylabel('Monthly Inflation Rate')
axes[1].legend()

# Define a custom formatter for the USD exchange rate
def brl_formatter(x, pos):
    return f'R${x:.2f}'

# Plot USD exchange rate data
axes[2].plot(dolar, label='USD')
axes[2].yaxis.set_major_formatter(brl_formatter)
axes[2].set_ylabel('Dolar (USD)')
axes[2].legend()

# Enable cursor interaction with the graphs
cursor = mplcursors.cursor()
@cursor.connect("add")
def on_add(sel):
    sel.annotation.get_bbox_patch().set(fc='gray', alpha=0.8)
    sel.annotation.get_bbox_patch().set_edgecolor('gray')
    sel.annotation.arrow_patch.set_color('white')
    sel.annotation.arrow_patch.set_arrowstyle('-')

# Display the graphs
plt.show()