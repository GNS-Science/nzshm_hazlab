from zipfile import ZipFile
import itertools
import io
from collections import namedtuple
import csv
import numpy as np
import numpy.typing as npt

AXIS_MAG = 0
AXIS_DIST = 1
AXIS_TRT = 2
AXIS_EPS = 3

AXIS_NUMS = dict(
    mag = AXIS_MAG,
    dist = AXIS_DIST,
    trt = AXIS_TRT,
    eps = AXIS_EPS
)

INV_TIME = 1.0

def prob_to_rate(prob: npt.ArrayLike) -> npt.ArrayLike:

    return -np.log(1.0 - prob) / INV_TIME

def rate_to_prob(rate: npt.ArrayLike) -> npt.ArrayLike:

    return 1.0 - np.exp(-INV_TIME * rate)

def calc_mode_disagg(disagg, bins, dimensions):

    disagg = prob_to_rate(disagg)
    
    sum_dims = tuple(AXIS_NUMS[d] for d in AXIS_NUMS.keys() if d not in dimensions)
    keep_dims = tuple(d for d in AXIS_NUMS.keys() if d in dimensions)

    disagg = np.sum(disagg, axis=sum_dims)
    disagg = disagg / np.sum(disagg)
    
    mode_ind = np.where(disagg == disagg.max())
    mode = {}
    for i, dim in enumerate(keep_dims):
        mode[dim] = float(bins[AXIS_NUMS[dim]][mode_ind[i][0]])

    contribution = disagg.max()

    return mode, contribution


def calc_mean_disagg(disagg, bins):

    disagg = prob_to_rate(disagg)
    dist_mean = np.sum(np.sum(disagg, axis = (AXIS_MAG, AXIS_TRT, AXIS_EPS) ) / np.sum(disagg) * bins[AXIS_DIST])
    mag_mean = np.sum(np.sum(disagg, axis = (AXIS_DIST, AXIS_TRT, AXIS_EPS) ) / np.sum(disagg) * bins[AXIS_MAG])
    eps_mean = np.sum(np.sum(disagg, axis = (AXIS_MAG, AXIS_DIST, AXIS_TRT) ) / np.sum(disagg) * bins[AXIS_EPS])

    return dict(dist = dist_mean, mag = mag_mean, eps = eps_mean)


def disagg_to_csv(disagg, bins, header, csv_filepath):

    disagg = disagg.flatten()
    disagg_pc = prob_to_rate(disagg)
    disagg_pc = disagg_pc / np.sum(disagg_pc) * 100.0
    with open(csv_filepath, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([header])
        writer.writerow(['magnitude','distance (km)','TRT','epsilon (sigma)','annual probability of exceedance', '% contribution to hazard'])
        for i, (mag, dist, trt, eps) in enumerate(itertools.product(*bins)):
            row = (f'{mag:0.1f}', f'{dist:0.0f}', trt, f'{eps:0.3f}', f'{disagg[i]:0.3e}', f'{disagg_pc[i]:0.3e}')
            writer.writerow(row)

