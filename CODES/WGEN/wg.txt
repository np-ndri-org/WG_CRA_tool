# -*- coding: utf-8 -*-
"""
Created on Thu May 23 10:44:02 2019

@author: dibes
Dibesh Shrestha, dibeshshrestha@live.com
Divas B.Basnyat,Ph.D, divas@ndri.org.np
Nepal Development Research Institue

This is for the development of multisite multivariate weathergenerator based on
paper -
Apipattanavis, S., G. Podesta´, B. Rajagopalan, and R. W. Katz (2007),
A semiparametric multivariate and multisite weather generator, Water Resour. Res., 43,
W11401, doi:10.1029/2006WR005714

Steinschneider, S., and C. Brown (2013), A semiparametric multivariate,
multisite weather generator with low-frequency variability for use in climate risk assessments,
Water Resour. Res., 49, 7205–7220, doi:10.1002/wrcr.20528.

"""

#defining class for precipitation series

#DTS is Daily Time Series
import os
import pandas as pd
import numpy as np
from datetime import datetime
import random
import calendar
#import time
from scipy.stats import gamma

class WeatherDTS(object):
    def __init__(self,data, name, precipitation_column_name = 'precip', var_dict = {}):
        """Initialisation
        data: pandas dataframe with 'Date' columns with other varaibles columns
            main data file that contains
            either area average values of weather variables for entire basin in case of multisite
            or values of weather variables for single site station
            If 'data' dataframe make sure that 'Date' is not an index.
            Index of data are simple numbering starting from 0 as python indexing.
            This is also the case for variables in var_data.
        name: python string
            Name of the data like station name etc
        precipitation_column_name: python string
            Name of data column that represents precipitation
        var_dict:
            (a) If case of single site this is {}.
            (b) In case of multisite:
                It is python dictionary in which key is varaible name and
                value is pandas dataframe for multisite for that variable.
                Each pandas dataframe contains only one type of weather variable
                Eg: var_dict = {'precip': pd_precip,
                                'tmax': pd_tmax}
                where 'pd_precip' dataframe consists of multisite precipitation data
                Eg of pd_precip:
                ---------------------------------
                     Date        p1   p2   p3
                 0  1980-01-01   0.20 0.50 0.50
                 1  1980-01-02   0.10 5.20 9.60
                ---------------------------------
                where p1, p2 and p3 are stations.
        It is assumed that the Date of observations for observations in data and
        var_data variables are same. If not, it will follow Date of data.
        """

        self.udata = data.copy() #Data to be used for further computation
        self.name = name
        self.precipitation_column = precipitation_column_name;
        # Length of observations in data and var_data must be same.
        # So,checking for that
        if len(var_dict) != 0:
            length_var_data = [len(x) for x in var_dict.values()]
            if len(set(length_var_data)) != 1:
                raise ValueError('Length of observations within var_data mismatch!')
            else:
                if len(data.index) != length_var_data[0]:
                    raise ValueError('Length of observations of data and var_data mismatch!')

        self.var_dict = var_dict.copy()

        # Check if the date, year and day has been computed in data
        # If not, then compute
        if 'Date' not in self.udata.columns:
            raise KeyError("'Date' not present in dataframe")
        elif self.udata['Date'].dtypes != 'datetime64[ns]':
            raise TypeError("Must be of numpy ''datetime64[ns]' type")

        if 'year' not in self.udata.columns:
            self.udata['year'] = self.udata['Date'].dt.year
        if 'month' not in self.udata.columns:
            self.udata['month'] = self.udata['Date'].dt.month
        if 'day' not in self.udata.columns:
            self.udata['day'] = self.udata['Date'].dt.day

        # Other variables to store the simulated results
        self.sim_results = None

    def getData(self):
        """ returns the data """
        return self.udata.copy()

    def updateData(self, updatedData):
        """ updates the data """
        self.udata = updatedData

    def genResampledTimeSeries(self,column,whichone):
        """ Generate the time series as required.
        Inputs:
            column
            whichone : string
                options are:
                    'Daily', 'Annual sum', 'Annual mean',
                    'Monthly sum', 'Monthly mean',
                    'AverageMonthly(sums)','AverageMonthly(means)'

        """
        D1 =self.getData()
        D1.drop_duplicates('Date',inplace = True)
        D1.index = D1['Date']

        if whichone == 'Daily':
            Y = D1
        elif whichone == 'Annual sum':
            Y = D1.resample('1Y').sum()
        elif whichone == 'Annual mean':
            Y = D1.resample('1Y').mean()
        elif whichone == 'Monthly sum':
            Y = D1.resample('1M').sum()
        elif whichone == 'Monthly mean':
            Y = D1.resample('1M').mean()
        elif whichone == 'AverageMonthly(sums)':
            Y1 = D1.groupby(['year','month']).sum()
            Y = Y1.groupby(['month']).mean()
        elif whichone == 'AverageMonthly(means)':
            Y1 = D1.groupby(['year','month']).mean()
            Y = Y1.groupby(['month']).mean()
        else:
            raise KeyError(" 'whichone' is not defined")
        return Y[[column]]

    def genYearlySumSeries(self,column):
        D1 = self.getData()
        D1.drop_duplicates('Date',inplace = True)
        D1.index = D1['Date']
        Y = D1.resample('1Y').sum()
        return Y[[column]]

    def genYearlyMeanSeries(self,column):
        D1 = self.getData()
        D1.drop_duplicates('Date',inplace = True)
        D1.index = D1['Date']
        Y = D1.resample('1Y').mean()
        return Y[[column]]

    def genMonthlySumSeries(self,column):
        D1 = self.getData()
        D1.drop_duplicates('Date',inplace = True)
        D1.index = D1['Date']
        Y = D1.resample('1M').sum()
        return Y[[column]]

    def genMonthlyMeanSeries(self,column):
        D1 = self.getData()
        D1.drop_duplicates('Date',inplace = True)
        D1.index = D1['Date']
        Y = D1.resample('1M').mean()
        return Y[[column]]

    def genAverageMonthlySumSeries(self,column):
        D1 = self.getData()
        D1.drop_duplicates('Date',inplace = True)
        Y = D1.groupby(['year','month']).sum()
        Y1 = Y.groupby(['month']).mean()
        return Y1[[column]]

    def genAverageMonthlyMeanSeries(self,column):
        D1 = self.getData()
        D1.drop_duplicates('Date',inplace = True)
        Y = D1.groupby(['year','month']).mean()
        Y1 = Y.groupby(['month']).mean()
        return Y1[[column]]

    def setNoStates(self,nostates = 3):
        """Sets the number of states
            Input:
                nostates: number of precipitation states (2 or 3)
                Default is 3.
        """
        if nostates not in [2,3]:
            raise ValueError('Number of states must be either 2 or 3')
        self.nstates = nostates

    def getNoStates(self):
        """ returns number of states (either 2 or 3)"""
        if self.nstates == None:
            raise ValueError('Number of states in not defined yet.')
        return self.nstates

    def setWetThreshold(self,wet_threshold_value=0.1):
        """ sets the wet threshold value (in units of precipitation).
        It is the value to seperate wet and dry condition.
        dry condition: condition when precipitation < wet_threshold_value
        wet condition: condition when precipitation >= wet_threshold_value
        Input:
            wet_threshold_value
            Default is 0.1 mm."""
        self.wet_threshold = wet_threshold_value

    def getWetThreshold(self):
        """ returns the wet threshold value if exists """
        if self.wet_threshold == None:
            raise ValueError('Wet Threshold value not defined yet.')
        return self.wet_threshold

    def setExtremeThreshold(self,extreme_threshold_value = 0.8):
        """ sets the extreme threshold value (in percentile).
        It is the value to seperate extremely wet condition from wet condition.
        Only applicable if number of states is 3.
        dry condition: condition when precipitation < wet_threshold_value
        wet condition: condition when precipitation >= wet_threshold_value and
                                      precipitation < extreme_threshold_value
        extremely wet condition: condition when precipitation >= extreme_threshold_value
        Input:
            extrement_threshold_value
            Default value is 0.8 (80th percentile)"""
        if not 0 < extreme_threshold_value <= 1:
            raise ValueError('Should be between 0 (exclusive) and 1(inclusive)')
        self.extreme_threshold = extreme_threshold_value

    def getExtremeThreshold(self):
        """ returns the extreme threshold value if exists """
        if self.extreme_threshold == None:
            raise ValueError('Extreme Threshold value not defined yet.')
        return self.extreme_threshold

    def findYearsDTS(self):
        """ Find the years in the data- (which years are in the data)
            dailyTS is daily time series (which is udata)
            dailyTS must have 'year' column"""
        try:
            return self.years_in_series
        except:
            dailyTS = self.getData()
            s = dailyTS['year'][0]
            years_in_series = [s]
            for i in dailyTS['year']:
                if s != i:
                    years_in_series.append(i)
                    s = i
            self.years_in_series = years_in_series
            return self.years_in_series

    def computeExtThresVals(self, column):
        """Computes the threshold values for each of the month for the given
        extreme precentile value (in fraction)
        dailyTS must have year, month and day columns computed
        from Date
        Note: This is only used when the number of states is 3
        Syntax:
            compute_extreme_threshold(dailyTS, extreme_threshold = 0.8)
        Input:
            dailyTS = daily time series with the 'precip' column
            extreme_threshold = fractional value of the percentile
        Output:
            extreme threshold values for the given months in python list
            of length 12
        """
        # This is computed when the number of the states  = 3
        try:
            return self.extreme_threshold_values
        except:
            dailyTS = self.getData();
            try:
                extreme_threshold = self.getExtremeThreshold()
            except:
                raise KeyError("Extreme Threshold percentile value not found")
            v = dailyTS[dailyTS[column] >= self.wet_threshold].copy()
            u = v.groupby(['month']).quantile(extreme_threshold)
            self.extreme_threshold_values = list(round(u[column],2))
            return self.extreme_threshold_values

    def gen_state_series(self,column, statecolumnname = 'state'):
        """ This will generate state series and add in into the daily TS.
        dry conditions is 0
        wet condition is 1
        and extremely wet condtion is 2
        Input:
            dailyTS : daily time series with column = 'precip'
            nstates : no of states (either 2 or 3)
            wet_threshold: threshold to seperate the precipitation as wet or dry
            extreme_threshold : percentile value in fraction to seperate the
                                extremely wet condition
        **kwargs is used only when number of states is 3
        In case of **kwargs,
            extreme_threshold = value

        Output:
            dailyTS with Added column 'state' with statecolumnname
        """
        dailyTS = self.getData();
        try:
            nstates = self.getNoStates();
        except:
            raise KeyError("No of states is not defined yet")
        try:
            wet_threshold = self.getWetThreshold();
        except:
            raise KeyError("Wet Threshold is not defined yet")

        sn = statecolumnname
        dailyTS[sn] = 0 #dailyTS.loc[:,column]
        dailyTS.loc[dailyTS[column] < wet_threshold, sn ] = 0;
        if nstates == 2:
            dailyTS.loc[dailyTS[column] >= wet_threshold, sn ] = 1;
        elif nstates == 3:
            ext_thres = self.computeExtThresVals(column)
            for mn in range(1,13):
                idx = mn-1
                dailyTS.loc[((dailyTS[column] >= wet_threshold) & \
                              (dailyTS[column] < ext_thres[idx]) & \
                              (dailyTS['month'] == mn)), sn] = 1
                dailyTS.loc[((dailyTS[column] >= wet_threshold) & \
                              (dailyTS[column] >= ext_thres[idx]) & \
                              (dailyTS['month'] == mn)), sn] = 2
        self.statecolumnname = statecolumnname;
        self.updateData(dailyTS)

    def getStateColumnName(self):
        try:
            return self.statecolumnname
        except:
            self.gen_state_series(self.precipitation_column)
            return self.statecolumnname

    def transitionStateCounter(self,pdseries):
        """This is a helper function.
            Counts the number of state transitions for various states
            pdseries is the panda series with 'state' column
            nstates is the number of states
            Input:
                pdseries: panda series that has the 'state' column

                Internally defined inputs:
                    nstates: number of states
                    pdcolumn: is the column in pandas that has state values
                           default is 'state'
            Output:
                returns the list with transition numbers according to the
                number of states
                if nstates is 2:
                ['n00','n01','n10','n11','N0','N1']
                if nsates is 3:
                ['n00','n01','n02','n10','n11','n12','n20','n21','n22','N0','N1','N2']
        """
        nstates = self.getNoStates();
        pdcolumn = self.getStateColumnName();

        n = [[0 for j in range(nstates)] for i in range(nstates)]
        N = [0 for i in range(nstates)]
        for st0 in range(nstates):
            for st1 in range(nstates):
                for i in range(len(pdseries[pdcolumn])-1):
                    states= (st0,st1)
                    states_to_check = (pdseries.iloc[i][pdcolumn], pdseries.iloc[i+1][pdcolumn])
                    if states_to_check == states:
                        n[st0][st1] += 1
                        if pdseries.iloc[i][pdcolumn] == st0:
                            N[st0] += 1
        nlist =[]
        for i in range(nstates):
            for j in range(nstates):
                nlist.append(n[i][j])
        # returns the transition number list
        return nlist + N

    def transitionStateNumber(self):
        """This function will compute the total number of transtions from one state
        to another for all the months and years in dailyTS series.
        Syntax: transititonStateNumber(daily, nstates)
        Input:
            dailyTS: dailyTS data with 'state' column = statecolumn
                     computed (using gen_state_series function)
            nstates: number of states
            statecolumn: specifying which column is the state column
        Output:
            dataframe with the number of transitions computes
            header will be as follows:
            When nstates = 2:
            ['year','month','n00','n01','n10','n11','N0','N1']
            When nstates = 3:
            ['year','month','n00','n01','n02','n10','n11','n12','n20','n21','n22','N0','N1','N2']
        Note:
            While computing the transtion numbers, say for month = mn,
            the last day of previous month mn-1 as been included for smooth transition
            form one month to other.
            For the first day of the first day year in the series,
            the last day of previous month (previous year i.e. 31 Dec)
            has been resampled at random from the 31st Dec values in the series.
        """

        nstates = self.getNoStates();
        self.getStateColumnName(); #This will generate state series and update
        # daily series
        dailyTS = self.getData(); #Getting the updated series

        # Considering the month as time-period for the computatiion of the transition matrix
        # Find the years in the data series
        years_in_given_series = self.findYearsDTS()
        # remove duplicate years if any in the series
        drop_dup_series= dailyTS.drop_duplicates(subset = 'Date', keep = 'first', inplace = False)

        # find unique years in the data and arrange in in ascending order
        #unique_years_in_series = set(find_years_DTS(drop_dup_series))

        # getting the last day for each of the month in the series
        # This is obtanied by substracting one from the Jan 1 indices
        lastdf = dailyTS.iloc[dailyTS[dailyTS['day']==1].index-1]
        # Take the given year in the series

        if nstates == 2:
            c = ['year','month','n00','n01','n10','n11','N0','N1']
            monthlyTS = pd.DataFrame(columns = c)
        elif nstates == 3:
            c = ['year','month','n00','n01','n02','n10','n11','n12','n20','n21','n22','N0','N1','N2']
            monthlyTS = pd.DataFrame(columns = c)
        cnt = 0
        storage_dict={} #This is to store the list for efficiency

        for yr_cnt in range(len(years_in_given_series)):
            yrx = years_in_given_series[yr_cnt]; #current year
            if yr_cnt != 0:
                pyrx = years_in_given_series[yr_cnt-1] #previous year

            #print(yrx)
            newseries = drop_dup_series.loc[drop_dup_series['year'] == yrx]
            for mn in range(1,13):
                # Selecting the last day of previous month
                if (yr_cnt==0) & (mn==1):
                    # selecting random from all the december 31st
                    # as the intial state for the beginning year of the series
                    dfs = lastdf[(lastdf['day']==31) & \
                             (lastdf['month']==12)]
                    ru = dfs.shape[0]
                    df1 = dfs.iloc[[random.randint(1,ru-1)]]

                elif (yr_cnt!=0) & (mn==1):
                    # day = 31
                    # month = 12
                    # year is previous year ((years_in_given_series(yr_cnt-1))
                    df1 = lastdf[(lastdf['day']==31) & \
                                  (lastdf['month']==12) &\
                                  (lastdf['year']==pyrx)].head(1)
                else:
                    # day = can be 30,31,28,29
                    # month = previous month (mn-1)
                    # year = same year (years_in_given_series(yr_cnt))
                    df1 = lastdf[(lastdf['month']==mn-1) &\
                                 (lastdf['year'] == yrx)].head(1)
                # selecting the rows with the given month mn
                monthly_ns = newseries[newseries['month'] == mn]
                # concatening the lastday of previous month for continuity
                input_series = pd.concat([df1,monthly_ns])
                # computing the number of transitions from different states
                if mn < 10:
                    storageid = str(yrx) + '0' + str(mn)
                else:
                    storageid = str(yrx) + str(mn)
                # Here we can use the dictionary to improve the efficiency
                # However we can use it for month 1 because the previous day
                # can be of different years
                if mn != 1:
                    if (storageid in storage_dict):
                        tslist = storage_dict[storageid]
                    else:
                        tslist = self.transitionStateCounter(input_series)
                        # print('dict used')
                        storage_dict[storageid] = tslist
                else:
                    tslist = self.transitionStateCounter(input_series)

                monthlyTS.loc[cnt] = [yrx,mn] + tslist
                cnt += 1
                # print(n)
                # print(N)
        return monthlyTS

    def genTP(self):
        """computes the transition probabilities
            Input:
            Input:
                X: X data with 'state' column = statecolumn
                         computed (using gen_state_series function)
                nstates: number of states
                statecol: specifying which column is the state column
            Output:
                tuple of two dataframes:
                1.with transition probabilities computed for 12 months each
                header will be as follows:
                When nstates = 2:
                ['month','p00','p01','p10','p11']
                'month' will be index
                When nstates = 3:
                [month','p00','p01','p02','p10','p11','p12','p20','p21','p22']

                2.with total numbers of transtions computed for 12 months each
                dataframe with the number of transitions computes
                header will be as follows:
                When nstates = 2:
                [month','n00','n01','n10','n11','N0','N1']
                When nstates = 3:
                [month','n00','n01','n02','n10','n11','n12','n20','n21','n22','N0','N1','N2']
        """

        nstates = self.getNoStates();
        statecolumn = self.getStateColumnName();
        dailyTS = self.getData();

        len_DTS = dailyTS.shape[0]
        dailyTS['s0'] = dailyTS[statecolumn]
        x2 = dailyTS['state'].values
        x2 = np.append(x2[1:],[0]) #Appending 0 at the last, but it doesnt matter as we dont use it
        dailyTS['s1'] = x2
        dailyTS.dropna(subset = ['s0','s1'],inplace = True)

        dailyTS['s0s1'] = dailyTS['s0'].astype('str') + dailyTS['s1'].astype('str')
        X1 = dailyTS[['s0','s1','s0s1']].copy()
        X1['ones'] = 1

        for mn in range(1,13):
            e = dailyTS[dailyTS['month']==mn].index-1
            e = e[(e >= 0) & (e <= (len_DTS-2))]
            # computing counts
            sum_s0s1 = X1.loc[e].groupby(['s0s1']).count()
            sum_s0 = X1.loc[e].groupby(['s0']).count()

            if nstates == 2:
                N = {}
                n = {}
                for i in [0,1]:
                    if i in sum_s0.index:
                        N[i] = sum_s0.loc[i,'ones']
                    else:
                        N[i] = 0
                for j in ['00','01','10','11']:
                    if j in sum_s0s1.index:
                        n[j] = sum_s0s1.loc[j,'ones']
                    else:
                        n[j] = 0
                #Check
                N0 = n['00'] + n['01']
                N1 = n['10'] + n['11']
                checkN = [N0,N1]
                for k1,k2 in zip([0,1],checkN):
                    if N[k1] != k2:
                        raise Exception("N(s0) is not equal to n(s0,0) + n(s0,1)")

                p = []
                for j1 in ['00','01','10','11']:
                    if j1 in ['00','01']:
                        if N0 == 0:
                            p.append(0)
                        else:
                            p.append(n[j1]/ N0)
                    else:
                        if N1 == 0:
                            p.append(0)
                        else:
                            p.append(n[j1]/ N1)

                prob = np.array(p)
                ntrans = [n['00'],n['01'],n['10'],n['11'],N0,N1]
                notransition = np.array(ntrans)

            if nstates == 3:
                N = {}
                n = {}
                for i in [0,1,2]:
                    if i in sum_s0.index:
                        N[i] = sum_s0.loc[i,'ones']
                    else:
                        N[i] = 0
                for j in ['00','01','02','10','11','12','20','21','22']:
                    if j in sum_s0s1.index:
                        n[j] = sum_s0s1.loc[j,'ones']
                    else:
                        n[j] = 0
                #Check
                N0 = n['00'] + n['01'] + n['02']
                N1 = n['10'] + n['11'] + n['12']
                N2 = n['20'] + n['21'] + n['22']
                checkN = [N0,N1,N2]
                for k1,k2 in zip([0,1,2],checkN):
                    if N[k1] != k2:
                        raise Exception("N(s0) is not equal to n(s0,0) + n(s0,1) + n(s0,2)")

                p = []
                for j1 in ['00','01','02','10','11','12','20','21','22']:
                    if j1 in ['00','01','02']:
                        if N0 == 0:
                            p.append(0)
                        else:
                            p.append(n[j1]/ N0)
                    elif j1 in ['10','11','12']:
                        if N1 == 0:
                            p.append(0)
                        else:
                            p.append(n[j1]/ N1)
                    else:
                        if N2 == 0:
                            p.append(0)
                        else:
                            p.append(n[j1]/ N2)

                prob = np.array(p)
                ntrans = [n['00'],n['01'],n['02'],n['10'],n['11'],n['12'],n['20'],n['21'],n['22'],N0,N1,N2]
                notransition = np.array(ntrans)

            if mn == 1:
                TP = prob
                TN = notransition
            else:
                TP = np.vstack((TP,prob))
                TN = np.vstack((TN,notransition))
        monthscnt = [i for i in range(1,13)]
        columns2state = ['p00','p01','p10','p11']
        columns3state = ['p00','p01','p02','p10','p11','p12','p20','p21','p22']
        columns2TN = ['n00','n01','n10','n11','N0','N1']
        columns3TN = ['n00','n01','n02','n10','n11','n12','n20','n21','n22','N0','N1','N2']

        if nstates == 2:
            TP_df = pd.DataFrame(data = TP, index = monthscnt, columns = columns2state)
            TN_df = pd.DataFrame(data = TN, index = monthscnt, columns = columns2TN)
        if nstates == 3:
            TP_df = pd.DataFrame(data = TP, index = monthscnt, columns = columns3state)
            TN_df = pd.DataFrame(data = TN, index = monthscnt, columns = columns3TN)
        TP_df.index.name = 'month'
        TN_df.index.name = 'month'
        self.TP = TP_df
        self.nTransitions = TN_df
        return (TP_df,TN_df)

    def getTP(self):
        try:
            return self.TP
        except:
            self.genTP()
            return self.TP

    def setTP(self,newTP):
        """ Sets user-defined transition probability to the dataseries instead
        of using the computed one.
        Inputs:
            newTP:  Pandas dataframe
                    New transition probability
                    It must have 'month' as index and it should be from 1 to 12
                    Its columns should be:
                        ['p00','p01','p10','p11'] if nstates = 2
                        ['p00','p01','p02','p10','p11','p12','p20','p21','p22']
                        if nstates = 3
        Output:
            sets the TP of the instance of WeatherDTS to newTP
        Note:
            newTP will undergo testing for the sum of transition probabilites
            Eg: If nstates = 3
                p0 = p00 + p01 + p02 = 1
                p1 = p10 + p11 + p12 = 1
                p2 = p20 + p21 + p22 = 1
                If nstates = 2
                p0 = p00 + p01 = 1
                p1 = p10 + p11 = 1
            If the sum of transition proababilites is not 1 (tolerance = 0.001)
            the newTP will not be set. Instead, TP will be revert to the original
            TP.
        """
        chkTP = newTP.copy()
        chkTP2 = newTP.copy()
        #print(chkTP)
        if self.nstates == 2:
            chkTP['p0'] = chkTP['p00'] + chkTP['p01']
            chkTP['p1'] = chkTP['p10'] + chkTP['p11']
            newchkTP = chkTP.loc[:,['p0','p1']].copy().values
        elif self.nstates == 3:
            chkTP['p0'] = chkTP['p00'] + chkTP['p01'] + chkTP['p02']
            chkTP['p1'] = chkTP['p10'] + chkTP['p11'] + chkTP['p12']
            chkTP['p2'] = chkTP['p20'] + chkTP['p21'] + chkTP['p22']
            newchkTP = chkTP.loc[:,['p0','p1','p2']].copy().values
        else:
            ValueError('Invalid number of states')
        # Here ideally sum of transitions probabilities must be one, but
        # when there is no such condition, for eg. if all the days in the
        # month is wet, then p00 doesn't exists and so its p01 and p02
        # In such case p00 = p01 = p02 = 0 is defined
        # So, checking if sum of TP is 1 where  p00 + p01 + p02 != 0
        NEQ0 = ~np.isclose(newchkTP,0,atol=0.001)
        #print(NEQ0)
        res1 = np.isclose(newchkTP,1,atol=0.001)
        #print(res1)
        CheckFlag1 = np.all(res1[NEQ0] == True)
        #print(CheckFlag1)

        #print("Check greater than one")
        Check_greater_than_one = np.any(chkTP2.values > 1)
        #print(chkTP2.values > 1)
        #print(Check_greater_than_one)
        #print("Check smaller than zero")
        Check_smaller_than_zero = np.any(chkTP2.values < 0)
        #print(chkTP2.values < 0)
        #print(Check_smaller_than_zero)
        CheckFlag2 = Check_greater_than_one | Check_smaller_than_zero
        #print(CheckFlag2)

        if (CheckFlag1 & ~CheckFlag2)  == True:
            # Setting TP to user provided TP
            self.TP = newTP
        else:
            # generating the original TP
            print("Invalid user defined TP. Reverting to the original TP")
            x = self.genTP()
            self.TP = x[0]
        # Perform check if sum of the probabilities exceeds

    def arrangeMovingWindow(self, windowsize):
        """This function will arrange duplets of states (of previous day t-1
        and of current day t (s0 and s1)) for each month and each day in a year.
        Input:
            X: time series with 'state' column
            windowsize: windowsize of the moving window
        Output:
            dictionary of dataframe for each day of everty month.
            Dataframe consists of the duplets of states s0 and s1
            with index as index of dailyTS
            key of dictionay is a tuple (month,day)
            value of dictionary is dataframe
            Eg:
                {(1,15): Dataframe of duplets of states column is s0 and s1}
        Will add the February 28 window for leap year Feb 29
        """
        statecol = self.getStateColumnName()
        dailyTS = self.getData();
        dailyTS['s0'] = dailyTS[statecol]
        x2 = dailyTS['state'].values
        x2 = np.append(x2[1:],[0])
        dailyTS['s1'] = x2

        daysNormalyear = {1:31,2:28,3:31,4:30,5:31,6:30,7:31,8:31,9:30,10:31,11:30,12:31}
        G1 = {}
        len_DTS = dailyTS.shape[0]
        for mn in range(1,13):
            for dy in range(1,daysNormalyear[mn]+1):
                #print((mn,dy))
                # Getting the python index of dataframe (row number)
                # which is different from the index of dataframe
                f = (dailyTS[(dailyTS['month']==mn) & (dailyTS['day']==dy)].index-int(windowsize/2)).values
                for i1,j1 in enumerate(f):
                    if i1 == 0:
                        e = np.arange(j1,j1+windowsize)
                    else:
                        e = np.append(e,np.arange(j1,j1+windowsize))
                e = e[(e >= 0) & (e <= (len_DTS-2))]
                # Here in (len_DTS-2) , minus 2 is because
                # 1 is for aranging the index as its srarts from 0
                # another 1 is for fact the last row does have s1 state
                G1[(mn,dy)] = dailyTS.loc[e,['s0','s1']].copy()

        # Adding Feb 28 window as Feb 29 window
        G1[(2,29)] = G1[(2,28)]
        return G1.copy()

    def getArrangedWindow(self, windowsize):
        try:
            return self.arrangedWindow.copy()
        except:
            self.arrangedWindow = \
                self.arrangeMovingWindow(windowsize)
        return self.arrangedWindow

    def simStateNextday(self,simDate0,s0):
        """Simulate the next day precipitation state s1.
           Input:
               -simDate0 is the current day simulation date.
                   Should be pandas or python datetime
               -s0 is the current day precipitation state
               -nstates is no of state
               -TP is dataframe of transition probailities of states (month wise)
                   which is output of genTP() or getTP()
           Output:
               s1 is the precipitation state for next day.
        """
        nstates = self.getNoStates()
        TP = self.getTP()

        assert s0 in [0,1,2]
        assert nstates in [2,3]
        yr = simDate0.year
        mn = simDate0.month
        dy = simDate0.day

        if calendar.isleap(yr):
            d = 29
        else:
            d = 28
        daysyear = {1:31,2:d,3:31,4:30,5:31,6:30,7:31,8:31,9:30,10:31,11:30,12:31}

        endday_month = daysyear[mn]

        U = random.random()
        #print(U)
        #print()
        #print(TP)
        if nstates == 2:
            if s0 == 0:
                col = 'p00'
            elif s0 ==1:
                col = 'p10'

            if (dy != endday_month):
                pA = TP.loc[mn,col]
            elif (dy == endday_month) & (mn != 12):
                pA = TP.loc[mn+1,col]
            else:
                pA = TP.loc[1,col]
            #print(pA)
            #print()
            #print(TP[col])
            if U < pA:
                s1 = 0
            else:
                s1 = 1

        elif nstates == 3:
            if s0 == 0:
                col1 = 'p00'; col2 = 'p01'
            elif s0 == 1:
                col1 = 'p10'; col2 = 'p11'
            else:
                col1 = 'p20'; col2 = 'p21'

            if (dy != endday_month):
                pA = TP.loc[mn,col1]; pB = TP.loc[mn,col2]
            elif (dy == endday_month) & (mn != 12):
                pA = TP.loc[mn+1,col1]; pB = TP.loc[mn+1,col2]
            else:
                pA = TP.loc[1,col1]; pB = TP.loc[1,col2]
            #print((pA, pB))
            #print()
            #print(TP[[col1,col2]])
            if U < pA:
                s1 = 0
            elif pA <= U < (pA + pB):
                s1 = 1
            else:
                s1 = 2

        else:
            raise ValueError('Wrong number of states')

        return s1

    def selectFromArrangedWindow(self,ArrWindow,MONTH,DAY,s0,s1,windowsize):
        """ extract the data from dailyTS given s0 and s1 for given
        ArrWindow = ArrangedWindow
        month MONTH and day DAY
        First it will find the index of the data from ArrWindow
        for given s0 and s1 for given
        month MONTH and day DAY
        """
        #ArrWindow = self.getArrangedWindow(windowsize)
        dailyTS = self.getData()

        AW = ArrWindow[MONTH,DAY]
        selected_ids = AW[(AW['s0'] == s0) & (AW['s1'] == s1)].index
        # selected_ids is a list
        # so dailyTS.loc[selected_ids].copy() will return dataframe
        # even if there is only one record
        return dailyTS.loc[selected_ids].copy()

    # Reserved function
    def computeDistance(self,X,WV,columnsWV,weights_type = 'inv_std',**kwargs): #Good to use
        """ Computes the distances required for kNN simulation
        Inputs:
        X:
            It is dataframe with data for which distances are to be computed.
            It is not all entire data but selected data based on moving window /
            month.
        WV:
            Weather vector required from which distances are to be computed in X.
            It is python list.
            Eg: [0.5,26.5] for ['precip','tmean']
        columnsWV:
            It is python list of columns in dataframe which contains weather vectors.
            Eg: ['precip','tmean']
        weights_type:
            It is method for computation of distances for k-NN.
            It has three types:
                (a) "equal"
                (b) "user_defined"
                (c) "inv_std"
        If weights_method = "user_defined" then **kwargs is weights.
        **kwargs:
            weights = [wt_WV1, wt_WV2, wt_WV3.....]

        Note:
        Normalisation: Normalisation will be carried out.
        If in case the normalisation is not possible for all the
        weather variables. So the distances computed are with normalised
        weather variables using weighted euclidean distances.
        In case normalisation is not possible (Eg. when standard deviation is
        zero or X is just a row), normal euclidean distances will be returned.

        Outputs: Tuple- (Y,weights)
        Y:
            It is dataframe with indices with distances from WV to data in X, along
        with indices in X
        weights:
            Weights used for computation of distances for each of WV variables
        """
        X1 = X.copy()

        WV = np.array(WV) #convert it into numpy array
        if np.isnan(WV).all() == True:
            raise Exception('Invalid weather vector WV. All values are nan.')


        if weights_type == "user_defined":
            if 'weights' not in kwargs.keys():
                raise Exception('Invalid weights key. No "weights" key found!')
            if 'weights' in kwargs.keys():
                # lists of weights
                weights = kwargs.get('weights')
                if len(weights) != len(WV):
                    raise Exception('Length of User supplied weights list is not equal to WV')
                wts = np.array(weights)

        if weights_type == "equal":
            wts = np.ones(len(columnsWV))

        idWV = np.arange(0,len(columnsWV)) # this is for id
        newidWV = idWV[~np.isnan(WV)] #This will get the id for values in WV which are not NaN
        newWV = WV[~np.isnan(WV)] #This will be the new WV after removing NaN
        newcolumnsWV = []
        for i in newidWV:
            newcolumnsWV.append(columnsWV[i])

        #original_length = X1.shape[0]
        X1.dropna(inplace  = True)
        if X1.shape[0] == 0:
            raise Exception('All the data rows have nan values! Please fill the data!')
        Y1 = X1[newcolumnsWV].values
        #print(Y1)
        if (Y1.shape[0] == 1) | (np.unique(Y1,axis = 0).shape[0] == 1):
            diff = Y1 - newWV
            # In this case there will be no point of standard deviation
            # and so all assign equal weights when weights_type == "inv_std"
            if weights_type == "inv_std":
                wts = np.ones(len(newcolumnsWV))
        else:
            M = np.nanmean(Y1,axis = 0) #mean
            S = np.nanstd(Y1,axis = 0, ddof = 1) #standard deviation with ddof = 1

            if weights_type == "inv_std":
                O = np.ones_like(M)
                wts = np.divide(O,S,out = np.zeros_like(O), where = (S!=0))
            nY1 = (Y1-M)
            normY1 = np.divide(nY1,S,out = np.zeros_like(nY1), where = (S!=0))
            nWV = (newWV-M)
            normWV = np.divide(nWV,S,out = np.zeros_like(nWV), where = (S!=0))
            diff = (normY1 - normWV)
        #print(wts)
        if weights_type != "inv_std":
            wts = wts[~np.isnan(WV)]
        #print(wts)
        g = (diff*diff) * wts
        dist = np.sqrt(np.sum(g,axis = 1))
        Y = pd.DataFrame(data=dist,index = X1.index,columns = ['dist'])
        return (Y,wts)

    #Simulation function
    def simulate_kNN(self,simulation_dateseries,iState,initialWV,columnsWV,windowsize=7,messages = False,\
                     weights_method = 'inv_std',writefile = False,outputdir = os.getcwd(), **kwargs):
        """ Simulate the daily Time Series using k-NN.
        Inputs:
        simulation_dateseries:
            Dateseries for which simulation is to be carried out.
            It should be python or pandas datetime.
        iState:
            It is the intial state of precipitaion required for simulation.
            It is integer value either 0,1, or 2.
        initialWV:
            Initial weather vector required for simulation.
            It is python list.
            Eg: [0.5,26.5] for ['precip','tmean']
        columnsWV:
            It is python list of columns in dataframe which contains weather vectors.
            Eg: ['precip','tmean']
        windowsize:
            It is the sumilation window size.
            It is odd integer value. Default is 7.
        messages:
            It is option for messages to be displayed while simulating.
            Essential for debugging.
            Default is False.
        writefile:
            if False, it will do nothing.
            If True, write the simulation results in csv format.
                If there is multisite,
                It will make csv files for them too.
        weights_method:
            It is method for computation of distances for k-NN.
            It has three types:
                (a) "equal"
                (b) "user_defined"
                (c) "inv_std"
        outputdir:
            It the output directory where the output will be written
        If weights_method = "user_defined" then **kwargs is weights.
        **kwargs:
            weights = [wt_WV1, wt_WV2, wt_WV3.....]

        Outputs: Tuple - (index_simulatedWVs,simulated_series)
        index_simulatedWVs:
            It is ptyhon list of indices of simulated data for each time step
            in orginal series.
        simulated_series:
            It is dataframe with simulated weather series.
            It has Simulation_date, old_index columns.

        """
        # This is required subfunction to check states
        def check_simulated_states(nstates,neighbors,s0,s1):
            """Check the validity of the selected neighbors during simulation of
            daily states. Check if current state and next day (timestep) states, s0 and
            s1 respectively are available in the neighbors/ dataframe of s0 and s1
            for the given time.
            What will it do?
            Type A:
            If the simulated states (s0,s1) doesn't exists in the neighbors,
            it will try to find other neighbors. First it will find all the neighbors
            with states s0 only. Since there is no s1, it will list and count
            all the states with (s0,x1),(s0,x2)..etc.
            Then after assingin probability, new states will chosen randomly.
            Type B:
            If the simulates state (s0) is not present, then it will lists all other
            possible state combinations, and then assign probability and then
            sample a random one.
            Inputs:
                nstates= number of states
                neighbors = dataframe with all neighbors with s0 and s1 conditions
                    dataframe will have index, s0 and s1 columns
                s0 = current day state
                s1 = next day state
            Outputs:
                (s0,s1)- newly sampled states
            """
            AW1 = neighbors;
            AW_s0 = AW1[AW1['s0']==s0].copy();
            # if there is s0 in the set but not s1
            if AW_s0.empty == False:
                #print('Type A')
                if nstates == 3:
                    remains = set([0,1,2]) - set([s1])
                else:
                    remains = set([0,1]) - set([s1])
                N=[]
                e1 = []
                for j in remains:
                    e1.append(j)
                    N.append(AW_s0[(AW_s0['s1'] == j)].shape[0])
                p1 = list(np.array(N)/sum(N))
                #print(e1)
                #print(N)
                s1 = np.random.choice(list(e1),1,p=p1)[0]
            else: #if there is not s0 but there is s1
                # Now we change the s0
                #print('Type B')
                if nstates == 3:
                    remains = set([0,1,2]) - set([s0])
                else:
                    remains = set([0,1])- set([s0])
                e1 = []
                e2 = []
                N=[]
                cnt = 0
                for j in remains:
                    for k in [0,1,2]:
                        e1.append(cnt)
                        e2.append((j,k))
                        N.append(AW1[(AW1['s0'] == j) & (AW1['s1'] == k)].shape[0])
                        cnt += 1
                p1 = list(np.array(N)/sum(N))
                #print(e1)
                #print(e2)
                #print(N)
                selected = np.random.choice(e1,1,p=p1)[0]
                s0,s1 = e2[selected]
            #print(s0,s1)
            return (s0,s1)
        # End of sub-function

        ################### Main module ##################################
        # Getting variables within from self
        self.getStateColumnName();
        nstates = self.getNoStates()
        X = self.getData()
        #TP = self.getTP()
        AW = self.getArrangedWindow(windowsize)

        if weights_method == "user_defined":
            if 'weights' not in kwargs.keys():
                raise Exception('Invalid weights key. No "weights" key found!')
            if 'weights' in kwargs.keys():
                # lists of weights
                weights = kwargs.get('weights')
                if len(weights) != len(initialWV):
                    raise Exception('Length of User supplied weights list is not equal to WV')

        X1 = X.copy()
        #dateseries = pd.date_range(start=startDate, end=endDate);
        dateseries = simulation_dateseries;
        counter=0
        check = {};
        index_simulatedWVs = []
        s1 = iState #This is just for initialisation, later it will change in each step
        simulatedWV = initialWV
        for i in dateseries:
            if messages == True:
                print()
                print('Date: {}'.format(i))
            # Get the precipitation state for the next day
            if counter == 0:
                s0 = iState;
                WV = initialWV;
            else:
                s0 = s1;
                # WV is just the list of weather vectors
                WV = list(simulatedWV.values)[0];
            # Simulation for the next day
            #Note: If you want to simulate from date say 2008-1-1, start the simulation \
            # from 2007-12-31 and istate is the precipitaton state at 2007-12-31
            # Extract the data from dailyTS given s0 and s1 for given month MONTH and day DAY
            # They are the all neighbors that we can find
            # This results in the dataframe with selected states (s0,s1)
            s1 = self.simStateNextday(i,s0);
            all_neighbours = self.selectFromArrangedWindow(AW,i.month,i.day,s0,s1,windowsize);
            # Redoing again
            # When there are no observations with states (s0,s1)
            if all_neighbours.empty == True:
                if messages == True:
                    print('States are {}'.format([s0,s1]))
                    print('Warning there are no observations with given states')
                    print('So, resampling again!')
            while all_neighbours.empty == True:
                AW1 = AW[i.month,i.day]
                s0,s1 = check_simulated_states(nstates,AW1,s0,s1)
                all_neighbours = self.selectFromArrangedWindow(AW,i.month,i.day,s0,s1,windowsize);

            if messages == True:
                print('States are {}'.format([s0,s1]))
                print('Neighbors are:')
                print('Length of neighbors are = {}'.format(len(all_neighbours)))
                print(all_neighbours)
            # Computes the distances
            DD = self.computeDistance(all_neighbours,WV,columnsWV,weights_type = weights_method,**kwargs)
            # Distances are the first positin in DD
            distances_df = DD[0].copy()
            # Sorting the distances in ascending order
            distances_df.sort_values(by=['dist'],inplace = True)
            # No = no of observations selected
            No = distances_df.shape[0]
            # values of k is sqrt(N) (value to change in integer value)
            k = int(np.ceil(np.sqrt(No)))
            # selected k-Nearest Neighbors
            kNNs = distances_df.head(k).copy()
            # Computing the weights using kernel function
            kNNs['rank'] = np.array(list(range(len(kNNs.index))))+1
            kNNs['ones'] = 1
            kNNs['invrank'] = kNNs['ones']/kNNs['rank']
            kNNs['kernel_wts'] = kNNs['invrank']/kNNs['invrank'].sum()

            if messages == True:
                print('Selected kNNs: \n {}'.format(kNNs))
            # discrete sampling using numpy random choice
            # elements to be sampled
            kNNs_drop_duplicates = kNNs.drop_duplicates('dist').copy()
            elements = kNNs.index
            elements_dropped = kNNs_drop_duplicates.index
            probabilities = kNNs['kernel_wts'].values
            # here we sample one element
            index_s0 = np.random.choice(elements,1,p=list(probabilities))
            # index_s0 is the sampled index corresponding to so
            # Now for index of s1, which is required, is next day of s0
            # That is index of s1 = index sampled + 1
            index_s1 = index_s0 + 1;
            # Therefore, simulated weather vector
            simulatedWV = X1.loc[index_s1,columnsWV];

            if messages == True:
                print('SimuatedWV = {}',format(simulatedWV))
                print('Index of SimulatedWV = {}'.format(simulatedWV.index.values[0]))
                #print(simulatedWV.values)
                #print(list(simulatedWV.values)[0])
                #print(np.isnan(list(simulatedWV.values)[0]))
                #print(np.isnan(list(simulatedWV.values)[0]).any())
                print('Length of kNNs = {}'.format(len(elements)))
                print('Length of kNNs removing duplicates = {}'.format(len(elements_dropped)))

            # converting into python list
            # It will form list with two dimnesions because
            # numpy array from the df.values is in 2D
            # Eg it will form like [[ 0.1 27.8 20.8 24.3]]
            # So we have to index the first one
            if np.isnan(list(simulatedWV.values)[0]).all() == True:
                raise Exception('All of weather variables for given day are NaN type or missing! \
                                 Please fill the data and run it again!')

            elif np.isnan(list(simulatedWV.values)[0]).any() == True & len(elements_dropped)==1:
                if messages == True:
                    print('Warning! Two or more of weather variables in simuated values are missing! \n \
                           Since, the number of neighbors from which it is \n \
                           selected is only one, the simulation is carried out \n \
                           with only variables that are not missing.')
            else:
                while np.isnan(list(simulatedWV.values)[0]).any() == True & len(elements_dropped)>1:
                    if messages == True:
                        print('Warning! Two or more of weather variables are missing! \n\
                               so, ingnoring this! \n \
                               Simulating new one that do not have missing values!')
                    index_s0 = np.random.choice(elements,1,p=list(probabilities))
                    # index_s0 is the sampled index corresponding to so
                    # Now for index of s1, which is required, is next day of s0
                    # That is index of s1 = index sampled + 1
                    index_s1 = index_s0 + 1;
                    # Therefore, new simulated weather vector is
                    simulatedWV = X1.loc[index_s1,columnsWV];
                    print('Newly simulatedWV is: {}'.format(simulatedWV))
            check[i] = all_neighbours;
            index_simulatedWVs.append(simulatedWV.index.values[0])
            counter += 1

        new_index = [i for i in range(len(dateseries))]
        # This is for main data (area-averaged values)
        simulated_series = X1.loc[index_simulatedWVs].copy()
        simulated_series.drop(columns = ['Date','year','month','day','state'],inplace = True)
        #simulated_series.rename(columns = {"Date":"his_date","year": "his_year","month":"his_month","day":"his_day","state":"his_state"},inplace = True)
        simulated_series.insert(0,"Date",dateseries)
        #simulated_series.insert(1,"his_index",index_simulatedWVs)
        simulated_series.index = new_index
        #simulated_series['year'] = simulated_series['Date'].dt.year
        #simulated_series['month'] = simulated_series['Date'].dt.month
        #simulated_series['day'] = simulated_series['Date'].dt.day
        #simulated_series_write = simulated_series.copy()
        #drop_list1 = ['his_index','his_date','his_year','his_month','his_day','his_state','year','month','day']
        #for i in drop_list1:
        #    try:
        #        simulated_series_write.drop(columns = [i], inplace = True)
        #    except:
        #        pass
        if writefile == True:
            if self.name is not None:
                fname0 = self.name + '_simulated_series.csv';
            else:
                fname0 = 'Unnamed' + '_simulated_series.csv';
            fpathname0 = os.path.join(outputdir,fname0)
            simulated_series.to_csv(fpathname0, index = False)
            #simulated_series_write.to_csv(fpathname0, index = False)
        #simulated_series2 = simulated_series_write.copy()
        # For multisite (MS) case
        MS = self.var_dict;
        if len(MS) == 0:
            sim_MS = None
            #sim_MS2 = None
        else:
            sim_MS = {}
            #sim_MS2 = {}
            for var_name,var_data in MS.items():
                sim_var_data = var_data.loc[index_simulatedWVs].copy()
                sim_var_data.drop(columns =['Date'],inplace = True)
                #sim_var_data.rename(columns = {"Date":"his_date"},inplace = True)
                sim_var_data.insert(0,"Date",dateseries)
                #sim_var_data.insert(1,"his_index",index_simulatedWVs)
                sim_var_data.index = new_index
                sim_MS[var_name] = sim_var_data
                #sim_var_data_write = sim_var_data.copy()
                #drop_list2 = ['his_index','his_date']
                #for i in drop_list2:
                    #try:
                        #sim_var_data_write.drop(columns = [i], inplace = True)
                    #except:
                        #pass
                if writefile == True:
                    if self.name is not None:
                        fname1 = self.name + '_simulated_' + var_name +'.csv';
                    else:
                        fname1 = 'Unnamed' + '_simulated_' + var_name +'.csv';
                    fpathname1 = os.path.join(outputdir,fname1)
                    sim_var_data.to_csv(fpathname1, index = False)
                    #sim_var_data_write.to_csv(fpathname1,index = False)
                #sim_MS2[var_name] = sim_var_data_write
        self.sim_results = (index_simulatedWVs,simulated_series,\
                            sim_MS)
        return (index_simulatedWVs,simulated_series,sim_MS)

    def fit_gamma_month(self,precip_column):
        """Fits the gamma distribution over precipitaion data at monthly scale.
        Inputs:
        X: pandas dataframe
           X should have Date, year, month and day column which class WeatherDTS will
           generate.
           X should also have precipitation column given by precip_column
        precip_column: string
            Name of the precipitation column in the dataframe
            (wet_threshold: float
            Threshold for defining wet days)
        Outputs:
        G1:
            pandas dataframe with index of months 1 to 12 and columns of
            mean: mean of the fitted distribution
            variance: variance of the fitted distribution
            CV: coefficient of variation (stdev/mean) of the fitted distribution
            shape: estimated shape parameter
            location: estimated location parameter
            scale: estimated scale parameter
        """
        dailyTS = self.getData()
        wet_threshold = self.getWetThreshold()
        months = [i+1 for i in range(12)]
        G1 = pd.DataFrame(index = months,columns = ['mean','variance','CV','shape','location','scale'])
        for mn in months:
            monP = dailyTS.loc[((dailyTS[precip_column] >= wet_threshold) & \
                                  (dailyTS['month'] == mn)),precip_column].copy()
            #print(monP)
            (a,l,s) = gamma.fit(monP,floc = 0)
            G1.loc[mn,['shape','location','scale']] = [a,l,s]
            (m,v) = gamma.stats(a, loc=l, scale=s, moments='mv')
            CV = np.sqrt(v)/m
            G1.loc[mn,['mean','variance','CV']] = [m,v,CV]
        self.gamma_params = G1
        return G1

    def get_gamma_params(self,precip_column):
        try:
            return self.gamma_params
        except:
            self.fit_gamma_month(precip_column)
            return self.gamma_params

    def change_gamma_month(self,G,prop = 'mean', change = [[0 for i in range(12)]]):
        """Changes moments of gamma distribution
        Inputs:
        G: Dataframe
            Consists of monthly values of mean and variance of gamma distribution
            Result of fit_gamma_month function
        prop: string variable
            'm' - for mean
            'CV' - for coefficient of variation
            'mCV' - for both mean and CV
        change: python lists of changes in fraction for all months
            for 'm' and 'CV' option, it is 1-D list of shape (1,12)
            Eg: [[0.2 for i in range(12)]]
            for 'ms' option,it is 2-D list of shape (2,12)
            Eg: [[0.2 for i in range(12)],[0.2 for i in range(12)]]
            This will be converted into numpy array for computation

        Output:
        G2:
            pandas dataframe with index of months 1 to 12 and columns of
            mean: mean of the changed distribution
            variance: variance of the changed distribution
            shape: changed shape parameter
            location: changed location parameter
            scale: changed scale parameter
        """
        CH = np.array(change)
        #print(CH)
        G1 = G.copy()
        if prop == 'mean': #Change only the mean, others are kept constant
            ch  = CH[0]
            G1['new_mean'] = G1['mean']*(1+ch);
            G1['new_scale'] = (G1['CV'] * G1['new_mean'])**2 / G1['new_mean']
            G1['new_shape'] = G1['new_mean'] / G1['new_scale']
            G1['new_location'] = G1['location']

            G1['new_variance'] = G1['new_shape'] * (G1['new_scale']**2)
            G1['new_CV'] = (G1['new_variance']**0.5)/G1['new_mean']
        elif prop == 'CV': #Change only the CV, other are kept constant
            ch = CH[0]
            G1['new_CV'] = G1['CV'] * (1+ch)
            G1['new_scale'] = (G1['new_CV'] * G1['mean'])**2 / G1['mean']
            G1['new_shape'] = G1['mean'] / G1['new_scale']
            G1['new_location'] = G1['location']

            G1['new_mean'] = G1['new_shape'] * (G1['new_scale'])
            G1['new_variance'] = G1['new_shape'] * (G1['new_scale']**2)
        elif prop == 'mCV': #Change both mean and CV
            ch_mean = CH[0]
            ch_CV = CH[1]
            G1['new_mean'] = G1['mean']*(1+ch_mean);
            G1['new_CV'] = G1['CV'] * (1+ch_CV);
            G1['new_scale'] = (G1['new_CV'] * G1['new_mean'])**2 / G1['new_mean']
            G1['new_shape'] = G1['new_mean'] / G1['new_scale']
            G1['new_location'] = G1['location']

            G1['new_variance'] = G1['new_shape'] * (G1['new_scale']**2)
        else:
            raise Exception('Unrecognised property in prop!')
        G2 = G1.loc[:,['new_mean','new_variance','new_CV','new_shape','new_location','new_scale']].copy()
        G2.rename(columns = {'new_mean':'mean',
                   'new_variance': 'variance',
                   'new_CV': 'CV',
                   'new_shape': 'shape',
                   'new_location': 'location',
                   'new_scale': 'scale'}, inplace = True)
        return G2

    def gamma_map(self,precip_column,mapped_columnname,G1,G2):
        """Generate the quantile mapped series with new Gamma parameters
        Inputs:
            precip_column: name of column of the precipitation series
            mapped_columnname: name of column of the mapped precipitation series
            It is name for new column for the mapped data.

            G1: Gamma distribution parameters of Z
                Result of fit_gamma_month function
            G2: Gamma distribution paramters into which Z is to be mapped
                Result of  change_gamma_month function
            (wet_threshold = wet threshold to define the precipitation)

            Outputs:
            copy of Z with added column of quantile mapped precipitation
            """
        dailyTS = self.getData()
        wet_threshold = self.getWetThreshold()

        def qmapX(x,mn,G1,G2):
            p = gamma.cdf(x,a = G1.loc[mn,'shape'], \
                                    loc = G1.loc[mn,'location'], \
                                    scale = G1.loc[mn,'scale'])
            X = gamma.ppf(p,a = G2.loc[mn,'shape'], \
                                    loc = G2.loc[mn,'location'], \
                                    scale = G2.loc[mn,'scale'])
            return X

        months = [i+1 for i in range(12)]
        sn = mapped_columnname
        dailyTS.loc[:,sn] = dailyTS.loc[:,precip_column]
        for mn in months:
            ind = dailyTS.loc[((dailyTS[precip_column] >= wet_threshold) & \
                         (dailyTS['month'] == mn)), precip_column].index
            dailyTS.loc[ind,sn] = dailyTS.loc[ind, precip_column].apply(qmapX,args = [mn,G1,G2])
        self.updateData(dailyTS.copy())
        return dailyTS.copy()

    def deltashift(self,column_name,mapped_columnname,shifts = [0 for i in range(12)]):
        """This will shift the temperature / other data by the given amount.
            It operates in monthly basis.

        Inputs:
        Z: pandas data frame
        column_name: Name of the column which you want to shift
        mapped_columnname: Name of the column with shifted data
            It is name for new column for the shifted data.
        shifts: Python list of monthly shifts
        Eg: [0.1,0.2,......]

        Outputs:
        copy of Z with added column with shifted data under 'mapped_columnname' name.
        """
        dailyTS = self.getData()
        months = [i+1 for i in range(12)]
        sn = mapped_columnname
        dailyTS.loc[:,sn] = dailyTS.loc[:,column_name]
        for mn in months:
            ind = dailyTS.loc[(dailyTS['month'] == mn), column_name].index
            dailyTS.loc[ind,sn] = dailyTS.loc[ind, column_name] + shifts[mn-1]
        self.updateData(dailyTS.copy())
        return dailyTS.copy()

def apply_gamma_map_multisite(variable_dictionary, precip_keyname_in_var_dict,\
                              wet_threshold, mapped_columnname,desired_changes):
    """This will apply gamma mapping to precipitation values in the multisite stations
    Inputs:
    variable_dictionary:
          It is python dictionary in which key is varaible name and
                value is pandas dataframe for multisite for that variable.
                Each pandas dataframe contains only one type of weather variable
                Eg: var_dict = {'precip': pd_precip,
                                'tmax': pd_tmax}
                where 'pd_precip' dataframe consists of multisite precipitation data
                Eg of pd_precip:
                ---------------------------------
                     Date        p1   p2   p3
                 0  1980-01-01   0.20 0.50 0.50
                 1  1980-01-02   0.10 5.20 9.60
                ---------------------------------
                where p1, p2 and p3 are stations.

    precip_keyname_in_var_dict: python string
        Name of key for the precipitaion in the  variable dictionary

    wet_threshold:
        It is the value to seperate wet and dry condition.

    mapped_columnname   :
        It is name for new column for the mapped data.

    desired_changes:
        python lists of changes in fraction for all months
            for 'm' and 'CV' option, it is 1-D list of shape (1,12)
            Eg: [[0.2 for i in range(12)]]
            for 'ms' option,it is 2-D list of shape (2,12)
            Eg: [[0.2 for i in range(12)],[0.2 for i in range(12)]]
            This will be converted into numpy array for computation

    Outputs:
    gammaMappedData: pandas Dataframe will the gamma mapped data for the all
        the multisite stations

    """
    # Multisite P = mP
    mP = variable_dictionary[precip_keyname_in_var_dict]
    # Creating the dictiionary to store the WeatherDTS instance of each of the
    mP_dict = {}
    for i in mP.columns:
        #print(i)
        if i != 'Date':
            u = mP.loc[:,['Date',i]].copy()
            #print(u)
            mP_dict[i] = WeatherDTS(data = u,name = i, \
                           precipitation_column_name = i, \
                           var_dict = variable_dictionary)

    gammaMappedData = pd.DataFrame(index = mP['Date'])
    for k,v in mP_dict.items():
        v.setWetThreshold(wet_threshold)
        v.fit_gamma_month(k)
        G1 = v.get_gamma_params(k)
        # mean and coefficient of variation both will be used
        G2 = v.change_gamma_month(G1,prop='mCV',change = desired_changes)
        new_col_nm = mapped_columnname + k
        Gmapped = v.gamma_map(k,new_col_nm,G1,G2)
        #print(Gmapped[new_col_nm].values)
        gammaMappedData[k] = np.round(Gmapped[new_col_nm].values,3)
    return gammaMappedData

def apply_deltashift_multisite(variable_dictionary, variable_keyname_in_var_dict,\
                               mapped_columnname,desired_shifts):
    """This will apply gamma mapping to precipitation values in the multisite stations
    Inputs:
    variable_dictionary:
          It is python dictionary in which key is varaible name and
                value is pandas dataframe for multisite for that variable.
                Each pandas dataframe contains only one type of weather variable
                Eg: var_dict = {'precip': pd_precip,
                                'tmax': pd_tmax}
                where 'pd_precip' dataframe consists of multisite precipitation data
                Eg of pd_precip:
                ---------------------------------
                     Date        p1   p2   p3
                 0  1980-01-01   0.20 0.50 0.50
                 1  1980-01-02   0.10 5.20 9.60
                ---------------------------------
                where p1, p2 and p3 are stations.

    variable_keyname_in_var_dict: python string
        Name of key for varaible (taht you want to make shift) in the  variable dictionary

    mapped_columnname   :
        It is name for new column for the mapped data.

    desired_shifts:
        shifts: Python list of monthly shifts
        Eg: [0.1,0.2,......]

    Outputs:
    shiftedData: pandas Dataframe with shifted data for the all
        the multisite stations

    """
    # Multisite P = mP
    mT = variable_dictionary[variable_keyname_in_var_dict]
    # Creating the dictiionary to store the WeatherDTS instance of each of the
    mT_dict = {}
    for i in mT.columns:
        #print(i)
        if i != 'Date':
            u = mT.loc[:,['Date',i]].copy()
            #print(u)
            mT_dict[i] = WeatherDTS(data = u,name = i, \
                           var_dict = variable_dictionary)

    shiftedData = pd.DataFrame(index = mT['Date'])
    for k,v in mT_dict.items():
        new_col_nm = mapped_columnname + k
        Dshifted = v.deltashift(k,new_col_nm,shifts = desired_shifts)
        shiftedData[k] = np.round(Dshifted[new_col_nm].values,3)
    return shiftedData

def convert2singlesite(data):
    wg_dict = {}
    # Columns to convert into the weather genrator
    cols=[i for i in data.columns if i not in ["Date","date","year","month","day"]]
    for i in cols:
        #print(i)
        if i != 'Date':
            u = data.loc[:,['Date',i]].copy()
            #print(u)
            wg_dict[i] = WeatherDTS(data = u,name = i)
    return wg_dict

def wg_cra(SimAnnualSeriesPrecip,ObsAnnualSeriesPrecip,ObsDailySeries,\
           precipitation_column_name,\
           multisite_dict,model_params_dict):
    """wg_cra generates multisite daily series using k-NN based WG.
    Inputs:
        SimAnnualSeriesPrecip:
            pandas Dataframe with 'Date' and annual precipitation as columns
            Note: Other than that, it will give error.
            Date columns should be named 'Date'.
            Eg:
                         Date  precip
                id
                0  1980-01-01  1340.9
                1  1981-01-01  1370.7
                2  1982-01-01  1169.2

        ObsAnnualSeriesPreicp:
            pandas Dataframe with Date and annual precipitation
            Eg. Same as SimAnnualSeriesPrecip

        ObsDailySeries:
            pandas Dataframe with Date and daily values of weather variables
            Eg:
                           Date  precip  Tmax  Tmin  Tmean
                id
                0    1980-01-01     0.0  16.8   4.8  10.80
                1    1980-01-02     1.0  16.8   4.2  10.50
                2    1980-01-03     0.0  16.8   3.9  10.35
                3    1980-01-04     0.0  15.5   0.5   8.00

        multisite_dict: python dictionary
            (a) If case of single site this is None.
            (b) In case of multisite:
                It is python dictionary in which key is varaible name and
                value is pandas dataframe for multisite for that variable.
                Each pandas dataframe contains only one type of weather variable
                Eg: var_dict = {'precip': pd_precip,
                                'tmax': pd_tmax}
                where 'pd_precip' dataframe consists of multisite precipitation data
                Eg of pd_precip:
                ---------------------------------
                     Date        p1   p2   p3
                 0  1980-01-01   0.20 0.50 0.50
                 1  1980-01-02   0.10 5.20 9.60
                ---------------------------------
                where p1, p2 and p3 are stations.

        model_params_dict: python dictionary
            Its the dictionary with following parameters (compulsory)

            model_params_dict
            {'nResamples': integer value for number of resamples,
             'nStates':  precipitation states [2 or 3],
             'wet_threshold': float value to seperate wet and dry day,
             'extreme_threshold': float value,
             'changes_in_TP': pandas dataframe of user defined changes in transition probability
                              in same format as TP with month as index
             'window_size': interger value odd integer value,
             'weights_type': One of three strings "equal","user_defined","inv_std",
             'weights': python list of weights to varibles if "weights_type" = "user_defined",
             'iState': integer either of 0,1 or 2,
             'initialWV': python list,
             'varlist': python list of string of the variables name for k-NN simulation
             }

            Description of model_params:
            nResamples:
                Number of resamples to take during creation of annual daily series
                from annual series
            nStates:
                Number of precipitation states [2 or 3]
            wet_threshold:
                It is the value to seperate wet and dry condition.
                dry condition: condition when precipitation < wet_threshold_value
                wet condition: condition when precipitation >= wet_threshold_value
                It is the value to seperate extremely wet condition from wet condition.
            extreme_threshold:
                Only applicable if number of states is 3.
                dry condition: condition when precipitation < wet_threshold_value
                wet condition: condition when precipitation >= wet_threshold_value and
                                      precipitation < extreme_threshold_value
                extremely wet condition: condition when precipitation >= extreme_threshold_value
            windowsize:
                It is the sumilation window size.
            iState:
                It is the intial state of precipitaion required for simulation.
                It is integer value either 0,1, or 2.
            initialWV:
                Initial weather vector required for simulation.

            weights_type:
                It is method for computation of distances for k-NN.
                It has three types:
                (a) "equal"
                (b) "user_defined"
                (c) "inv_std"
            weights:
                If weights_type = "user_defined"
                weights = [wt_WV1, wt_WV2, wt_WV3.....] given to weather variables

    Outputs:
        pandas dataframes

    """
    def compute_distance(x,dataseries,column):
        """ compute the distance between x and values in 'column' in dataseries
        Inputs:
            x: scalar value in this case
            dataseries: pandas dataframe with the annual precipitation values
            column: name of annual precipitation column in dataframe
        Outputs:
            X: pandas dataframe with 'dist' column
        """
        Y = dataseries.copy()
        Y['diff'] = Y[column] - x #this will broadcast
        Y['sqdiff'] = Y['diff'] * Y['diff']
        Y['dist'] = Y['sqdiff'] ** (1/2)
        Y.drop(columns = [column,'diff','sqdiff'], inplace = True)
        return Y

    # Data inputs
    SIM = SimAnnualSeriesPrecip.copy()
    OBS = ObsAnnualSeriesPrecip.copy()
    X = ObsDailySeries.copy()
    MULTI = multisite_dict
    pcolumn = precipitation_column_name

    # Model parameters
    nResam = model_params_dict['nResamples']
    nStates = model_params_dict['nStates']
    wet_threshold = model_params_dict['wet_threshold']
    extreme_threshold = model_params_dict['extreme_threshold']
    changes_in_TP = model_params_dict['changes_in_TP']
    window_size = model_params_dict['window_size']
    weights_type = model_params_dict['weights_type']
    if weights_type == "user_defined":
        wts = model_params_dict['weights']
    else:
        wts = []
    iState = model_params_dict['iState']
    initialWV = model_params_dict['initialWV']
    variable_list = model_params_dict['varlist']

    #Check if SimAnnualSeriesPrecip has only two columns and one of them is Date
    if (SIM.shape[1] == 2) & (OBS.shape[1] == 2):
        flag1 = 1
    else:
        flag1 = 0
    datatypes1 = []; datatypes2 = []
    for i in SIM.columns:
        datatypes1.append(SIM[i].dtype)
    for j in OBS.columns:
        datatypes2.append(OBS[j].dtype)
    if (np.dtype('datetime64[ns]') in datatypes1) & (np.dtype('datetime64[ns]') in datatypes2):
        flag2 = 1
    else:
        flag2 = 0
    flag3a = 0; flag3b = 0;
    for i1 in SIM.columns:
        if i1.upper() == 'DATE':
            SIM.rename(columns={i1: "Date"}, inplace = True)
            flag3a = 1
            break
    for j1 in OBS.columns:
        if j1.upper() == 'DATE':
            OBS.rename(columns={j1: "Date"}, inplace = True)
            flag3b = 1
            break
    if flag3a & flag3b:
        flag3 = 1
    else:
        flag3 = 0
    if flag1 & flag2 & flag3:
        pass
    else:
        raise ValueError('Number of columns must be 2 and one of them should be named "Date" with datetime64 type')

    precip_col_SIM = [i for i in SIM.columns if i != 'Date']
    precip_col_SIMname = precip_col_SIM[0]
    precip_col_OBS = [i for i in OBS.columns if i != 'Date']
    precip_col_OBSname = precip_col_OBS[0]

    YRS = SIM['Date'].dt.year
    # Creating the empty frame for storage of the final results
    final_series = pd.DataFrame()
    final_multisite = {}
    for keyname in multisite_dict.keys():
        final_multisite[keyname] = pd.DataFrame()

    for YR,annual_precip in zip(YRS,SIM[precip_col_SIMname].values):
        print("Simulating - Year: {}, Annual precipitation: {}".format(YR,annual_precip))
        # Computes Distances
        distances_df = compute_distance(annual_precip,OBS,precip_col_OBSname)
        # Sorting the distances in ascending order
        distances_df.sort_values(by=['dist'],inplace = True)
        # No = no of observations selected
        No = distances_df.shape[0]
        # values of k is sqrt(N) (value to change in integer value)
        k = int(np.ceil(np.sqrt(No)))
        # selected k-Nearest Neighbors
        kNNs = distances_df.head(k).copy()
        # Computing the weights using kernel function
        kNNs['rank'] = np.array(list(range(len(kNNs.index))))+1
        kNNs['ones'] = 1
        kNNs['invrank'] = kNNs['ones']/kNNs['rank']
        kNNs['kernel_wts'] = kNNs['invrank']/kNNs['invrank'].sum()
        probabilities = kNNs['kernel_wts'].values
        # here we sample nResam element
        elements = kNNs.index
        index_s0 = np.random.choice(elements,nResam,p=list(probabilities))
        # Getting the years that are resampled
        yrs0 = OBS.loc[elements,['Date']]
        sel_yrs = yrs0['Date'].dt.year.values.tolist() #sel_yrs = selected years
        # Getting the resampled years
        yrs1 = OBS.loc[index_s0,['Date']]
        resam_yrs = yrs1['Date'].dt.year.values.tolist() #resam_yrs = resampled years
        #print(resam_yrs)
        # Creating the dictionary of indicies of osbervations that have
        # the years in sel_yrs (that is selected years)
        index_dict = {}
        for i1 in sel_yrs:
           index_dict[i1] = X.loc[(X['Date'].dt.year == i1)].index
        # Now appending the indices for resampled years by extracting for index_dict
        # c will contain the indices of days for the resampled year
        # This c will be used as index to make the new dataseries and multisite dataseries
        # as inputs to weather generator
        for i2,j2 in enumerate(resam_yrs):
            if i2 == 0:
                c = index_dict[j2]
            else:
                c = np.r_[c,index_dict[j2]]

        # Creating the new dataseries conditioned on resampled_years (or c)
        maindata = X.loc[c,:].copy()
        # Now, we have to reindex the data starting from 0
        maindata.reset_index(drop = True, inplace = True)
        #maindata.drop(columns = ['id'],inplace = True)
        # Doing the same for multisite and creating the new multisite data
        # for to feed into weather generator
        new_var_dict = {}
        for key,value in MULTI.items():
            # Here mx is multisite data
            mx = value.loc[c,:].copy()
            mx.reset_index(drop = True, inplace = True)
            new_var_dict[key] = mx.copy()
        # Now steps to do
        # generate weather for year YR
        # Creating the class of WeatherDTS using wg module
        sim_name = 'Simulation_' + str(YR)

        yrwiseWG = WeatherDTS(maindata, name = sim_name, \
                            precipitation_column_name = pcolumn, \
                            var_dict = new_var_dict)
        # Setting up the model parameters
        yrwiseWG.setNoStates(nostates = nStates)
        yrwiseWG.setWetThreshold(wet_threshold_value = wet_threshold)
        yrwiseWG.setExtremeThreshold(extreme_threshold_value = extreme_threshold)
        #print("Orginal TP")
        #print(yrwiseWG.getTP())
        # If transition probability is user-defined
        if changes_in_TP is not None:
            newTP = yrwiseWG.getTP() + changes_in_TP
            yrwiseWG.setTP(newTP)
        #print("USed TP")
        #print(yrwiseWG.getTP())
        # else
            # do nothing
        yrwiseWG.getArrangedWindow(windowsize = window_size)

        sim_date_series = pd.date_range(datetime(YR,1,1),datetime(YR,12,31))
        # Simulating
        Results = yrwiseWG.simulate_kNN(simulation_dateseries = sim_date_series,\
                                 iState = iState,\
                                 initialWV = initialWV, \
                                 columnsWV = variable_list,\
                                 windowsize = window_size,\
                                 messages = False,\
                                 weights_method = weights_type,\
                                 writefile = False, \
                                 outputdir = os.getcwd(),\
                                 weights = wts)
        # Deleting the variables to free the memory
        del distances_df,No,k,kNNs,probabilities,elements,index_s0,sel_yrs,\
            resam_yrs,c,maindata,new_var_dict,yrwiseWG,sim_date_series
        #Results_collection[YR] = Results
        final_series = pd.concat([final_series,Results[1]]).copy()
        temp_result_dict = Results[2]
        #print(Results[2])
        if temp_result_dict is not None:
            for keyx,valx in temp_result_dict.items():
                z = pd.concat([final_multisite[keyx],valx]).copy()
                final_multisite[keyx] = z
        del Results

    final_series.reset_index(drop = True, inplace = True)
    for keyxx,valxx in final_multisite.items():
        final_multisite[keyxx].reset_index(drop= True,inplace = True)

    return (final_series,final_multisite)

if __name__ == "__main__":
    print("WG Loaded")
    pass