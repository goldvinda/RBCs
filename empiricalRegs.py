#If fancy python execution rather than ipynb

import pandas as pd  # For data manipulation
import numpy as np  # For matrices handling
import requests  # For API interaction
import statsmodels.api as sm # For HP filtering 

#Environment definition. OECD is the binding restriction for the data. 
variables = {"GDP": "GDP+B1_GE", "C": "P31S14_S15", "Cg": "P3S13", "X": "P6", "M": "P7", "I": "P51"}
dates = {"start": "2003-Q1", "end": "2022-Q3"}
countries = ["MEX","KOR","TUR","SVK","CAN","NOR","ESP","NZL"]
data = {}

#API endpoint interaction, We will work with data from Mexico and Canada, 1980 to 2022, quarterly. Check for sources.
for country in countries:

    #Create an empty DataFrame for each country of interest.
    data[country] = pd.DataFrame(columns=["DATE","GDP", "C", "X", "M", "NX", "I"])

    for key in variables:
        #Seek the variables of interest in the OECD API!
        api_url = f'http://stats.oecd.org/sdmx-json/data/QNA/{country}.{variables[key]}.VPVOBARSA.Q/all?startTime={dates["start"]}&endTime={dates["end"]}&dimensionAtObservation=allDimensions'
        response = requests.get(api_url)
        # Variables are: Output, Household Consumption (excl. Gov consumption), or private consumption Investment (as gross fixed capital accumulation), Net exports (X-M). Create them from this datapoint.
        data[country]["ln_"+key] = list(map(lambda i: np.log(response.json()["dataSets"][0]["observations"][i][0]) ,response.json()["dataSets"][0]["observations"]))
        data[country][key] = list(map(lambda i: response.json()["dataSets"][0]["observations"][i][0] ,response.json()["dataSets"][0]["observations"]))
        # Filterred of the series using HP 1600, (robust check with band pass freqs btw 6 and 32
        data[country][key+"_cycle"],data[country][key+"_trend"]  = sm.tsa.filters.hpfilter(data[country]["ln_"+key], 1600)
    
    #Net Exports (X-M)
    data[country]["NX"] = data[country]["X"] - data[country]["M"]
    data[country]["NXGDP"] = data[country]["NX"] / data[country]["GDP"]
    
    #Just for robusticity, set DATE accordingly.
    data[country]["DATE"] = list(map(lambda i: i["id"], response.json()["structure"]["dimensions"]["observation"][4]['values']))
    data[country] = data[country].set_index("DATE")
    
    #volatility of output filtered
    data[country]["sigma_GDP"] = data[country]["GDP_cycle"].std()
    
    #volatility of first diff of unfiltered log output
    data[country]["sigma_deltaGDP"] = data[country]["GDP_cycle"].diff().std()
    
    #Autocorrelation filtered output vs t-1
    data[country]["rho_GDP_GDP-1"] = data[country]["GDP_cycle"].autocorr(lag=1)
    
    #Autocorrelation unfiltered diff vs t-1    
    data[country]["rho_deltaGDP_deltaGDP-1"] = data[country]["GDP_cycle"].diff().autocorr(lag=1)
    
    #Ratio of volatility of filtered c/gdp
    data[country]["sigma_C/sigma_GDP"] = data[country]["C_cycle"].std() / data[country]["GDP_cycle"].std()
    
    #Ratio of volatility of filtered I/gdp
    data[country]["sigma_I/sigma_GDP"] = data[country]["I_cycle"].std() / data[country]["GDP_cycle"].std()
    
    #Volatility of ratio NX/gdp
    data[country]["sigma_NXGDP"] = data[country]["NXGDP"].std()
    
    #Autocorrelation c,gdp
    data[country]["rho_C_GDP"] = data[country]["GDP_cycle"].corr(data[country]["C_cycle"])
    
    #Autocorrelation I,gdp
    data[country]["rho_I_GDP"] = data[country]["GDP_cycle"].corr(data[country]["I_cycle"])
    
    #Autocorrelation NX/Y,Y
    data[country]["rho_NY/Y_GDP"] = data[country]["GDP_cycle"].corr(data[country]["NXGDP"])

# Exporting tables for authors contributions
with pd.ExcelWriter('data.xlsx') as writer:
    for sheet_name, df in data.items():
        df.to_excel(writer, sheet_name)