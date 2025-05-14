import numpy as np
import pandas as pd
from pandas import DataFrame
from matplotlib.pylab import Axes, Line2D
from typing import List, Dict
import matplotlib.pyplot as plt
from nzshm_common.location import CodedLocation
from nzshm_hazlab.base_functions import period_from_imt, imt_from_period
from nzshm_hazlab.data_functions import ( 

    # calculate_agg,
    compute_hazard_at_poe,
    rp_from_poe,
    poe_from_rp,
    rp_from_poe
)

from uuid import RESERVED_FUTURE
from matplotlib.collections import LineCollection

from mpl_toolkits.axes_grid1.inset_locator import inset_axes

AXIS_FONTSIZE = 28
TICK_FONTSIZE = 22

def set_plot_formatting():    
    # set up plot formatting
    SMALL_SIZE = 12
    MEDIUM_SIZE = 16
    BIGGER_SIZE = 25

    plt.rc('font', size=SMALL_SIZE)  # controls default text sizes
    plt.rc('axes', titlesize=MEDIUM_SIZE)  # fontsize of the axes title
    plt.rc('axes', labelsize=MEDIUM_SIZE)  # fontsize of the x and y labels
    plt.rc('xtick', labelsize=SMALL_SIZE)  # fontsize of the tick labels
    plt.rc('ytick', labelsize=SMALL_SIZE)  # fontsize of the tick labels
    plt.rc('legend', fontsize=SMALL_SIZE)  # legend fontsize
    plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title


def plot_hazard_curve(
        hazard_data: DataFrame,
        location: CodedLocation,
        imt: str,
        ax: Axes,
        xlim: List[float],
        ylim: List[float],
        central: str ='mean',
        bandw: Dict[str,str] = {},
        ref_lines: List[dict] = [],
        quants: List[str] = [],
        xscale: str ='log',
        custom_label: str = '',
        color: str = '',
        title: str = '',
        linestyle: str = '-'
) -> List[Line2D]:
    
    lat, lon = location.code.split('~')

    hd_filt = hazard_data.loc[ (hazard_data['imt'] == imt) & (hazard_data['lat'] == lat) & (hazard_data['lon'] == lon)]

    levels = hd_filt.loc[ hazard_data['agg'] == central]['level'].iloc[0]
    values = hd_filt.loc[ hazard_data['agg'] == central]['apoe'].iloc[0]

    clr = color if color else 'k'

    label = custom_label if custom_label else central
    lh, = ax.plot(levels,values,color=clr,lw=3,label=label, linestyle=linestyle)

    clr = color if color else 'b'
    alpha1 = 0.25
    alpha2 = 0.8
    if bandw: #{'u1':'0.8,'u2':'0.95', ...}
        
        bandw_data = {}
        for k,v in bandw.items():
            values = hd_filt.loc[ hazard_data['agg'] == v]['apoe'].iloc[0]
            bandw_data[k] = values
        
        ax.fill_between(levels, bandw_data['upper1'], bandw_data['lower1'],alpha = alpha1, color=clr)
        ax.plot(levels, bandw_data['upper2'],color=clr,lw=1)
        ax.plot(levels, bandw_data['lower2'],color=clr,lw=1)
        # ax.plot(levels, bandw_data['upper2'],linestyle='--',color=clr,lw=1)
        # ax.plot(levels, bandw_data['lower2'],linestyle='--',color=clr,lw=1)
        # ax.plot(levels, bandw_data['upper1'],color=clr,lw=2)
        # ax.plot(levels, bandw_data['lower1'],color=clr,lw=2)
    if quants:
        for quant in quants:
            levels = hd_filt.loc[ hazard_data['agg'] == quant]['level'].iloc[0]
            values = hd_filt.loc[ hazard_data['agg'] == quant]['apoe'].iloc[0]
            ax.plot(levels,values,'b',alpha=alpha2,lw=1,label=quant)


    for ref_line in ref_lines:
        if ref_line['type'] == 'poe':
            poe = ref_line['poe']
            inv_time = ref_line['inv_time']
            rp = rp_from_poe(poe, inv_time)
        elif ref_line['type'] == 'rp':
            inv_time = ref_line['inv_time']
            rp = ref_line['rp']
            poe = poe_from_rp(poe, inv_time)

        text = f'{poe*100:.0f}% in {inv_time:.0f} years (1/{rp:.0f})'
        
        _ = ax.plot(xlim,[1/rp]*2,ls='--',color='dimgray',zorder=-1)
        # _ = ax.annotate(text, [xlim[1],1/rp], ha='right',va='bottom')
        if xscale == 'log':
            _ = ax.annotate(text, [xlim[0],1/rp], ha='left',va='bottom', fontsize=TICK_FONTSIZE*0.8)
        else:
            _ = ax.annotate(text, [xlim[1],1/rp], ha='right',va='bottom', fontsize=TICK_FONTSIZE*0.8)

    # if not bandw:
    _ = ax.legend(handlelength=2)

    if xscale == 'log':
        _ = ax.set_xscale('log')
    _ = ax.set_yscale('log')
    _ = ax.set_ylim(ylim)
    _ = ax.set_xlim(xlim)
    _ = ax.set_xlabel('Shaking Intensity, %s [g]'%imt, fontsize=AXIS_FONTSIZE)
    _ = ax.set_ylabel('Annual Probability of Exceedance', fontsize=AXIS_FONTSIZE)
    _ = ax.tick_params(axis='both', which='major', labelsize=TICK_FONTSIZE)
    _ = ax.grid(color='lightgray')  

    if title:
        ax.set_title(title)

    return lh, levels

            
def plot_spectrum(
        hazard_data: DataFrame,
        location: CodedLocation,
        poe: float,
        inv_time: float,
        ax: Axes,
        central: str='mean',
        bandw: bool=False,
        color: str='b'
):
    #TODO: this is slow!

    lat, lon = location.split('~')

    hd_filt = hazard_data.loc[ (hazard_data['lat'] == lat) & (hazard_data['lon'] == lon)]


    imts = set(hazard_data['imt'])
    periods = [period_from_imt(imt) for imt in imts]
    periods.sort()
    imts = [imt_from_period(period) for period in periods]

    # lvls = list(set(hazard_data['level']))
    # lvls.sort()


    if bandw:
        quantiles = dict(
                        upper1 = 0.9,
                        lower1 = 0.1,
                        upper2 = 0.975,
                        lower2 = 0.025,
                        )
        hazard = {}
        for k,quant in quantiles.items():
            haz = []
            for imt in imts:
                # vals = calculate_agg(hazard_data,location,imt,quant)
                vals = hd_filt.loc[(hd_filt['imt'] == imt) & (hd_filt['agg'] == str(quant)),'apoe'].to_numpy()[0]
                lvls = hd_filt.loc[(hd_filt['imt'] == imt) & (hd_filt['agg'] == str(quant)),'level'].to_numpy()[0]
                haz.append(compute_hazard_at_poe(lvls,vals,poe,inv_time))
            hazard[k] = haz
        ax.fill_between(periods,hazard['upper1'],hazard['lower1'],alpha = 0.5, color=color)
        ax.plot(periods, hazard['upper2'],color=color,lw=1)
        ax.plot(periods, hazard['lower2'],color=color,lw=1)
    # else:
    #     da = 0.01
    #     aggs = np.arange(0,1.0+da,da)
    #     for i,agg in enumerate(aggs):
    #         # alpha = min(1.0,(len(aggs)/2.0 - np.abs(len(aggs)/2.0 - i)) / (len(aggs)/2.0)+0.25)
    #         # alpha = min(1.0,-(2.0/len(aggs))**2 * (i-len(aggs)/2.0)**2  + 1.2)
    #         # alpha = max(0.0,(len(aggs)/2.0 - np.abs(len(aggs)/2.0 - i)) / (len(aggs)/2.0)-0.1)
    #         alpha = max(0.0,(len(aggs)/2.0 - np.abs(len(aggs)/2.0 - i)) / (len(aggs)/2.0))
    #         hazard = []
    #         for imt in imts:
    #             breakpoint()
    #             lvls = hd_filt.loc[(hd_filt['imt'] == imt) & (hd_filt['agg'] == str(quant)),'level']
    #             lvls = hd_filt.loc[(hd_filt['imt'] == imt) & (hd_filt['agg'] == str(quant)),'level']
    #             # vals = calculate_agg(hazard_data,location,imt,agg)
    #             hazard.append(compute_hazard_at_poe(lvls,vals,poe,inv_time))
    #         ax.plot(periods,hazard,color=str(alpha),alpha=0.6,lw=1)


    hazard = []
    for imt in imts:
        values = hd_filt.loc[(hd_filt['imt'] == imt) & (hd_filt['agg'] == central),'apoe'].item()
        levels = hd_filt.loc[(hd_filt['imt'] == imt) & (hd_filt['agg'] == central),'level'].item()
        hazard.append(compute_hazard_at_poe(levels,values,poe,inv_time))
    print(periods)
    print(hazard)

    lh = ax.plot(periods, hazard, color=color, alpha=0.8,lw=2)
    lh = lh[0]

    xlim = [0, max(periods)]
    ylim = ax.get_ylim()
    ylim = [0, ylim[1]]
    _ = ax.set_ylim(ylim)
    _ = ax.set_xlim(xlim)
    _ = ax.set_xlabel('Period [s]', fontsize=AXIS_FONTSIZE)
    _ = ax.set_ylabel('Shaking Intensity [g]', fontsize=AXIS_FONTSIZE)
    _ = ax.tick_params(axis='both', which='major', labelsize=TICK_FONTSIZE)
    _ = ax.grid(color='lightgray')


    return lh
