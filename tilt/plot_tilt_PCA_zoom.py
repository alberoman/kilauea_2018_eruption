#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plot tiltmeters position on dem and stereonets associated to  the time series of each tiltmeters.

Created on Wed Sep 25 16:35:48 2019

@author: aroman
"""
def get_data_segment(date_start,date_end,dates):
    #extract data between to dates expresses in human format
    number_start = mdates.date2num(datetime.strptime(date_start,'%Y-%m-%d'))
    number_end = mdates.date2num(datetime.strptime(date_end,'%Y-%m-%d'))
    ind = (dates>number_start) & (dates<number_end)
    return ind,number_start,number_end

def stick_slip(tilt_filt,dates,cald_start):
    ind, _ = signal.find_peaks(tilt_filt,distance=500,prominence=10)
    time_peaks = dates[ind]
    peaks = tilt_filt[ind]
    min_peaks = []
    time_min_peaks = []
    for i in range(len(ind)-1):
        y = tilt_filt[ind[i]:ind[i+1]]
        x = dates[ind[i]:ind[i+1]]
        minimum = np.min(y)
        min_peaks.append(minimum)
        time_min_peaks.append(x[np.where(y==minimum)][0])
    y = tilt_filt[ind[-1]:]
    x = dates[ind[-1]:]
    minimum = np.min(y)
    min_peaks.append(minimum)
    time_min_peaks.append(x[np.where(y==minimum)][0])
    peaks = np.array(peaks)
    min_peaks =np.array(min_peaks[:-1])
    time_min_peaks = np.array(time_min_peaks[:-1])
    time_peaks = np.array(time_peaks)
    min_peaks = min_peaks[time_min_peaks > cald_start]
    time_min_peaks = time_min_peaks[time_min_peaks > cald_start]
    peaks = peaks[time_peaks > cald_start]
    time_peaks = time_peaks[time_peaks > cald_start]
    print('Number of collapses: ',len(time_peaks))
    plt.figure()
    plt.plot(dates,tilt_filt)
    plt.plot(dates,tilt_filt)
    plt.plot(time_peaks,peaks,'ro-')
    plt.plot(time_min_peaks,min_peaks,'bo-')
    
    return (np.diff(time_min_peaks),time_min_peaks[:-1])

import pickle
import numpy as np 
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from datetime import datetime
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
from scipy import signal
from PCA_projection_tilt import *


plt.rcParams['svg.fonttype'] = 'none'

stations = pickle.load(open('tilt_dictionary_01may.pickle','rb')) 
'''
Find mininimum and maximum time for colormap
'''
tmin = 1e+7
tmax = 0
b, a = signal.butter(2, 0.03)
months = mdates.MonthLocator()  # every month
fifteen_days = mdates.DayLocator(bymonthday=(1,15))  # labels every 15 day
days = mdates.DayLocator()  # every day
date_fmt = mdates.DateFormatter('%m/%d')
list_station = ['POO','SDH','UWD',]  #Select station to plot

date_eruption = mdates.date2num(datetime.strptime('2018-05-03','%Y-%m-%d'))
date_eruption_end = mdates.date2num(datetime.strptime('2018-08-04','%Y-%m-%d'))
date_caldera_start = mdates.date2num(datetime.strptime('2018-05-26','%Y-%m-%d'))
date_caldera_end = mdates.date2num(datetime.strptime('2018-08-03','%Y-%m-%d'))
day_beginning = '2018-07-10' #Few cycles
day_end = '2018-07-20'
#day_beginning = '2018-05-01' #all timeseries
#day_end = '2018-08-06'
first_day = mdates.date2num(datetime.strptime(day_beginning,'%Y-%m-%d'))
last_day = mdates.date2num(datetime.strptime(day_end,'%Y-%m-%d'))

for name in list_station:
    east = stations[name]['east']
    north = stations[name]['north']
    time = stations[name]['time']
    tmax = max(tmax,np.max(time))
    tmin = min(tmin,np.min(time))
    
N_station = len(list_station)

h_station = 2.5 #for few cycles
w_station = 3 #for few cycles
#h_station = 3 #For the all timeseries
#w_station = 6 #for the all time series
h_total_station = h_station * N_station

h_figure=  h_total_station 

fig_main = plt.figure(1,figsize = (w_station,h_figure))

'''
Start plotting tiltmeters position and tilt on stereonets
'''

counter = 0
for name in list_station:
    fig = plt.figure()
    gs = fig.add_gridspec(6, 6)

    east = stations[name]['east']
    north = stations[name]['north']
    time = stations[name]['time']
    '''
    Extract staff that is not nan
    '''
    indices = (np.isnan(north) == False) & (np.isnan(east) == False)
    time = time[indices] 
    east = east[indices] 
    north = north[indices]
    index,start,end = get_data_segment(day_beginning,day_end,time)
    east = east[index]
    north = north[index]
    time = time[index]
    east = (east - east[0]) 
    north = (north - north[0])
    time = time[::1]
    north = north[::1]
    east = east[::1]
    
    u1,w1,u2,w2,PCAmean = PCA_vectors(east,north) #Extract PCA vector and PCA mean
    gs = fig.add_gridspec(6, 6)
    ax1 = fig.add_subplot(gs[:, :3])    
    cm = ax1.scatter(east,north,c = time, vmin = tmin, vmax = tmax,alpha = 0.6)
    ax1.quiver(PCAmean[0],PCAmean[1],u1,w1,angles='xy', scale_units='xy', scale = 0.1)
    ax2 = fig.add_subplot(gs[:3, 4:]) 
    ax2.plot(time,east,'g')
    ax2.plot(time,north,'r')
    ax2.xaxis.set_major_formatter(date_fmt)
    ax2.xaxis.set_major_locator(months)
    ax2.xaxis.set_minor_locator(days)
    ax2.set_xlim([tmin,tmax])
    ax3 = fig.add_subplot(gs[4:, 4:]) 
    proj_max = east * u1 + north * w1
    proj_min = east * u2 + north * w2
    if not(name=='POO'):
        proj_max = signal.filtfilt(b, a, proj_max)

    ax3.plot(time,proj_max,'orange')
    ax3.plot(time,proj_min,'blue')
    ax3.xaxis.set_major_formatter(date_fmt)
    ax3.xaxis.set_major_locator(months)
    ax3.xaxis.set_minor_locator(days)
    ax3.set_xlim([tmin,tmax])
    ax1.set_title(name)
    
    ax = fig_main.add_subplot(N_station,1,counter + 1)
    ax.plot(time,proj_max,'orange')
    ax.xaxis.set_major_formatter(date_fmt)
    ax.xaxis.set_major_locator(fifteen_days)
    ax.xaxis.set_minor_locator(days)
    ax.set_xlim([first_day,last_day])
    ax.tick_params(axis='both', which='major', labelsize=12)
    ax.set_ylabel(name,fontsize = 14,fontweight = 'heavy')
    ax.xaxis.set_ticklabels([])
    counter = counter + 1
fig_main.set_tight_layout(True)
fig_main.autofmt_xdate()

plt.figure(1)
plt.savefig('Figs/principal_component_zoom.pdf')
plt.show()

