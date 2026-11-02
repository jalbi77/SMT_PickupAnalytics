"""Nachvollziehbare Aggregation ohne externe Zugriffe."""
import numpy as np
import pandas as pd

COUNTS = ['RejectParts', 'NoPickupCount', 'PickupErrors', 'VisionErrors']
SPECS = {
    'Bauteile': ('DeviceComment', 'FeedCount', [3, 1, 2, 1]),
    'Feeder': ('Fidl', 'FeedCount', [0, 1, 2, 0]),
    'Saugdüsen': ('Nid', 'PickupCount', [3, 2, 3, 1]),
}


def calculate(raw, category):
    key, denominator, weights = SPECS[category]
    required = [key, denominator, *COUNTS]
    missing = set(required) - set(raw.columns)
    if missing:
        raise ValueError('Fehlende Spalten: ' + ', '.join(sorted(missing)))
    df = raw[required].copy()
    for col in [denominator, *COUNTS]:
        df[col] = pd.to_numeric(df[col], errors='raise')
        if df[col].isna().any() or not np.isfinite(df[col]).all() or (df[col] < 0).any():
            raise ValueError(f'Ungültige Zählerwerte in {col}')
    missing_ids = int((df[key].isna() | df[key].astype('string').str.strip().eq('')).sum())
    df = df.loc[df[key].notna() & df[key].astype('string').str.strip().ne('')]
    result = df.groupby(key, as_index=False)[[denominator, *COUNTS]].sum()
    result['WeightedErrors'] = sum(result[col] * weight for col, weight in zip(COUNTS, weights))
    relevant = [col for col, weight in zip(COUNTS, weights) if weight]
    result['UnweightedErrors'] = result[relevant].sum(axis=1)
    result['ErrorIndex'] = result['WeightedErrors'] / result[denominator].where(result[denominator] > 0)
    result['Status'] = np.where(result[denominator] > 0, 'Bewertbar', 'Nicht bewertbar: Nenner 0')
    return result.sort_values('ErrorIndex', ascending=False, na_position='last'), missing_ids
