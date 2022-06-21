from oq_hazard_report.base_functions import *

from uuid import RESERVED_FUTURE
from matplotlib.collections import LineCollection

#TODO runs slowly; any performance imporvements to be had?

def plot_hazard_curve(ax, site_list, imt, xlim, ylim, results,
                        ref_lines=None,
                        legend_type='site',
                        mean=False,
                        median=True,
                        quant=False,
                        show_rlz=True,
                        intensity_type='acc',
                        xscale='linear',custom_label=None, color=None):
    """
    plot hazard curves

    Parameters
    ----------
    ax:             matplotlib.axes
                    axis handle to plot to
    site_list:      list of str
                    sites to plot from the results dictionary
    imt:            list of str
                    intensity masure types to plot
    xlim:           list of float
                    x-limits for plot
    ylim:           list of float
                    y-limits for plot
    results:        dict
                    dictionary containing hazard data
    ref_lines:      dict, optional
                    draw lines at PoE or 1/(return period).
                    list of dicts. each dict contains a key called 'type' = ('poe' | 'rp')
                    if type=='poe', then other dict keys are 'poe' = poe and 'inv_time' = investigation time
                    if type=='rp', then other dict key is 'rp' = repeat period
    legend_type:    str, optional
                    specify how curves are colored and noted in legend 'site' or 'quant'
    mean:           bool, optional
                    turn on mean plotting
    median:         bool, optional
                    turn on median plotting
    quant:          bool, optional
                    turn on quantile plotting
    show_rlz:       bool, optional
                    show realizations
    intensity_type: str, optional
                    'acc' or 'disp'
    xscale:         str, optional
                    'linear' or 'log'
    """
    
    imtls = results['metadata'][f'{intensity_type}_imtls']
    
    hcurves_stats = np.array(results['hcurves']['hcurves_stats'])
    sites = pd.DataFrame(results['metadata']['sites'])
    quantiles = results['metadata']['quantiles']

    if show_rlz:
        hcurves_rlzs = np.array(results['hcurves']['hcurves_rlzs']) 
    
    imt_idx = list(imtls.keys()).index(imt)  
    
    for i_site,site in enumerate(site_list):
        if not color:
            color = 'C%s'%i_site
                
        if legend_type == 'quant':
            color_m = 'r'
        else:
            color_m = color

        site_idx = sites.loc[site,'sids']
        
        if mean:
            if custom_label:
                label = custom_label
            else:
                if legend_type == 'site':
                    label = site
                elif legend_type == 'quant':
                    label = 'mean'

            ls = '-'
            lw = 5
            _ = ax.plot(imtls[imt],hcurves_stats[site_idx,imt_idx,:,0],color='k',lw=lw,ls=ls)
            ls = '-.'
            lw = 3
            _ = ax.plot(imtls[imt],hcurves_stats[site_idx,imt_idx,:,0],color=color_m,lw=lw,ls=ls,label=label)
        
        if median:
            if custom_label:
                label = custom_label
            else:
                if legend_type == 'site':
                    label = site
                elif legend_type == 'quant':
                    label = 'median (p50)'

            q_idx = quantiles.index(0.5)+1
            ls = '-'
            lw = 4
            # _ = ax.plot(imtls[imt],hcurves_stats[site_idx,imt_idx,:,q_idx],color='k',lw=lw,ls=ls)
            ls = '-'
            lw = 3
            _ = ax.plot(imtls[imt],hcurves_stats[site_idx,imt_idx,:,q_idx],color=color_m,lw=lw,ls=ls,label=label)

        if quant:
            if legend_type == 'quant':
                label = 'p10/p90'
            elif legend_type == 'site':
                label = ''

            ls = '--'
            lw = 1.5
            q_idx = quantiles.index(0.1)+1
            _ = ax.plot(imtls[imt],hcurves_stats[site_idx,imt_idx,:,q_idx],color=color_m,lw=lw,ls=ls,label=label)
            q_idx = quantiles.index(0.9)+1
            _ = ax.plot(imtls[imt],hcurves_stats[site_idx,imt_idx,:,q_idx],color=color_m,lw=lw,ls=ls)
            
        if show_rlz:
            lw = 1
            alpha = 0.25
            [_,_,n_imtls,n_rlz] = hcurves_rlzs.shape
            segs = np.zeros([n_rlz, n_imtls, 2])
            segs[:, :, 0] = imtls[imt]
            segs[:, :, 1] = np.transpose(np.squeeze(hcurves_rlzs[site_idx,imt_idx,:,:]))
            line_segments = LineCollection(segs, color=color, alpha=alpha, lw=lw)
            _ = ax.add_collection(line_segments)
            
    for ref_line in ref_lines:
        if ref_line['type'] == 'poe':
            poe = ref_line['poe']
            inv_time = ref_line['inv_time']
            rp = -inv_time/np.log(1-poe)
        elif ref_line['type'] == 'rp':
            inv_time = ref_line['inv_time']
            rp = ref_line['rp']
            poe = 1 - np.exp(-inv_time/rp)

        text = f'{poe*100:.0f}% in {inv_time:.0f} years (1/{rp:.0f})'
        
        _ = ax.plot(xlim,[1/rp]*2,ls='--',color='dimgray',zorder=-1)
        _ = ax.annotate(text, [xlim[1],1/rp], ha='right',va='bottom')

    if mean or median:
        _ = ax.legend(handlelength=2)
    
    _ = ax.set_yscale('log')
    if xscale == 'log':
        _ = ax.set_xscale('log')
    _ = ax.set_ylim(ylim)
    _ = ax.set_xlim(xlim)
    
    _ = ax.grid(color='lightgray')
    
    if intensity_type=='acc':
        _ = ax.set_xlabel('Shaking Intensity, %s [g]'%imt)
    elif intensity_type=='disp':
        _ = ax.set_xlabel('Displacement, %s [m]'%imt)
    _ = ax.set_ylabel('Annual Probability of Exceedance')


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


def plot_spectrum(ax,site,rp,results,inv_time,legend_type='site',color='C0',mean=False,median=True,quant=False,show_rlz=True,intensity_type='acc'):
    
    sites = pd.DataFrame(results['metadata']['sites'])
    imtls = results['metadata'][f'{intensity_type}_imtls']
    quantiles = results['metadata']['quantiles']
    
    hazard_rps = np.array(results['hazard_design']['hazard_rps'])
    im_hazard = np.array(results['hazard_design'][intensity_type]['im_hazard'])
    stats_im_hazard = np.array(results['hazard_design'][intensity_type]['stats_im_hazard'])
    
    site_idx = sites.loc[site,'sids']
    rp_idx = np.where(hazard_rps==rp)[0]

    poe = 1-np.exp(-inv_time/rp)
    tmp = f'{poe*100:.0f}_in_{inv_time:.0f}'

    if legend_type=='site':
        label = site
        color_m = color
    elif legend_type=='quant':
        color_m = 'r'
    
    periods = [period_from_imt(imt) for imt in imtls.keys()]
    
    if mean:
        if legend_type == 'quant':
            label = 'mean'

        ls = '-'
        lw = '5'
        _ = ax.plot(periods,np.squeeze(stats_im_hazard[site_idx,:,rp_idx,0]),color='k',lw=lw,ls=ls)
        ls = '-.'
        lw = 3
        _ = ax.plot(periods,np.squeeze(stats_im_hazard[site_idx,:,rp_idx,0]),color=color_m,lw=lw,ls=ls,label=label)

    if median:
        if legend_type == 'quant':
            label = 'median (p50)'

        q_idx = quantiles.index(0.5)+1
        ls = '-'
        lw = 5
        _ = ax.plot(periods,np.squeeze(stats_im_hazard[site_idx,:,rp_idx,q_idx]),color='k',lw=lw,ls=ls)
        ls = '-'
        lw = 3
        _ = ax.plot(periods,np.squeeze(stats_im_hazard[site_idx,:,rp_idx,q_idx]),color=color_m,lw=lw,ls=ls,label=label)

    if quant:
            if legend_type == 'quant':
                label10 = 'p10'
                label90 = 'p90'
            elif legend_type == 'site':
                label10 = ''
                label90 = ''

            ls = '--'
            lw = 2

            q_idx = quantiles.index(0.1)+1
            _ = ax.plot(periods,np.squeeze(stats_im_hazard[site_idx,:,rp_idx,q_idx]),color=color_m,lw=lw,ls=ls,label=label10)
            q_idx = quantiles.index(0.9)+1
            _ = ax.plot(periods,np.squeeze(stats_im_hazard[site_idx,:,rp_idx,q_idx]),color=color_m,lw=lw,ls=ls,label=label90)

    if show_rlz:
        lw = 1
        alpha = 0.25
        [_,n_imts,n_rps,n_rlz,_] = im_hazard.shape
        segs = np.zeros([n_rlz, n_imts, 2])
        segs[:, :, 0] = periods
        segs[:, :, 1] = np.transpose(np.squeeze(im_hazard[site_idx,:,rp_idx,:,0]))
        line_segments = LineCollection(segs, color=color, alpha=alpha, lw=lw)
        _ = ax.add_collection(line_segments)

    if mean or median:
        _ = ax.legend(handlelength=2)
    
    _ = ax.grid(color='lightgray')
        
    _ = ax.set_xlabel('Period [s]')
    if intensity_type=='acc':
        _ = ax.set_ylabel('Shaking Intensity [g]')
    elif intensity_type=='disp':
        _ = ax.set_ylabel('Displacement [m]')

    xlim = [0, max(periods)]
    ylim = ax.get_ylim()
    ylim = [0, ylim[1]]
    _ = ax.set_ylim(ylim)
    _ = ax.set_xlim(xlim)


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


