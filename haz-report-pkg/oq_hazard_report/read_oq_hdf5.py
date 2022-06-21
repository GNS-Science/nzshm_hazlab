from oq_hazard_report.base_functions import *
from nzshm_common.location import location

def retrieve_data(file_id,named_sites=True):
    '''
    retrieves the relevant data and metadata from an oq .hdf5 file and stores it in a dictionary
    '''

    data = {}

    dstore = datastore.read(file_id)
    oqparam = vars(dstore['oqparam'])
    data['metadata'] = {}
    data['metadata']['quantiles'] = oqparam['quantiles']
    
    acc_imtls = oqparam['hazard_imtls']
    data['metadata']['acc_imtls'] = acc_imtls
    data['metadata']['disp_imtls'] = convert_imtls_to_disp(acc_imtls) 
    
    if named_sites:
        data['metadata']['sites'] = find_site_names(dstore.read_df('sitecol')).to_dict()
    else:
        data['metadata']['sites'] = dstore.read_df('sitecol').to_dict()

    dstore.close()

    with h5py.File(file_id, 'r') as hf:
        data['metadata']['rlz_weights'] = hf['weights'][:].tolist()
        
        data['hcurves'] = {}
        data['hcurves']['hcurves_rlzs'] = np.moveaxis(hf['hcurves-rlzs'][:], 1, 3).tolist() #[site,imt,imtl,realizations (source*gmpe) ] (order after moveaxis)
        data['hcurves']['hcurves_stats'] = np.moveaxis(hf['hcurves-stats'][:], 1, 3).tolist() #[site,imt,imtl,mean+quantiles] (order after moveaxis)

    return data

def convert_imtls_to_disp(acc_imtls):
    '''
    converts the intensity measure types and levels to spectral displacements
    '''
    disp_imtls = {}
    for acc_imt in acc_imtls.keys():
        period = period_from_imt(acc_imt)
        disp_imt = acc_imt.replace('A','D')

        disp_imtls[disp_imt] = acc_to_disp(np.array(acc_imtls[acc_imt]),period).tolist()
        
    return disp_imtls

def find_site_names(sites,dtol=0.001):
    '''
    sets site names as the index for the sites dataframe
    '''

    def name_from_latlon(lat, lon, location_codes, dtol):
        lat_idx = (location_codes['latitude'] >= lat-dtol) & (location_codes['latitude'] <= lat+dtol)
        lon_idx = (location_codes['longitude'] >= lon-dtol) & (location_codes['longitude'] <= lon+dtol)
        idx = lat_idx & lon_idx
        if not True in idx.values:
            return f'Lat: {lat:.2f}, Lon: {lon:.2f}'
        return location_codes[lat_idx & lon_idx].index

    location_codes = {}
    for loc in location.LOCATIONS:
        location_codes[loc['name']] = {'id':loc['id'],'latitude':loc['latitude'],'longitude':loc['longitude']}
    location_codes = pd.DataFrame(location_codes).transpose()


    sites.loc[0,'name'] = 'dummy'
    if 'custom_site_id' in sites:
        for i in sites.index:
            id_idx = location_codes['id'] == sites.loc[i,'custom_site_id']
            if True in id_idx.values:
                try:
                    sites.loc[i,'name'] = location_codes[id_idx].index
                except: #handle duplicate custom_site_ids by looking up by lat lon
                    sites.loc[i,'name'] = name_from_latlon(sites.loc[i,'lat'], sites.loc[i,'lon'], location_codes, dtol)
            else: #if it's not on the list just use the custom_site_id
                sites.loc[i,'name'] = sites.loc[i,'custom_site_id']
    else:
        for i in sites.index:
            sites.loc[i,'name'] = name_from_latlon(sites.loc[i,'lat'], sites.loc[i,'lon'], location_codes, dtol)
    
    return sites.set_index('name')

