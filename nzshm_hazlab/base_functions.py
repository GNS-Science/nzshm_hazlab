import re

def period_from_imt(imt):
    if imt in ['PGA','PGD']:
        period = 0
    else:
        period = float(re.split('\(|\)',imt)[1])
    return period

def imt_from_period(period):
    if period == 0:
        imt = 'PGA'
    else:
        imt = f'SA({period})'
    return imt
