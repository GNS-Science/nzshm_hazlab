import numpy as np
from toshi_hazard_store import model, query

def get_lv(toshi_id,imt,site_list,aggrigations):
    
    xy = {}
    vs30 = 250 #TODO Vs30 arg
    
    res = query.get_hazard_curves_stats(toshi_id, vs30, imt, site_list, aggrigations)

    for site in site_list:
        xy[site] = {}
        
    for r in res:
        xy[r.location_code][r.aggregation] = np.array([[p.level,p.value] for p in r.lvl_val_pairs])

    return xy
    