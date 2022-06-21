import numpy as np
import pandas as pd

from oq_hazard_report.read_oq_hdf5 import convert_imtls_to_disp, find_site_names
from toshi_hazard_store import query
from nzshm_common.location import location


def retrieve_data(hazard_id, load_rlz=True):
    '''
    Retrieves the data and metadata from toshi-hazard-store and producing legacy data structure (designed by Anne H.).
    '''

    data = {}
    data['metadata'] = {}

    for m in query.get_hazard_metadata([hazard_id]):
        rlzs_df = pd.read_json(m.rlz_lt) 
        aggs = m.aggs
        imts = list(m.imts)
        imts.sort()
    
    data['metadata']['quantiles'] = [float(agg) for agg in aggs if (agg != 'mean')]
    data['metadata']['quantiles'].sort()
    data['metadata']['acc_imtls'] = dict.fromkeys(imts)

    sites = pd.DataFrame(list(m.locs))
    sites.columns = ['custom_site_id']

    sites = find_site_names(sites).sort_index()
    sites['sids'] = None
    for i,s in enumerate(sites.index):
        sites.loc[s,'sids'] = i
    data['metadata']['sites'] = sites.to_dict()
    
    data['metadata']['rlz_weights'] = rlzs_df['weight'].to_list()

    nsites = len(m.locs)
    nimts = len(m.imts)

    # TODO is there a better way to tget the number of levels?
    re = next(query.get_hazard_stats_curves_v2(hazard_id))
    nimtls = len(re.values[0].lvls)
    
    stats_array = np.empty((nsites,nimts,nimtls,1+len(data['metadata']['quantiles'])))
    stats_array[:] = np.nan
    
    data['hcurves'] = {}
    res = query.get_hazard_stats_curves_v2(hazard_id) # TODO one arg
    for re in res:
        site = re.loc
        for r in re.values:
            imt = r.imt 
            idx_imt = list(data['metadata']['acc_imtls'].keys()).index(imt)
            idx_site = list(data['metadata']['sites']['custom_site_id'].values()).index(site)
            
            idx_quant = data['metadata']['quantiles'].index(float(re.agg))+1 if re.agg!='mean' else 0

            data['metadata']['acc_imtls'][imt] = r.lvls
            stats_array[idx_site, idx_imt,:,idx_quant] = r.vals
    data['hcurves']['hcurves_stats'] = stats_array.tolist()

    
    if load_rlz:
        nrlzs = len(rlzs_df.index)
        rlzs_array = np.empty((nsites,nimts,nimtls,nrlzs))
        rlzs_array[:] = np.nan

        res = query.get_hazard_rlz_curves_v2(hazard_id)
        for re in res:
            site = re.loc
            idx_rlz = int(re.rlz)
            for r in re.values:
                imt = r.imt
                idx_imt = list(data['metadata']['acc_imtls'].keys()).index(imt)
                idx_site = list(data['metadata']['sites']['custom_site_id'].values()).index(site)
                
                rlzs_array[idx_site, idx_imt,:,idx_rlz] = r.vals
        data['hcurves']['hcurves_rlzs'] = rlzs_array.tolist()
    
    
    data['metadata']['disp_imtls'] = convert_imtls_to_disp(data['metadata']['acc_imtls'])
        
    return data
