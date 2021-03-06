import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

import json
import os
import h5py
import string
import re

# set all single line variables to be displayed, not just the last line
from IPython.core.interactiveshell import InteractiveShell
InteractiveShell.ast_node_interactivity = "all"




def plot_hazard_curve(ax,site_list,imt,ref_rps,xlim,ylim,results,mean=False,median=True,show_rlz=True,intensity_type='acc'):
    
    imtls = results['metadata'][f'{intensity_type}_imtls']
    hcurves_rlzs = np.array(results['hcurves']['hcurves_rlzs'])
    hcurves_stats = np.array(results['hcurves']['hcurves_stats'])
    sites = pd.DataFrame(results['metadata']['sites'])
    quantiles = results['metadata']['quantiles']
    
    imt_idx = list(imtls.keys()).index(imt)  
    
    for i_site,site in enumerate(site_list):
        color = 'C%s'%i_site
        site_idx = sites.loc[site,'sids']
        
        if mean:
            ls = '-'
            lw = '5'
            _ = ax.plot(imtls[imt],hcurves_stats[site_idx,imt_idx,:,0],color='k',lw=lw,ls=ls)
            ls = '--'
            lw = 3
            _ = ax.plot(imtls[imt],hcurves_stats[site_idx,imt_idx,:,0],color=color,lw=lw,ls=ls,label=site)
        
        if median:
            q_idx = quantiles.index(0.5)+1
            ls = '-'
            lw = 5
            _ = ax.plot(imtls[imt],hcurves_stats[site_idx,imt_idx,:,q_idx],color='k',lw=lw,ls=ls)
            ls = '-'
            lw = 3
            _ = ax.plot(imtls[imt],hcurves_stats[site_idx,imt_idx,:,q_idx],color=color,lw=lw,ls=ls,label=site)
            
        if show_rlz:
            lw = 1
            alpha = 0.25
            [_,_,n_imtls,n_rlz] = hcurves_rlzs.shape
            segs = np.zeros([n_rlz, n_imtls, 2])
            segs[:, :, 0] = imtls[imt]
            segs[:, :, 1] = np.transpose(np.squeeze(hcurves_rlzs[site_idx,imt_idx,:,:]))
            line_segments = LineCollection(segs, color=color, alpha=alpha, lw=lw)
            _ = ax.add_collection(line_segments)
            
    for rp in ref_rps: 
        _ = ax.plot(xlim,[1/rp]*2,ls='--',color='dimgray',zorder=-1)
        _ = ax.annotate('1 / %s '%rp, [xlim[1],1/rp], ha='right',va='bottom')
    
    if mean or median:
        _ = ax.legend(handlelength=1)
    
    _ = ax.set_yscale('log')
    _ = ax.set_ylim(ylim)
    _ = ax.set_xlim(xlim)
    
    _ = ax.grid(color='lightgray')
    
    _ = ax.set_xlabel('Shaking Intensity, %s [g]'%imt)
    _ = ax.set_ylabel('Probability of Exceedance')


def plot_rfactor_curve(ax,site_list,imt,ref_rps,xlim,ylim,results,mean=False,median=True,show_rlz=True,intensity_type='acc'):
    
    rfactor_1170 = np.array([[20,  25,   50,   100, 250,  500, 1000, 2000, 2500],
                             [0.2, 0.25, 0.35, 0.5, 0.75, 1.0, 1.3,  1.7,  1.8]])
    r_rp = 500
    
    imtls = results['metadata'][f'{intensity_type}_imtls']
    hcurves_rlzs = np.array(results['hcurves']['hcurves_rlzs'])
    hcurves_stats = np.array(results['hcurves']['hcurves_stats'])
    sites = pd.DataFrame(results['metadata']['sites'])
    quantiles = results['metadata']['quantiles']
    
    hazard_rps = np.array(results['hazard_design']['hazard_rps'])
    im_hazard = np.array(results['hazard_design'][intensity_type]['im_hazard'])
    stats_im_hazard = np.array(results['hazard_design'][intensity_type]['stats_im_hazard'])
    
    imt_idx = list(imtls.keys()).index(imt)
    rp_idx = np.where(hazard_rps==r_rp)[0]
    
    for i_site,site in enumerate(site_list):
        color = 'C%s'%i_site
        site_idx = sites.loc[site,'sids']
        
        if mean:
            ls = '-'
            lw = '5'
            _ = ax.plot(imtls[imt]/stats_im_hazard[site_idx,imt_idx,rp_idx,0],hcurves_stats[site_idx,imt_idx,:,0],color='k',lw=lw,ls=ls)
            ls = '--'
            lw = 3
            _ = ax.plot(imtls[imt]/stats_im_hazard[site_idx,imt_idx,rp_idx,0],hcurves_stats[site_idx,imt_idx,:,0],color=color,lw=lw,ls=ls,label=site)
        
        if median:
            q_idx = quantiles.index(0.5)+1
            ls = '-'
            lw = 5
            _ = ax.plot(imtls[imt]/stats_im_hazard[site_idx,imt_idx,rp_idx,q_idx],hcurves_stats[site_idx,imt_idx,:,q_idx],color='k',lw=lw,ls=ls)
            ls = '-'
            lw = 3
            _ = ax.plot(imtls[imt]/stats_im_hazard[site_idx,imt_idx,rp_idx,q_idx],hcurves_stats[site_idx,imt_idx,:,q_idx],color=color,lw=lw,ls=ls,label=site)
            
        if show_rlz:
            lw = 1
            alpha = 0.25
            [_,_,n_imtls,n_rlz] = hcurves_rlzs.shape
            segs = np.zeros([n_rlz, n_imtls, 2])
            for i_rlz in range(n_rlz):
                segs[i_rlz, :, 0] = imtls[imt] / im_hazard[site_idx,imt_idx,rp_idx,i_rlz,0]
            segs[:, :, 1] = np.transpose(np.squeeze(hcurves_rlzs[site_idx,imt_idx,:,:]))
            line_segments = LineCollection(segs, color=color, alpha=alpha, lw=lw)
            _ = ax.add_collection(line_segments)
            
    for rp in ref_rps: 
        _ = ax.plot(xlim,[1/rp]*2,ls='--',color='dimgray',zorder=-1)
        _ = ax.annotate('1 / %s '%rp, [xlim[1],1/rp], ha='right',va='bottom')
        
    _ = ax.plot(rfactor_1170[1,:],1/rfactor_1170[0,:],color='k',lw=5,label='NZS1170.5')
    
    _ = ax.legend(handlelength=1)
    
    _ = ax.set_yscale('log')
    _ = ax.set_ylim(ylim)
    _ = ax.set_xlim(xlim)
    
    _ = ax.grid(color='lightgray')
    
    _ = ax.set_xlabel('R-factor, %s/%s$_{%s}$'%(imt,imt,r_rp))
    _ = ax.set_ylabel('Probability of Exceedance')


def plot_spectrum(ax,site,rp,results,color,label='site',mean=False,median=True,show_rlz=True,intensity_type='acc'):
    
    sites = pd.DataFrame(results['metadata']['sites'])
    imtls = results['metadata'][f'{intensity_type}_imtls']
    quantiles = results['metadata']['quantiles']
    
    hazard_rps = np.array(results['hazard_design']['hazard_rps'])
    im_hazard = np.array(results['hazard_design'][intensity_type]['im_hazard'])
    stats_im_hazard = np.array(results['hazard_design'][intensity_type]['stats_im_hazard'])
    
    site_idx = sites.loc[site,'sids']
    rp_idx = np.where(hazard_rps==rp)[0]

    if label=='site':
        label = site
    elif label=='rp':
        label = '1 / %s'%rp
    
    periods = [period_from_imt(imt) for imt in imtls.keys()]
    
    if mean:
        ls = '-'
        lw = '5'
        _ = ax.plot(periods,np.squeeze(stats_im_hazard[site_idx,:,rp_idx,0]),color='k',lw=lw,ls=ls)
        ls = '--'
        lw = 3
        _ = ax.plot(periods,np.squeeze(stats_im_hazard[site_idx,:,rp_idx,0]),color=color,lw=lw,ls=ls,label=label)

    if median:
        q_idx = quantiles.index(0.5)+1
        ls = '-'
        lw = 5
        _ = ax.plot(periods,np.squeeze(stats_im_hazard[site_idx,:,rp_idx,q_idx]),color='k',lw=lw,ls=ls)
        ls = '-'
        lw = 3
        _ = ax.plot(periods,np.squeeze(stats_im_hazard[site_idx,:,rp_idx,q_idx]),color=color,lw=lw,ls=ls,label=label)

    if show_rlz:
        lw = 1
        alpha = 0.25
        [_,n_imts,n_rps,n_rlz,_] = im_hazard.shape
        segs = np.zeros([n_rlz, n_imts, 2])
        segs[:, :, 0] = periods
        segs[:, :, 1] = np.transpose(np.squeeze(im_hazard[site_idx,:,rp_idx,:,0]))
        line_segments = LineCollection(segs, color=color, alpha=alpha, lw=lw)
        _ = ax.add_collection(line_segments)


def retrieve_design_intensities(results,intensity_type,design_type,imt,rp=500):
    '''
    return the design intensities based on the selected design parameters
    '''
    
    imtls = results['metadata'][f'{intensity_type}_imtls']
    imt_idx = list(imtls.keys()).index(imt)

    if design_type == 'hazard_design':
        im_idx = results[design_type]['hazard_rps'].index(rp)
        im_values_rlzs = np.squeeze(np.array(results[design_type][intensity_type]['im_hazard'])[:,imt_idx,im_idx,:,0])
        im_values_stats = np.squeeze(np.array(results[design_type][intensity_type]['stats_im_hazard'])[:,imt_idx,im_idx,:])
        
    return im_values_rlzs, im_values_stats