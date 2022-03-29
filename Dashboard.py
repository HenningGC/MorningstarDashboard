import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
%matplotlib inline
import urllib.request, json
from datetime import datetime
import plotly
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import plotly.figure_factory as ff
from tqdm import tqdm
import requests
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup


class Dashboard:
    def __init__(self, reference):
        self.df = None
        self.reference = reference
        self.allocation = dict()
        
    def _get_returns_data(self, x):
        
        return (np.log(x/x.shift(1))).cumsum()
    
    def _get_allocation(self, symbol):
        
        req = Request(url=f'https://www.morningstar.es/es/funds/snapshot/snapshot.aspx?id={symbol}',headers={'user-agent':'my-app'})
        response = urlopen(req)
        html = BeautifulSoup(response, 'html')
        info_table = html.find_all(class_= "snapshotTextColor snapshotTextFontStyle snapshotTable overviewAssetAllocationTable")

        tipo = [result.findAll(class_='label') for result in info_table][0]
        tipo = [i.text for i in tipo]
        operacion = [result.findAll(class_='msBold') for result in info_table][0]
        operacion = [i.text for i in operacion]
        nums = [result.findAll(class_='value number') for result in info_table][0]
        nums = [i.text for i in nums]
        
        dicc = {'p largo': nums[::3], 'p corto': nums[1::3], 'p patrimonio': nums[2::3]}
        return pd.DataFrame(dicc, index = tipo)
              
    def add_data(self, isins):
        if not isinstance(isins, list):
            raise TypeError("data must be set to a list")
        
        localDf = pd.DataFrame()
        self.symbols = isins
        c = 0
        import datetime
        
        for symbol in set(self.symbols):
            with urllib.request.urlopen(f"https://tools.morningstar.es/api/rest.svc/timeseries_price/2nhcdckzon?id={symbol}%5D2%5D1%5D&currencyId=EUR&idtype=Morningstar&priceType=&frequency=daily&startDate=2000-10-07&endDate=2022-03-24&outputType=COMPACTJSON") as url:
                self.data = json.loads(url.read().decode())
            
            s_name = (self.reference).loc[self.reference['linkId'] == symbol, 'Name'].iloc[0]
            if c == 0:
                self.data = [ [datetime.datetime.fromtimestamp(i[0]/1000).strftime('%Y-%m-%d'),i[1]] for i in self.data]
                localDf = pd.DataFrame(self.data, columns = ['Date', f'Price_{s_name}'])
                localDf['Date'] = pd.to_datetime(localDf['Date'])
                localDf = localDf.set_index('Date')
                
                self.df = localDf
                #self.allocation[s_name] = self._get_allocation(symbol)
                c+= 1
                
            else:
                self.data = [ [datetime.datetime.fromtimestamp(i[0]/1000).strftime('%Y-%m-%d'),i[1]] for i in self.data]
                localDf = pd.DataFrame(self.data, columns = ['Date', f'Price_{s_name}'])
                localDf['Date'] = pd.to_datetime(localDf['Date'])
                localDf = localDf.set_index('Date')
                self.df = pd.concat([self.df, localDf], axis = 1)
                #self.allocation[s_name] = self._get_allocation(symbol)
                
        print(f'Successfuly added data for: {self.df.columns.to_list()}!')
                
    def revenue(self, revDf):
        pass
            
    def custom_portfolio(self, weights, initial_capital):
        
        if not isinstance(weights, list):
            raise TypeError("data must be set to a list")
        
        if len(weights) != len(self.df.columns):
            raise NameError('There has to be an equal amount of weights and assets')
        
        if sum(weights) != 1:
            raise NameError('Sum of weights has to equal to 1')
                
        retsDf = self.df.pct_change()
        
        x = 0
        for col in self.df.columns:
            retsDf[ (col.split('_')[1])+'_returns'] = retsDf[col]*weights[x]
            x += 1
            
        retsDf['PortfolioReturns'] = sum([retsDf[col] for col in retsDf.columns if '_returns' in col])
        
        retsDf['Equity Curve'] = ((retsDf['PortfolioReturns'] + 1).cumprod())*initial_capital

        retsDf['Equity Curve'].plot()
        plt.title('Portfolio Equity Curve')
        plt.show()
    
    def MPT(self, constraints):
        pass
            
    def visualize_data(self):
        
        cum_rets = (self.df).apply(self._get_returns_data)
        cum_rets.columns = [col.split('_')[1] for col in self.df.columns]
        
        ax = cum_rets.plot()
        ax.set_xlabel('Date')
        ax.set_ylabel('Returns')

        plt.title('Cumulative Returns')
        #plt.legend(loc='upper left', fontsize=12)
        plt.legend(bbox_to_anchor = (1.05, 0.6))
        #plt.tight_layout()
        plt.style.use('bmh')
        plt.grid(True)
        plt.show()
