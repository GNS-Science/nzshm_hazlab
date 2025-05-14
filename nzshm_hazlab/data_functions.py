import numpy as np
from toshi_hazard_store import model, query
from pandas import DataFrame
from typing import List
from nzshm_common.location import CodedLocation
import pandas as pd
from numpy.typing import NDArray

def rp_from_poe(poe, inv_time):

    return -inv_time/np.log(1-poe)


def poe_from_rp(rp, inv_time):

    return 1 - np.exp(-inv_time/rp)


def interp_hazard(levels: NDArray, values: NDArray, poe: float, inv_time: float) -> NDArray:
    
    rp = -inv_time/np.log(1-poe)
    try:
        haz = np.exp( np.interp( np.log(1/rp), np.flip(np.log(values)), np.flip(np.log(levels)) ) )
    except:
        breakpoint()
    return haz


def compute_hazard_at_poe(levels: NDArray,values: NDArray, poe: float, inv_time: float) -> NDArray:

    # TODO: fix calls to cast args to NDArray before using this function 
    if len(values.shape) == 1:
        return interp_hazard(levels, values, poe, inv_time)
    else:
        nrows = values.shape[0]
        haz = np.empty((nrows,))
        for row_i in range(values.shape[0]):
            haz[row_i] = interp_hazard(levels, values[row_i,:], poe, inv_time)
    return haz
