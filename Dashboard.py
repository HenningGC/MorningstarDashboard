class Dashboard:
    def __init__(self, reference):
        self.df = None
        self.reference = reference
        self.allocation = dict()
        plt.style.use('seaborn-darkgrid')
        
        self.c = 0
        
    def _get_returns_data(self, x):
        
        return (np.log(x/x.shift(1))).cumsum()
    
    def get_mean_returns(self):
        m_rets = self.df.resample('Y').last().pct_change().mean()
        
        return m_rets.sort_values(ascending=False)
    
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
        divDf = None
        for asset in [col.split('_')[1] for col in portDf]:
            symbol = self.reference.loc[self.reference['Name'] == asset,'linkId'].iloc[0]
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
        
        if not 0.98 <= sum(weights) <= 1.01:
            raise NameError('Sum of weights has to be equal to 1')
            
        corr = self.df.corr()
        display(corr.style.background_gradient(cmap='coolwarm'))
                
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
        
        if divs is not None:
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
            display(revSum)
            display(revSum.groupby(revSum.index.year)['RevSum'].sum())
        
        revDf['Total Revenue'] = revDf.sum(axis=1)
        revDf['Total Revenue'].cumsum().plot()
        plt.title('Portfolio Cumulative Income')
        plt.show()
        
    
    def MPT(self, constraints):
        
        cov_matrix = self.df.pct_change().apply(lambda x: np.log(1+x)).cov()
        ind_er = self.df.resample('Y').last().pct_change().mean()
        ann_sd = self.df.pct_change().apply(lambda x: np.log(1+x)).std().apply(lambda x: x*np.sqrt(250))
        
        p_ret = [] # Define an empty array for portfolio returns
        p_vol = [] # Define an empty array for portfolio volatility
        p_weights = [] # Define an empty array for asset weights

        num_assets = len(self.df.columns)
        num_portfolios = 10000


        for portfolio in range(num_portfolios):
            weights = np.random.random(num_assets)
            weights = weights/np.sum(weights)
            p_weights.append(weights)
            returns = np.dot(weights, ind_er) # Returns are the product of individual expected returns of asset and its 
                                              # weights 
            p_ret.append(returns)
            var = cov_matrix.mul(weights, axis=0).mul(weights, axis=1).sum().sum()# Portfolio Variance
            sd = np.sqrt(var) # Daily standard deviation
            ann_sd = sd*np.sqrt(250) # Annual standard deviation = volatility
            p_vol.append(ann_sd)

        data = {'Returns':p_ret, 'Volatility':p_vol}
        
        
        for counter, symbol in enumerate(self.df.columns.tolist()):
            data[symbol+' weight'] = [w[counter] for w in p_weights]

        portfolios  = pd.DataFrame(data)
        min_vol_port = portfolios.iloc[portfolios['Volatility'].idxmin()]
        # idxmin() gives us the minimum value in the column specified.
        
        rf = 0.01 # risk factor
        optimal_risky_port = portfolios.iloc[((portfolios['Returns']-rf)/portfolios['Volatility']).idxmax()]
        
        plt.subplots(figsize=(10, 10))
        plt.scatter(portfolios['Volatility'], portfolios['Returns'],marker='o', s=10, alpha=0.3)
        plt.scatter(min_vol_port[1], min_vol_port[0], color='r', marker='*', s=500)
        plt.scatter(optimal_risky_port[1], optimal_risky_port[0], color='g', marker='*', s=500)
        
        plt.xlabel('Volatility')
        plt.ylabel('Returns')
        
        print('Minimum Volatility Portfolio: ')
        display(min_vol_port)
        print(min_vol_port.to_list()[2:])
        print('Maximum Sharpe Ratio Portfolio: ')
        display(optimal_risky_port)
        print(optimal_risky_port.to_list()[2:])
        
        
            
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
