import pandas as pd
import numpy as np

def drawdown(return_series: pd.Series):
    """
    Takes a time series of asset returns
    Computes and returns a DataFrame that contains:
    the wealth index
    the previous peaks
    percent drawdowns
    """
    wealth_index = 1000*(1+return_series).cumprod()
    previous_peaks = wealth_index.cummax()
    drawdowns = (wealth_index - previous_peaks)/previous_peaks
    
    return pd.DataFrame({
        "Wealth": wealth_index,
        "Peaks": previous_peaks,
        "Drawdown": drawdowns
    })

def get_ffme_returns():

    me_m = pd.read_csv("data/Portfolios_Formed_on_ME_monthly_EW.csv",
                     header = 0, index_col=0, parse_dates=True, 
                      na_values=-99.99)

    rets = me_m[["Lo 10", "Hi 10"]]/100
    rets.columns = ["SmallCap", 'LargeCap']

    rets.index = pd.to_datetime(rets.index, format="%Y%m").to_period('M')

    return rets

def get_hfi_returns():
    """
    Load and format the EDHEC Hedge Fund Index Returns
    """
    hfi = pd.read_csv("data/edhec-hedgefundindices.csv",
                header=0, index_col=0, parse_dates=True)
    hfi = hfi/100
    hfi.index = hfi.index.to_period("M")

    return hfi

def skewness(r): 
    """
    Alternative to sicpy.stats.skew()
    Computes the skewness of the supplied Series or DataFrame 
    Returns a float or a Series
    """
    demeaned_r = r - r.mean()
    # use the population standard deviation, so set dof=0
    sigma_r = r.std(ddof=0)
    exp = (demeaned_r**3).mean()
    return exp/sigma_r**3

def kurtosis(r): 
    """
    Alternative to sicpy.stats.kurtosis()
    Computes the kurtosis of the supplied Series or DataFrame 
    Returns a float or a Series
    """
    demeaned_r = r - r.mean()
    # use the population standard deviation, so set dof=0
    sigma_r = r.std(ddof=0)
    exp = (demeaned_r**4).mean()
    return exp/sigma_r**4

import scipy
def is_normal(r, level = 0.01):
    """
    Applies the Jarque-Bera test to determine if a Series is normal or not 
    Test is applied at the 1% level by default 
    Returns True if the Hypothesis of normality is accepte, False otherwise.
    """
    statistic, p_value = scipy.stats.jarque_bera(r)
    return p_value>level

def semideviation(r):
    """
    Returns the semideviation aka negative semideviation of r
    r must be a Serie or a DataFrame
    """
    return r[r<0].std(ddof=0)

def var_historic(r, level=5):
    """ 
    Returns the historic Value at Risk at a specified level 
    i.e. returns the number such that "level" percent of returns 
    fall below that number, and the (100 - level) percent are above
    """
    if isinstance(r, pd.DataFrame):
        return r.aggregate(var_historic, level=level)
    elif isinstance(r, pd.Series):
        return -np.percentile(r, level)
    else:
        raise TypeError("Expected r to be Series or DataFrame")

from scipy.stats import norm 
def var_gaussian(r,level=5, modified=False):
    """
    Returns the Paremetric Gaussian VaR of Series or DataFrames
    """
    #Computes the Z - normal score
    z = norm.ppf(level/100)

    if modified:#Computes the Cornish-Fisher modified Score 
        s = skewness(r)
        k = kurtosis(r)
        z = (z + 
                (z**2-1)/6 + 
                (z**3 -3*z)*(k-3)/24 - 
                (2*z**3-5*z)*(s**2)/36
            )

    return -1*(r.mean()+z*r.std(ddof=0))

def cvar_historic(r, level=5):
    """
    Computes the Conditional VaR of Series or DataFrame
    """
    if isinstance(r, pd.Series):
        is_beyond = (r <= -var_historic(r, level=level))
        return -r[is_beyond].mean()

    elif isinstance(r, pd.DataFrame):
        return r.aggregate(cvar_historic, level=level)
    else:
        raise TypeError("Expected r to be a Series or a DataFrame")