from pathlib import Path
import time

import pandas as pd
from pandas import DataFrame
import numpy as np

from nzshm_common.location import CodedLocation
from nzshm_common.grids import RegionGrid

from nzshm_hazlab.store.curves import get_hazard_v1, get_hazard
from nzshm_hazlab.data_functions import get_poe_df, compute_hazard_at_poe
from toshi_hazard_store import query


POE_DTYPE = {'lat': float, 'lon': float, 'level': float}
RESOLUTION = 0.001
SITE_LIST = 'NZ_0_1_NB_1_1'
INV_TIME = 50

def grid_locations(site_list):

    grid = RegionGrid[site_list].load()
    for loc in grid:
        yield CodedLocation(loc[0], loc[1], RESOLUTION)


def get_hazard_at_poe(hazard_id, vs30, imt, agg, poe):

    ghaz = next(query.get_gridded_hazard([hazard_id], [SITE_LIST], [vs30], [imt], [agg], [poe]))
    grid = RegionGrid[SITE_LIST]
    locations = list(
        map(lambda grd_loc: CodedLocation(grd_loc[0], grd_loc[1], resolution=grid.resolution), grid.load())
    )
    lat = [loc.lat for loc in locations]
    lon = [loc.lon for loc in locations]
    haz_poe = pd.DataFrame( data={'lat': lat, 'lon': lon, 'level': ghaz.grid_poes})
    return haz_poe