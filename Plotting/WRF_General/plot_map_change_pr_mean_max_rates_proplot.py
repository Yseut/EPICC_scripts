#!/usr/bin/env python
"""
#####################################################################
# Author: Daniel Argueso <daniel>
# Date:   2021-03-17T09:40:51+01:00
# Email:  d.argueso@uib.es
# Last modified by:   daniel
# Last modified time: 2021-03-17T09:40:54+01:00
#
# @Project@
# Version: x.0 (Beta)
# Description:
#
# Dependencies:
#
# Files:
#
#####################################################################
"""


import xarray as xr
import numpy as np
import netCDF4 as nc
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import proplot as plot
import argparse
import dateparser
import datetime as dt
import sys

import string
from glob import glob

import epicc_config as cfg

from matplotlib.ticker import MaxNLocator

from wrf import (to_np, getvar,get_cartopy, cartopy_xlim,GeoBounds,CoordPair,
                 cartopy_ylim, latlon_coords)



#### READING INPUT FILE ######
### Options

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--start",dest="sdatestr",type=str,help="Starting date  of the period to plot in format 2019-09-11 09:00\n partial datestrings such as 2019-09 also valid\n [default: 2019-09-11 09:00]",metavar="DATE",default='2019-09-11 09:00')
parser.add_argument("-e", "--end"  ,dest="edatestr",type=str,help="Ending date  of the period to plot in format 2019-09-11 09:00\n partial datestrings such as 2019-09 also valid\n [default: 2019-09-15 09:30]",metavar="DATE",default='2019-09-15 09:30')
parser.add_argument("-f", "--freq", dest="freq",help="Frequency to plot from 10min to monthly\n [default: hourly]",metavar="FREQ",default='01H',choices=['10MIN','01H','DAY','MON'])
parser.add_argument("-v", "--var", dest="var", help="Variable to plot \n [default: RAIN]",metavar="VAR",default='RAIN')
parser.add_argument("-r", "--reg", dest="reg", help="Region to plot \n [default: EPICC]",metavar="REG",default='EPICC',choices=cfg.reg_coords.keys())
args = parser.parse_args()

varname = args.var
sdatestr  = args.sdatestr
edatestr  = args.edatestr
reg = args.reg
freq= args.freq

sdate=dateparser.parse(sdatestr)
edate=dateparser.parse(edatestr)

###########################################################
###########################################################


labeltop={'10MIN': f'{sdate.strftime("%H:%M %d %b %Y")}-{edate.strftime("%H:%M %d %b %Y")}',
              '01H'  : f'{sdate.strftime("%H:00 %d %b %Y")}-{edate.strftime("%H:00 %d %b %Y")}',
              'DAY'  : f'{sdate.strftime("%d %b %Y")}-{edate.strftime("%d %b %Y")}',
              'MON'  : f'{sdate.strftime("%b %Y")}-{edate.strftime("%d %b %Y")}'}
units = {'10MIN': f'%',
              '01H'  : f'%',
              'DAY'  : f'%',
              'MON'  : f'%'}

def get_geoinfo():

    fileref = nc.Dataset(f'{cfg.path_wrfout}/{wrun_pre}/out/{cfg.file_ref}')
    hgt = getvar(fileref, "ter")
    lats, lons = latlon_coords(hgt)
    cart_proj = get_cartopy(hgt)

    return cart_proj,lats,lons,hgt

def map_bounds(reg):

    if reg=='EPICC':
        mbounds = None
    else:
        mbounds = GeoBounds(CoordPair(lat=cfg.reg_coords[reg][0], lon=cfg.reg_coords[reg][1]),
                               CoordPair(lat=cfg.reg_coords[reg][2], lon=cfg.reg_coords[reg][3]))
    return mbounds



###########################################################
###########################################################

wrun_pre = cfg.wrf_runs[0]
wrun_fut = wrun_pre.replace("ERA5","ERA5_CMIP6anom")

cmap = plot.Colormap('DryWet')
cart_proj,lats,lons,hgt = get_geoinfo()

mbounds = map_bounds(reg)

filesin_pre = sorted(glob(f'{cfg.path_in}/{wrun_pre}/{cfg.patt_in}_{freq}_{varname}_????-??.nc'))
fin_all_pre = xr.open_mfdataset(filesin_pre,concat_dim="time", combine="nested")

filesin_fut = sorted(glob(f'{cfg.path_in}/{wrun_fut}/{cfg.patt_in}_{freq}_{varname}_????-??.nc'))
fin_all_fut = xr.open_mfdataset(filesin_fut,concat_dim="time", combine="nested")

fin_pre = fin_all_pre.sel(time=slice(sdate,edate)).squeeze()
fin_fut = fin_all_fut.sel(time=slice(sdate,edate)).squeeze()

#tot_seconds = int((fin.isel(time=-1).time-fin.isel(time=0).time)*1e-9)
if reg!='EPICC':
    fin_reg_pre =  fin_pre.where((fin_pre.lat>=cfg.reg_coords[reg][0]) &\
                         (fin_pre.lat<=cfg.reg_coords[reg][2]) &\
                        (fin_pre.lon>=cfg.reg_coords[reg][1]) &\
                        (fin_pre.lon<=cfg.reg_coords[reg][3]),
                        drop=True)
    fin_reg_fut =  fin_fut.where((fin_fut.lat>=cfg.reg_coords[reg][0]) &\
                    (fin_fut.lat<=cfg.reg_coords[reg][2]) &\
                    (fin_fut.lon>=cfg.reg_coords[reg][1]) &\
                    (fin_fut.lon<=cfg.reg_coords[reg][3]),
                    drop=True)
else:
    fin_reg_pre = fin_pre
    fin_reg_fut = fin_fut



lmean = MaxNLocator(nbins=15).tick_values(-100,100)
lmax = MaxNLocator(nbins=15).tick_values(-100,100)

#lmean = np.arange(-50,55,5)
#lmax = np.arange(-50,55,5)

###########################################################
###########################################################

#Plotting
# Create a figure
fig, axs = plot.subplots(width=12,height=4,ncols=2,nrows=1,proj=cart_proj)
#plot.rc.abc = True
#fig.suptitle.size='x-large'

axs.format(
        suptitle="Precipitation",
        suptitlesize='xx-large',
        abc=True, abcloc='ul',
        #grid=False, xticks=25, yticks=5
    )

###########################################################
###########################################################


axs[0].add_feature(cfeature.COASTLINE,linewidth=0.5)
axs[0].add_feature(cfeature.BORDERS,linewidth=0.5)
axs[0].text(0.5,1.02,f'Mean', fontsize='x-large', horizontalalignment='center', transform=axs[0].transAxes)

mseas_pre = fin_pre[varname].mean(dim='time')
mseas_fut = fin_fut[varname].mean(dim='time')

dplot0= (mseas_fut - mseas_pre)*100./mseas_pre
m0=axs[0].contourf(to_np(lons), to_np(lats), dplot0,levels=lmean,
             transform=ccrs.PlateCarree(),
             cmap=cmap,extend='both')
axs[0].set_xlim(cartopy_xlim(hgt,geobounds=mbounds))
axs[0].set_ylim(cartopy_ylim(hgt,geobounds=mbounds))
gl0=axs[0].gridlines(color="black", linestyle="dotted",linewidth=0.5,draw_labels=True,x_inline=False, y_inline=False)#,xlocs=range(-10,10,1), ylocs=range(20,60,1))
gl0.right_labels=False
gl0.top_labels=False
#axs[0].colorbar(m0,length=0.7, loc='b',label='mm day-1')
###########################################################
###########################################################


axs[1].add_feature(cfeature.COASTLINE,linewidth=0.5)
axs[1].add_feature(cfeature.BORDERS,linewidth=0.5)
axs[1].text(0.5,1.02,f'{freq} Maximum Rate', fontsize='x-large', horizontalalignment='center', transform=axs[1].transAxes)

#axs[1].text(0.98,1.02,f'{season}', fontsize='x-large', horizontalalignment='right', transform=axs[1].transAxes)
#axs[1].text(0.98,0.02,f'{labeltop[freq]}', fontsize='medium', horizontalalignment='right', transform=axs[1].transAxes)
#CS = axs[1].contour(to_np(lons), to_np(lats), fin[varname].max('time')*tot_seconds,levels=11,linewidth=0)

xseas_pre = fin_pre[varname].max(dim='time')
xseas_fut = fin_fut[varname].max(dim='time')


dplot1 = (xseas_fut - xseas_pre)*100./xseas_pre
m1=axs[1].contourf(to_np(lons), to_np(lats), dplot1,levels=lmax,
                transform=ccrs.PlateCarree(),
                cmap=cmap,extend='both')

axs[1].set_xlim(cartopy_xlim(hgt,geobounds=mbounds))
axs[1].set_ylim(cartopy_ylim(hgt,geobounds=mbounds))


gl1=axs[1].gridlines(color="black", linestyle="dotted",linewidth=0.5,draw_labels=True, x_inline=False, y_inline=False)#,xlocs=range(-10,10,1), ylocs=range(20,60,1))
gl1.right_labels=False
gl1.top_labels=False
#axs[1].colorbar(m1,length=0.7, loc='b',label=units[freq])

fig.colorbar(m0,length=0.7, loc='b',label=units[freq],col=1)
fig.colorbar(m1,length=0.7, loc='b',label=units[freq],col=2)


#fig.subplots_adjust(left=0.1,right=0.9,top=0.9,bottom=0.15,wspace=0.1,hspace=0.2)
plt.savefig(f'{cfg.path_out}/WRF_General/Change_{varname}_{freq}_{sdate.strftime("%Y-%m-%d_%H-%M")}-{edate.strftime("%Y-%m-%d_%H-%M")}_{reg}.png',dpi=150)
