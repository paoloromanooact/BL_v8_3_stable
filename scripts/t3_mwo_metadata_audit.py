"""Read-only audit of the T3 MWO candidate pool from saved FITS headers and DPD group metadata.

Uses dates, positions, areas and instrument metadata. Header ephemeris decisions and magnetic-pixel failures
remain outside this audit. The counts describe capacity before measurement, with DPD hemispheres.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import hashlib
import json
import math
from pathlib import Path
import re
import numpy as np
import pandas as pd

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda : f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()

def number(x):
    try:
        value = float(x)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None

def classification(dx, dy):
    (dx, dy) = (number(dx), number(dy))
    if dx is None or dy is None:
        return 'R0'
    if dx < 11 and dy < 15:
        return 'R1'
    if 11 <= dx <= 14 and dy >= 18:
        return 'R2'
    if dx >= 13.5 and 15 <= dy <= 19:
        return 'R3'
    return 'R0'

def filename_time(name, year, tavg):
    match = re.search('(?:^|/)m(\\d{2})(\\d{2})(\\d{2})_', name, re.I)
    if match is None:
        match = re.search('_0(\\d{2})(\\d{2})(\\d{2})_', name)
    hours = number(tavg)
    if match is None or hours is None:
        return None
    (yy, mm, dd) = map(int, match.groups())
    yyyy = min((1900 + yy, 2000 + yy), key=lambda y: abs(y - year))
    try:
        return datetime(yyyy, mm, dd) + timedelta(hours=hours)
    except ValueError:
        return None

def rotation(t):
    jd = pd.Timestamp(t).to_julian_date()
    n = int(math.floor((jd - 2398140.227) / 27.2752316))

    def start(c):
        m = math.radians(281.96 + 26.882476 * c)
        return 2398140.227 + 27.2752316 * c + 0.1454 * math.sin(m) - 0.0085 * math.sin(2 * m) - 0.0141 * math.cos(2 * m)
    while start(n) > jd:
        n -= 1
    while start(n + 1) <= jd:
        n += 1
    return n

def cycle(t):
    value = 20
    for (c, bound) in ((21, '1976-03-01'), (22, '1986-09-01'), (23, '1996-08-01'), (24, '2008-12-01')):
        if str(t)[:10] >= bound:
            value = c
    return value

def audit(root):
    root = Path(root)
    headers = root / 'results/MWO_HEADER_INVENTORY'
    meta = json.loads((headers / 'META.json').read_text())
    header_hashes = {name: digest(headers / name) == expected for (name, expected) in meta['products_sha256'].items()}
    data = root / 'data/sharp/external_DPD_20261118'
    manifest = {name: expected for (expected, name) in (line.split() for line in (data / 'SHA256SUMS.txt').read_text().splitlines())}
    input_hashes = {name: digest(data / name) == manifest[name] for name in ['dailyDPD1974_2016.txt', 'DPDformat.txt'] + [f'gDPD{y}.txt' for y in range(1974, 2013)]}
    h = pd.read_csv(headers / 'HEADERS.csv.gz', low_memory=False)
    fe = h[h.family.isin(['legacy_MP00_5250', 'modern_fe1'])].copy()
    by_day = defaultdict(list)
    instrument_counts = Counter()
    ignored = Counter()
    for row in fe.to_dict('records'):
        ot = filename_time(row['member'], row['archive_year'], row['TAVG-UT'])
        if ot is None:
            ignored['missing_or_invalid_time'] += 1
            continue
        day = ot.strftime('%Y-%m-%d')
        if not '1974-01-01' <= day < '2013-01-01':
            continue
        if row['family'] == 'legacy_MP00_5250':
            epoch = {0: 'E1', 256: 'E2', 1280: 'E3', 1281: 'E4', 1282: 'E5', 1283: 'E6'}.get(number(row['MRKMOD']))
        else:
            epoch = 'E7' if day < '1996-04-10' else 'E8'
        if epoch is None:
            ignored['unassigned_epoch'] += 1
            continue
        res = classification(row['DXB_OBS'], row['DYB_OBS'])
        item = dict(member=row['member'], ot=ot, epoch=epoch, res=res)
        by_day[day].append(item)
        instrument_counts[f'{epoch}/{res}'] += 1
    groups = {}
    parsing = Counter()
    for y in range(1974, 2013):
        for line in (data / f'gDPD{y}.txt').read_text().splitlines():
            if not line.startswith('g '):
                continue
            parsing['group_rows'] += 1
            try:
                (yy, mo, dd, hh, mi, ss) = [int(line[a:b]) for (a, b) in ((2, 6), (7, 9), (10, 12), (13, 15), (16, 18), (19, 21))]
                t = datetime(yy, mo, dd, hh, mi) + timedelta(seconds=ss)
                area = int(line[53:58])
                lat = float(line[59:65])
                lon = float(line[66:72])
                lcm = float(line[73:79])
            except ValueError:
                parsing['unparsed'] += 1
                continue
            if ss == 60:
                parsing['seconds_60_rows'] += 1
            if max(lat, lon, lcm) > 900:
                parsing['intermittent_rows'] += 1
                continue
            key = (t.strftime('%Y-%m-%d'), line[22:28].strip())
            if key in groups:
                parsing['duplicate_day_group'] += 1
            if key not in groups or area > groups[key]['area']:
                groups[key] = dict(day=key[0], noaa=key[1], t=t, area=area, lat=lat, lon=lon, lcm=lcm)
    per_day = defaultdict(list)
    for g in groups.values():
        per_day[g['day']].append(g)
    selected = {}
    eligible = Counter()
    ranks = {'R1': 0, 'R2': 1, 'R3': 2, 'R0': 3}
    for (day, rs) in per_day.items():
        if not '1974-01-01' <= day < '2013-01-01':
            continue
        lat = np.array([g['lat'] for g in rs])
        lon = np.array([g['lon'] for g in rs])
        neighbour = (abs(lat[:, None] - lat[None, :]) <= 6) & (abs((lon[:, None] - lon[None, :] + 180) % 360 - 180) <= 8)
        np.fill_diagonal(neighbour, False)
        for (i, g) in enumerate(rs):
            if g['area'] < 1 or abs(g['lat']) > 45:
                continue
            eligible['eligible_group_days'] += 1
            if day not in by_day:
                eligible['group_days_without_saved_magnetogram'] += 1
                continue
            mag = min(by_day[day], key=lambda m: (ranks[m['res']], abs((m['ot'] - g['t']).total_seconds()), m['ot'], m['member']))
            for label in ('all', 'isolated'):
                if label == 'isolated' and neighbour[i].any():
                    continue
                eligible[label + '_candidate_days'] += 1
                key = (label, g['noaa'])
                if key not in selected or (abs(g['lcm']), day) < (abs(selected[key]['lcm']), selected[key]['day']):
                    selected[key] = dict(g, mag=mag)
    summary = {}
    for label in ('all', 'isolated'):
        rs = [g for ((s, _), g) in selected.items() if s == label]
        summary[label] = dict(n_groups=len(rs), n_distinct_CR=len({rotation(g['mag']['ot']) for g in rs}), per_cycle_hem=dict(sorted(Counter((f"{cycle(g['day'])}{('N' if g['lat'] >= 0 else 'S')}" for g in rs)).items())), per_epoch=dict(sorted(Counter((g['mag']['epoch'] for g in rs)).items())), per_epoch_hem=dict(sorted(Counter((f"{g['mag']['epoch']}{('N' if g['lat'] >= 0 else 'S')}" for g in rs)).items())), per_resolution=dict(sorted(Counter((g['mag']['res'] for g in rs)).items())))
    fe_period = fe[fe.archive_year.between(1974, 2012)]
    hours = pd.to_numeric(fe_period['TAVG-UT'], errors='coerce')
    time_meta = dict(n_headers=len(fe_period), n_tavg_ge_24=int((hours >= 24).sum()), n_tavg_negative=int((hours < 0).sum()), n_tavg_missing=int(hours.isna().sum()), max_tavg=float(hours.max()), negative_headers=fe_period.loc[hours < 0, ['member', 'TAVG-UT']].to_dict('records'))
    header_values = {k: {str(value): int(n) for (value, n) in fe.loc[fe.archive_year.between(1974, 2012), k].fillna('missing').value_counts().items()} for k in ['BITPIX', 'NAXIS1', 'NAXIS2', 'BUNIT', 'BSCALE', 'BZERO', 'GV', 'ICHK']}
    catalogue_metadata = None
    design_path = root / 'results/T3_MWO_CATALOGUE/DESIGN.csv'
    if design_path.exists():
        design = pd.read_csv(design_path, usecols=['record_set', 'day', 'obs_time'])
        actual_day = pd.to_datetime(design.obs_time, format='mixed').dt.strftime('%Y-%m-%d')
        mismatch = design.day != actual_day
        catalogue_metadata = dict(design_sha256=digest(design_path),
            n_rows_per_set=design.groupby('record_set').size().to_dict(),
            wrong_utc_day_per_set=design[mismatch].groupby('record_set').size().to_dict(),
            sealed_file_read=False)
    if not all(header_hashes.values()) or not all(input_hashes.values()):
        raise ValueError('An input differs from its saved checksum')
    return dict(catalogue_metadata=catalogue_metadata, scope='metadata capacity, with DPD positions and hemispheres; ephemeris and magnetic measurement failures remain to be applied', header_products_verified=header_hashes, dpd_files_verified=input_hashes, group_parsing=dict(parsing), candidate_days=dict(eligible), metadata_selection=summary, instrument_by_epoch_resolution=dict(sorted(instrument_counts.items())), header_values=header_values, ignored_headers=dict(ignored), time_metadata=time_meta, inputs_sha256=dict(header_inventory=digest(headers / 'HEADERS.csv.gz'), dpd_manifest=digest(data / 'SHA256SUMS.txt')))
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    result = audit(args.root)
    text = json.dumps(result, indent=2) + '\n'
    if args.out:
        with args.out.open('x') as f:
            f.write(text)
    else:
        print(text, end='')
