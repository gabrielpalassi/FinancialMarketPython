from bcb import Expectativas
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import mplcursors

#
# Overview
#

print('\n#----------------------------- Program Overview -----------------------------#\n')
print('This program retrieves and graphs market expectations from the Brazilian Central Bank (BCB).')
print('- Selic (Sistema Especial de Liquidação e Custódia): Selic is the Brazilian Central Bank\'s benchmark interest rate.')
print('- Dollar (USD): Brazilian Real (BRL) x American Dollar (USD) exchange rate.')
print('- IPCA (Índice Nacional de Preços ao Consumidor Amplo): IPCA represents the official inflation index in Brazil.')
print('- IGP-M (Índice Geral de Preços do Mercado): IGP-M is another important inflation index in Brazil.')
print('\n#----------------------------------------------------------------------------#\n')

#
# Data
#

print('Downloading data...')

# Retrieve endpoint related to Selic interest rate expectations
selic_expectations = Expectativas().get_endpoint('ExpectativasMercadoSelic')

# Retrieve monthly market expectations data endpoint
monthly_expectations = Expectativas().get_endpoint('ExpectativaMercadoMensais')

# Retrive anual market expectations data endpoint
anual_expectations = Expectativas().get_endpoint('ExpectativasMercadoAnuais')

# Query and filter data for Selic interest rate
selic = (selic_expectations.query()
         .filter(selic_expectations.baseCalculo == '1')
         .select(selic_expectations.Data, selic_expectations.Reuniao, selic_expectations.Mediana)
         .orderby(selic_expectations.Data.asc())
         .collect())

# Query and filter data for IPCA inflation index
monthly_ipca = (monthly_expectations.query()
        .filter(monthly_expectations.Indicador == 'IPCA', monthly_expectations.baseCalculo == '1')
        .select(monthly_expectations.Data, monthly_expectations.DataReferencia, monthly_expectations.Mediana)
        .orderby(monthly_expectations.Data.asc())
        .collect())

anual_ipca = (anual_expectations.query()
        .filter(anual_expectations.Indicador == 'IPCA', anual_expectations.baseCalculo == '1')
        .select(anual_expectations.Data, anual_expectations.DataReferencia, anual_expectations.Mediana)
        .orderby(anual_expectations.Data.asc())
        .collect())

# Query and filter data for IGP-M inflation index
monthly_igpm = (monthly_expectations.query()
        .filter(monthly_expectations.Indicador == 'IGP-M', monthly_expectations.baseCalculo == '1')
        .select(monthly_expectations.Data, monthly_expectations.DataReferencia, monthly_expectations.Mediana)
        .orderby(monthly_expectations.Data.asc())
        .collect())
        
anual_igpm = (anual_expectations.query()
        .filter(anual_expectations.Indicador == 'IGP-M', anual_expectations.baseCalculo == '1')
        .select(anual_expectations.Data, anual_expectations.DataReferencia, anual_expectations.Mediana)
        .orderby(anual_expectations.Data.asc())
        .collect())

# Query and filter data for USD exchange rate
dollar = (monthly_expectations.query()
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

# Function to format anual expectations data
def format_anual_expectations(data):
    # Create a DataFrame from the input data
    dataframe = pd.DataFrame(data)
    # Find the latest expectation date in the 'Data' column
    lastest_expectation_date = dataframe['Data'].iloc[-1]
    # Filter the DataFrame to only include data for the latest expectation date
    dataframe = dataframe[dataframe['Data'] == lastest_expectation_date]
    # Convert the 'DataReferencia' column to datetime using the specified format (year)
    dataframe['DataReferencia'] = pd.to_datetime(dataframe['DataReferencia'], format='%Y')
    # Set the 'DataReferencia' column as the index of the DataFrame
    dataframe = dataframe.set_index('DataReferencia')
    # Drop the 'Data' column and return the formatted DataFrame
    return dataframe.drop(columns=['Data'])

# Apply formatting functions to the retrieved data
selic = format_selic_expectations(selic)
dollar = format_monthly_expectations(dollar)
monthly_ipca = format_monthly_expectations(monthly_ipca)
monthly_igpm = format_monthly_expectations(monthly_igpm)
anual_ipca = format_anual_expectations(anual_ipca)
anual_igpm = format_anual_expectations(anual_igpm)

#
# Graph
#

# Use a custom style for the graphs
plt.style.use('./mplstyles/financialgraphs.mplstyle')

# Create subplots for different graphs
graphs, axes = plt.subplots(2, 2, figsize=(14, 8))

# Plot Selic interest rate data
axes[0][0].plot(selic, label='Selic')
axes[0][0].yaxis.set_major_formatter(ticker.PercentFormatter())
axes[0][0].set_ylabel('Selic')
axes[0][0].legend()

# Define a custom formatter for the USD exchange rate
def brl_formatter(x, pos):
    return f'R${x:.2f}'

# Plot USD exchange rate data
axes[0][1].plot(dollar, label='USD')
axes[0][1].yaxis.set_major_formatter(brl_formatter)
axes[0][1].set_ylabel('Dollar (USD)')
axes[0][1].legend()

# Plot IPCA and IGP-M monthly inflation data
axes[1][0].plot(monthly_ipca, label='IPCA')
axes[1][0].plot(monthly_igpm, label='IGP-M')
axes[1][0].yaxis.set_major_formatter(ticker.PercentFormatter(decimals=2))
axes[1][0].set_ylabel('Monthly Inflation')
axes[1][0].legend()

# Convert the index of anual_ipca and anual_igpm to a list for plotting
years_ipca = anual_ipca.index.year.tolist()
years_igpm = anual_igpm.index.year.tolist()

# Define the bar width and an offset for the two datasets
bar_width = 0.3
bar_offset = bar_width / 2

# Plot IPCA and IGP-M anual inflation data with offset
axes[1][1].bar(np.array(years_ipca) - bar_offset, anual_ipca['Mediana'], width=bar_width, label='IPCA')
axes[1][1].bar(np.array(years_igpm) + bar_offset, anual_igpm['Mediana'], width=bar_width, label='IGP-M')
axes[1][1].yaxis.set_major_formatter(ticker.PercentFormatter(decimals=2))
axes[1][1].set_ylabel('Annual Inflation')
axes[1][1].legend()

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