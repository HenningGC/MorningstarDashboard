class Dashboard:
    def __init__(self, reference):
        self.df = None
        self.reference = reference
        self.allocation = dict()
        plt.style.use('seaborn-darkgrid')
        
        self.c = 0
        
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
        import datetime
        
        for symbol in set(self.symbols):
            with urllib.request.urlopen(f"https://tools.morningstar.es/api/rest.svc/timeseries_price/2nhcdckzon?id={symbol}%5D2%5D1%5D&currencyId=EUR&idtype=Morningstar&priceType=&frequency=daily&startDate=2000-10-07&endDate=2022-03-24&outputType=COMPACTJSON") as url:
                self.data = json.loads(url.read().decode())
            
            s_name = (self.reference).loc[self.reference['linkId'] == symbol, 'Name'].iloc[0]
            if self.c == 0:
                self.data = [ [datetime.datetime.fromtimestamp(i[0]/1000).strftime('%Y-%m-%d'),i[1]] for i in self.data]
                localDf = pd.DataFrame(self.data, columns = ['Date', f'Price_{s_name}'])
                localDf['Date'] = pd.to_datetime(localDf['Date'])
                localDf = localDf.set_index('Date')
                
                self.df = localDf
                #self.allocation[s_name] = self._get_allocation(symbol)
                self.c+= 1
                
            else:
                self.data = [ [datetime.datetime.fromtimestamp(i[0]/1000).strftime('%Y-%m-%d'),i[1]] for i in self.data]
                localDf = pd.DataFrame(self.data, columns = ['Date', f'Price_{s_name}'])
                localDf['Date'] = pd.to_datetime(localDf['Date'])
                localDf = localDf.set_index('Date')
                self.df = pd.concat([self.df, localDf], axis = 1)
                #self.allocation[s_name] = self._get_allocation(symbol)
                
        print(f'Successfuly added data for: {self.df.columns.to_list()}!')
        
    def _get_number_assets(self, weights, initial_capital):
        asset_list = [col for col in self.df.columns]
        
        capital_weights = dict()
        c = 0
        for asset in asset_list:
            initial_price = self.df[asset].loc[~self.df[asset].isnull()].iloc[0]
            n_assets = (initial_capital * weights[c]) // initial_price

            if n_assets >= 1:
                capital_weights[asset] = n_assets
            c+=1
        
        return capital_weights
    
    def _get_dividends(self, portDf):
        import datetime
        c = 0
        for asset in [col.split('_')[1] for col in portDf]:
            symbol = tD.reference.loc[tD.reference['Name'] == asset,'linkId'].iloc[0]
            with urllib.request.urlopen(f"https://tools.morningstar.es/api/rest.svc/timeseries_dividend/2nhcdckzon?id={symbol}%5D22%5D1%5D&idtype=Morningstar&frequency=monthly&timePeriod=200&outputType=COMPACTJSON") as url:
                data = json.loads(url.read().decode())
                if len(data) > 0:
                    if c == 0:
                        data = [ [datetime.datetime.fromtimestamp(i[0]/1000).strftime('%Y-%m-%d'),i[1]] for i in data]
                        localDf = pd.DataFrame(data, columns = ['Date', f'Dividends_{asset}'])
                        localDf['Date'] = pd.to_datetime(localDf['Date'])
                        localDf = localDf.set_index('Date')
                        divDf = localDf
                        c+=1
                    else:
                        data = [ [datetime.datetime.fromtimestamp(i[0]/1000).strftime('%Y-%m-%d'),i[1]] for i in data]
                        localDf = pd.DataFrame(data, columns = ['Date', f'Dividends_{asset}'])
                        localDf['Date'] = pd.to_datetime(localDf['Date'])
                        localDf = localDf.set_index('Date')
                        divDf = pd.concat([divDf, localDf], axis = 1)
                
        return divDf
    
    
            
    def analyze_portfolio(self, weights, initial_capital):
        
        if not isinstance(weights, list):
            raise TypeError("data must be set to a list")
        
        if len(weights) != len(self.df.columns):
            raise NameError('There has to be an equal amount of weights and assets')
        
        if sum(weights) != 1:
            raise NameError('Sum of weights has to equal to 1')
                
        retsDf = self.df.pct_change()
        capital_weight = self._get_number_assets(weights, initial_capital)
        
        x = 0
        for col in self.df.columns:
            retsDf[ (col.split('_')[1])+'_returns'] = retsDf[col]*weights[x]
            x += 1
            
        retsDf['PortfolioReturns'] = sum([retsDf[col] for col in retsDf.columns if '_returns' in col])
        
        retsDf['Equity Curve'] = ((retsDf['PortfolioReturns'] + 1).cumprod())*initial_capital
        
        revDf = pd.DataFrame()
        divs = self._get_dividends(self.df)
        
        for col in divs.columns:
            s_name = col.split('_')[1]
            if ('Price_'+col.split('_')[1]) in capital_weight.keys():
                revDf[f'Revenue_{s_name}'] = divs[col] * capital_weight['Price_'+ col.split('_')[1]]
                
                
        retsDf['Equity Curve'].plot()
        plt.title('Portfolio Equity Curve')
        plt.show()
        
        revDf.sum(axis=1).plot()
        #plt.bar(, revDf.sum(axis=1).index, revDf.sum(axis=1))
        plt.title('Portfolio Dividends')
        #plt.legend(bbox_to_anchor = (1.80, 0.6))
        plt.show()
        
        if len(revDf) > 0:
            revSum = pd.DataFrame()
            revSum['RevSum'] = revDf.sum(axis=1)
            revSum.groupby(revSum.index.year)['RevSum'].sum().plot()
            plt.title('Annual Dividend Income')
            plt.show()
            print(revSum)
            print(revSum.groupby(revSum.index.year)['RevSum'].sum())
        
        revDf['Total Revenue'] = revDf.sum(axis=1)
        revDf['Total Revenue'].cumsum().plot()
        plt.title('Portfolio Cumulative Income')
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
        plt.grid(True)
        plt.show()
