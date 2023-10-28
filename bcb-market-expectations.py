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

# Retrieve endpoints
selic_expectations = Expectativas().get_endpoint('ExpectativasMercadoSelic')
monthly_expectations = Expectativas().get_endpoint('ExpectativaMercadoMensais')
anual_expectations = Expectativas().get_endpoint('ExpectativasMercadoAnuais')

# Query and filter data
selic = (selic_expectations.query()
         .filter(selic_expectations.baseCalculo == '1')
         .select(selic_expectations.Data, selic_expectations.Reuniao, selic_expectations.Mediana)
         .orderby(selic_expectations.Data.asc())
         .collect())

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

dollar = (monthly_expectations.query()
         .filter(monthly_expectations.Indicador == 'Câmbio', monthly_expectations.baseCalculo == '1')
         .select(monthly_expectations.Data, monthly_expectations.DataReferencia, monthly_expectations.Mediana)
         .orderby(monthly_expectations.Data.asc())
         .collect())

def format_selic_expectations(data):
    dataframe = pd.DataFrame(data)

    # Filter the DataFrame to only include data for the latest expectation date
    lastest_expectation_date = dataframe['Data'].iloc[-1]
    dataframe = dataframe[dataframe['Data'] == lastest_expectation_date]

    # Split the 'Reuniao' column into two separate columns: 'ReuniaoNumber' and 'ReuniaoYear'
    dataframe[['ReuniaoNumber', 'ReuniaoYear']] = dataframe['Reuniao'].str.split('/', expand=True)
    dataframe['ReuniaoNumber'] = dataframe['ReuniaoNumber'].str.replace('R', '').astype(int)
    # Create a new 'DataReferencia' (copom meetings happen every 45 days and the first one is on the 31st of january)
    dataframe['DataReferencia'] = pd.to_datetime(dataframe['ReuniaoYear'] + '-01-31') + pd.to_timedelta((dataframe['ReuniaoNumber'] - 1) * 45, unit='D')
    
    # Create a copy of the DataFrame and adjust 'DataReferencia' by adding a time offset (selic should remain the same until next meeting)
    dataframe_copy = dataframe.copy()
    dataframe_copy['DataReferencia'] = dataframe_copy['DataReferencia'] + pd.to_timedelta(45, unit='D')
    dataframe_copy['DataReferencia'] = dataframe_copy['DataReferencia'].apply(lambda x: x.replace(day=31) if x.month == 1 else x)
    
    # Adjust the copied DataFrame's indices to create alternating rows (doubling the index)
    dataframe.index = dataframe.index * 2
    dataframe_copy.index = (dataframe_copy.index * 2) + 1
    dataframe = pd.concat([dataframe, dataframe_copy])

    dataframe = dataframe.sort_index()
    dataframe = dataframe.set_index('DataReferencia')
    return dataframe.drop(columns=['Data', 'Reuniao', 'ReuniaoNumber', 'ReuniaoYear'])

def format_expectations(data, type):
    dataframe = pd.DataFrame(data)

    # Filter the DataFrame to only include data for the latest expectation date
    lastest_expectation_date = dataframe['Data'].iloc[-1]
    dataframe = dataframe[dataframe['Data'] == lastest_expectation_date]

    # Convert the 'DataReferencia' column to datetime using the specified format
    if type == 'monthly':
        dataframe['DataReferencia'] = pd.to_datetime(dataframe['DataReferencia'], format='%m/%Y')
    elif type == 'anual':
        dataframe['DataReferencia'] = pd.to_datetime(dataframe['DataReferencia'], format='%Y')

    dataframe = dataframe.set_index('DataReferencia')
    return dataframe.drop(columns=['Data'])

selic = format_selic_expectations(selic)
dollar = format_expectations(dollar, 'monthly')
monthly_ipca = format_expectations(monthly_ipca, 'monthly')
monthly_igpm = format_expectations(monthly_igpm, 'monthly')
anual_ipca = format_expectations(anual_ipca, 'anual')
anual_igpm = format_expectations(anual_igpm, 'anual')

#
# Graph
#

plt.style.use('./mplstyles/financialgraphs.mplstyle')

graphs, axes = plt.subplots(2, 2, figsize=(14, 8))

axes[0][0].plot(selic, label='Selic')
axes[0][0].yaxis.set_major_formatter(ticker.PercentFormatter())
axes[0][0].set_ylabel('Selic')
axes[0][0].legend()

def brl_formatter(x, pos):
    return f'R${x:.2f}'

axes[0][1].plot(dollar, label='USD')
axes[0][1].yaxis.set_major_formatter(brl_formatter)
axes[0][1].set_ylabel('Dollar (USD)')
axes[0][1].legend()

axes[1][0].plot(monthly_ipca, label='IPCA')
axes[1][0].plot(monthly_igpm, label='IGP-M')
axes[1][0].yaxis.set_major_formatter(ticker.PercentFormatter(decimals=2))
axes[1][0].set_ylabel('Monthly Inflation')
axes[1][0].legend()

# Convert the index of anual_ipca and anual_igpm to a list for plotting in bars
years_ipca = anual_ipca.index.year.tolist()
years_igpm = anual_igpm.index.year.tolist()

# Define the bar width and an offset for the bars graph
bar_width = 0.3
bar_offset = bar_width / 2

# Plot IPCA and IGP-M anual inflation data with offset to avoid bars overlapping
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

plt.show()