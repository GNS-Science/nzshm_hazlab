from dis import dis
import numpy as np
from pathlib import Path
import itertools
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import ListedColormap, LinearSegmentedColormap, Normalize
from matplotlib.colors import LightSource

from nzshm_hazlab.disagg_data_functions import rate_to_prob, prob_to_rate

# MAGS = np.arange(5.25,10,.5)
#MAGS = np.arange(5.09745, 10.0, 0.1999)
#DISTS = np.arange(5,550,10)
#EPSS = np.arange(-3,5,2)
# EPSS = np.arange(-3.75,4.0,.5)
TRTS =  ['Active Shallow Crust', 'Subduction Interface', 'Subduction Intraslab']
AXIS_MAG = 0
AXIS_DIST = 1
AXIS_TRT = 2
AXIS_EPS = 3

CMAP = 'OrRd'
XLIM = (5,10)
YLIM = (0,350)
# YLIM = (0,600)
# >YLIM = (0,100)

cmp = cm.get_cmap(CMAP)
# white = np.array([cmp(0)[0], cmp(0)[1], cmp(0)[2], cmp(0)[3]])
white = np.array([1.0, 1.0, 1.0, 1.0])
newcolors = cmp(np.linspace(0,1,256))
newcolors[:5,:] = white
newcmp = ListedColormap(newcolors)


def plot_trt(fig, ax, disagg, bins):

    disaggs_r = prob_to_rate(disagg)
    # disagg_trt = rate_to_prob(np.sum(disaggs_r,axis=(AXIS_MAG,AXIS_DIST)) )
    disagg_trt_r = np.sum(disaggs_r,axis=(AXIS_MAG,AXIS_DIST,AXIS_EPS))
    # ax.bar(TRTS,disagg_trt/np.sum(disagg_trt) * 100)
    ax.bar(bins[AXIS_TRT],disagg_trt_r/np.sum(disagg_trt_r) * 100)
    ax.set_ylim([0, 110])
    ax.set_ylabel('% Contribution to Hazard')


def plot_mag_dist_2d(fig, ax, disagg, bins, xlim=None, ylim=None, cmin=None, cmax=None):

    disaggs_r = prob_to_rate(disagg)

    # disagg_md = rate_to_prob(np.sum(disaggs_r,axis=AXIS_TRT))
    disagg_md_r = np.sum(disaggs_r,axis=(AXIS_TRT,AXIS_EPS))
    # disagg_md = disagg_md/np.sum(disagg_md) * 100
    disagg_md_r = disagg_md_r/np.sum(disagg_md_r) * 100
    x, y = np.meshgrid(bins[AXIS_MAG], bins[AXIS_DIST])
    # pcx = ax.pcolormesh(x,y,disagg_md.transpose(),vmin=0,vmax=np.max(disagg_md),shading='auto',cmap=CMAP)
    pcx = ax.pcolormesh(x,y,disagg_md_r.transpose(),vmin=0,vmax=np.max(disagg_md_r),shading='auto',cmap=newcmp)
    fig.colorbar(pcx,label=f'% Contribution to Hazard')
    if xlim:
        ax.set_xlim(xlim)
    else:
        ax.set_xlim(XLIM)
    if ylim:
        ax.set_ylim(ylim)
    else:
        ax.set_ylim(YLIM)
    ax.set_xlabel('Magnitude')
    ax.set_ylabel('Distance (km)')

def plot_mag_dist_trt_2d(fig, ax, disagg, bins, xlim=None, ylim=None):

    xlim = XLIM if xlim is None else xlim
    ylim = YLIM if ylim is None else ylim

    disaggs_r = prob_to_rate(disagg)
    disaggs_trt0_r = prob_to_rate(disagg.copy()[:,:,0,:])
    disaggs_trt1_r = prob_to_rate(disagg.copy()[:,:,1,:])
    disaggs_trt2_r = prob_to_rate(disagg.copy()[:,:,2,:])

    disagg_md_trt0_r = np.sum(disaggs_trt0_r,axis=(AXIS_EPS-1))
    disagg_md_trt1_r = np.sum(disaggs_trt1_r,axis=(AXIS_EPS-1))
    disagg_md_trt2_r = np.sum(disaggs_trt2_r,axis=(AXIS_EPS-1))

    disagg_md_trt0_r = disagg_md_trt0_r/np.sum(disaggs_r) * 100
    disagg_md_trt1_r = disagg_md_trt1_r/np.sum(disaggs_r) * 100
    disagg_md_trt2_r = disagg_md_trt2_r/np.sum(disaggs_r) * 100

    vmax = max(np.max(disagg_md_trt0_r), np.max(disagg_md_trt1_r), np.max(disagg_md_trt2_r))

    x, y = np.meshgrid(bins[AXIS_MAG],bins[AXIS_DIST])
    pcx = ax[0].pcolormesh(x,y,disagg_md_trt0_r.transpose(),vmin=0,vmax=vmax,shading='auto',cmap=newcmp)
    pcx = ax[1].pcolormesh(x,y,disagg_md_trt1_r.transpose(),vmin=0,vmax=vmax,shading='auto',cmap=newcmp)
    pcx = ax[2].pcolormesh(x,y,disagg_md_trt2_r.transpose(),vmin=0,vmax=vmax,shading='auto',cmap=newcmp)
    ax[0].set_title(TRTS[0])    
    ax[1].set_title(TRTS[1])    
    ax[2].set_title(TRTS[2])    
    fig.colorbar(pcx, ax=ax, label=f'% Contribution to Hazard')

    for axs in ax[1:]:
        axs.get_yaxis().set_ticks([])

    for a in ax:
        a.set_xlim(xlim)
        a.set_ylim(ylim)
    # ax[0].set_xlabel('Magnitude')
    # ax[0].set_ylabel('Distance (km)')
    fig.supxlabel('Magnitude')
    fig.supylabel('Distance (km)')


def plot_mag_dist_trt_2d_v2(fig, ax, disagg, bins, xlim=None, ylim=None, cmin=None, cmax=None):

    xlim = XLIM if xlim is None else xlim
    ylim = YLIM if ylim is None else ylim

    disaggs_r = prob_to_rate(disagg)

    disagg_trt_r = np.sum(disaggs_r,axis=(AXIS_MAG,AXIS_DIST,AXIS_EPS))
    disagg_trt_r /= np.sum(disagg_trt_r)
    disagg_trt_r *= 100.0
    for i in range(3):
        ax[0,i].bar([bins[AXIS_TRT][i]], [disagg_trt_r[i]], width=0.6)
        ax[0,i].set_ylim([0, 110])
        ax[0,i].get_xaxis().set_ticks([])
        ax[0,i].set_title(TRTS[i])
        ax[0,i].set_xbound(-1.0 ,1.0)

    for axs in ax[0,1:]:
        axs.get_yaxis().set_ticks([])
    
    ax[0,0].set_ylabel('% Contribution\nto Hazard', wrap=True)

    disaggs_trt0_r = prob_to_rate(disagg.copy()[:,:,0,:])
    disaggs_trt1_r = prob_to_rate(disagg.copy()[:,:,1,:])
    disaggs_trt2_r = prob_to_rate(disagg.copy()[:,:,2,:])

    disagg_md_trt0_r = np.sum(disaggs_trt0_r,axis=(AXIS_EPS-1))
    disagg_md_trt1_r = np.sum(disaggs_trt1_r,axis=(AXIS_EPS-1))
    disagg_md_trt2_r = np.sum(disaggs_trt2_r,axis=(AXIS_EPS-1))

    disagg_md_trt0_r = disagg_md_trt0_r/np.sum(disaggs_r) * 100
    disagg_md_trt1_r = disagg_md_trt1_r/np.sum(disaggs_r) * 100
    disagg_md_trt2_r = disagg_md_trt2_r/np.sum(disaggs_r) * 100

    if cmax is None:
        cmax = max(np.max(disagg_md_trt0_r), np.max(disagg_md_trt1_r), np.max(disagg_md_trt2_r))
    if cmin is None:
        cmin = 0

    x, y = np.meshgrid(bins[AXIS_MAG],bins[AXIS_DIST])
    pcx = ax[1,0].pcolormesh(x,y,disagg_md_trt0_r.transpose(),vmin=cmin,vmax=cmax,shading='auto',cmap=newcmp)
    pcx = ax[1,1].pcolormesh(x,y,disagg_md_trt1_r.transpose(),vmin=cmin,vmax=cmax,shading='auto',cmap=newcmp)
    pcx = ax[1,2].pcolormesh(x,y,disagg_md_trt2_r.transpose(),vmin=cmin,vmax=cmax,shading='auto',cmap=newcmp)
    fig.colorbar(pcx, ax=ax, label=f'% Contribution to Hazard')

    for axs in ax[1,1:]:
        axs.get_yaxis().set_ticks([])

    for axs in ax[1,:]:
        axs.set_xlim(xlim)
        axs.set_ylim(ylim)
    ax[1,1].set_xlabel('Magnitude')
    ax[1,0].set_ylabel('Distance (km)')
    # fig.supylabel('Distance (km)')

def plot_single_mag_dist_eps(fig, ax, disagg, bins, ylim, min_mag_bin_width = 0):

    ls = LightSource(azdeg=45, altdeg=10)

    cmp = cm.get_cmap('coolwarm')
    newcolors = cmp(np.linspace(0,1,len(bins[AXIS_EPS])))
    newcmp = ListedColormap(newcolors)
    norm = Normalize(vmin=-4, vmax=4)

    disaggs_mde_r = np.sum(prob_to_rate(disagg),axis=AXIS_TRT) 
    if (bins[AXIS_MAG][1] - bins[AXIS_MAG][0]) < min_mag_bin_width:
        nbins_comb =  int(np.ceil( min_mag_bin_width/(bins[AXIS_MAG][1] - bins[AXIS_MAG][0]) ))
        nbins = int(np.ceil(len(bins[AXIS_MAG]) / nbins_comb))
        mags = np.empty((nbins,))
        merged_shape = list(disaggs_mde_r.shape)
        merged_shape[0] = nbins
        disaggs = np.empty(merged_shape)
        for i in range(nbins):
            if ((i+1)*nbins_comb) < len(bins[AXIS_MAG]):
                mags[i] = np.mean(bins[AXIS_MAG][i*nbins_comb:(i+1)*nbins_comb])
                disaggs[i] = np.mean(disaggs_mde_r[i*nbins_comb:(i+1)*nbins_comb], axis=AXIS_MAG)
            else:
                mags[i] = np.mean(bins[AXIS_MAG][i*nbins_comb:])
                disaggs[i] = np.mean(disaggs_mde_r[i*nbins_comb:], axis=AXIS_MAG)
    else:
        disaggs = disaggs_mde_r
        mags = bins[AXIS_MAG]
    disaggs = disaggs / np.sum(disaggs) * 100.0

    dind = bins[AXIS_DIST] <= ylim[1]
    disaggs = disaggs[:,dind,:]
    dists = bins[AXIS_DIST][dind]
    _xx, _yy = np.meshgrid(mags, dists)
    x, y = _xx.T.ravel(), _yy.T.ravel()
    width = 0.1    
    depth = (ylim[1]-ylim[0])/(XLIM[1] - XLIM[0]) * width
        
    bottom = np.zeros( x.shape )
    for i in range(len(bins[AXIS_EPS])):
        z0 = bottom
        z1 = disaggs[:,:,i].ravel()
        ind = z1 > 0.1
        if any(ind):
            ax.bar3d(x[ind], y[ind], z0[ind], width, depth, z1[ind], color=newcolors[i], lightsource=ls, alpha=1.0)
            bottom += disaggs[:,:,i].ravel()

    # cbar = fig.colorbar(cm.ScalarMappable(norm=norm, cmap=newcmp), ticks=EPSS, shrink = 0.3, anchor=(0.0,0.75),label='epsilon')
    # cbar = fig.colorbar(cm.ScalarMappable(norm=norm, cmap=newcmp), ticks=list(EPSS-1) + [EPSS[-1]+1], shrink = 0.3, anchor=(0.0,0.75),label='epsilon')
    deps = bins[AXIS_EPS][1] - bins[AXIS_EPS][0]
    cbar = fig.colorbar(cm.ScalarMappable(norm=norm, cmap=newcmp),
        ticks=(list(bins[AXIS_EPS] - deps/2) + [bins[AXIS_EPS][-1] + deps/2])[0:-1:2] + [bins[AXIS_EPS][-1] + deps/2],
        shrink = 0.3, anchor=(0.0,0.75),
        label='epsilon')
    ax.set_xlabel('Magnitude')
    ax.set_ylabel('Distance (km)')
    ax.set_zlabel('% Contribution to Hazard')
    ax.set_xlim(XLIM)
    ax.set_ylim(ylim)
    ax.view_init(elev=35,azim=45)
    ax.w_xaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
    ax.w_yaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
    ax.w_zaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))

    # plt.show()
    
    
def plot_mag_dist_eps(fig, disagg, bins, ylim=None, min_mag_bin_width=0):

    ax = fig.add_subplot(1,1,1,projection='3d')
    if not ylim: ylim = YLIM
    plot_single_mag_dist_eps(fig, ax, disagg, bins, ylim=ylim, min_mag_bin_width=min_mag_bin_width)


    