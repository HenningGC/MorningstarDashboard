# Dashboard Class

The `Dashboard` class provides an easy way to analyze and visualize portfolio performance using historical data.

## Methods

### __init__(self, reference)

Initializes the `Dashboard` object with the given reference dataframe.

### _get_returns_data(self, x)

Calculates cumulative returns for a given time series `x`.

### get_mean_returns(self)

Calculates and returns the mean returns of the assets in the portfolio, sorted in descending order.

### _get_allocation(self, symbol)

Fetches allocation data for a given symbol from Morningstar and returns a dataframe with the allocation information.

### add_data(self, isins)

Adds historical price data for a list of ISINs to the `Dashboard` object.

### _get_number_assets(self, weights, initial_capital)

Calculates the number of assets to purchase for each asset in the portfolio based on given weights and initial capital.

### _get_dividends(self, portDf)

Fetches and returns dividend data for the assets in the portfolio.

### analyze_portfolio(self, weights, initial_capital, skip='No')

Analyzes the portfolio's performance and visualizes the following:
- Portfolio's equity curve
- Portfolio's dividends
- Annual dividend income
- Portfolio's cumulative income

### MPT(self, constraints)

Performs Modern Portfolio Theory (MPT) analysis to find the minimum volatility and maximum Sharpe ratio portfolios.

### visualize_data(self)

Visualizes the cumulative returns of the individual assets in the portfolio. The x-axis represents the date, and the y-axis represents the returns. This visualization helps users to understand the historical performance of each asset in the portfolio.

