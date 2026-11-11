"""Prepare reproducibility policy tables from tracked CSVs; never run scientific code.

Draft policies, not a comparison or a reproduction result. Run with --root and
--out-dir to prepare the review outside the repository. No scientific module is imported.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

import pandas as pd

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
RTOL, NORMALIZED_ATOL = 1e-9, 1e-12
ETA = 3.56e-25  # fixed planning scale, P2f protocol section 2; never estimated here
GAMMA = 24.0   # same planning scale, degrees; not the true value of every generator
ID = ['kind','test','cand','scenario','effect','beta_frac','k','seed','sc','rho',
      'group','gruppo','variant','sample','set','comparison','activity','act',
      'quantity','estimator','check','convention','statistic','HARPNUM','T_REC',
      'role','CR','hemisphere','cyc','cycle','year','item','lag']
PROV = re.compile(r'^(git_commit|git_dirty|sha256_.*|.*_sha256.*|validation_git_commit)$')

# Explicit keys reviewed on the table schemas, including the 23 initially
# unresolved tables and the five exposed by the narrower identifier vocabulary.
MANUAL = {'results/DIAGNOSTIC/AUDIT_C1_Z_CORR.csv': ['test', 'scenario_1', 'scenario_2'],
 'results/DIAGNOSTIC/C_RAW_RUN1.csv.gz': ['scenario', 'k', 'test', 'arm'],
 'results/DIAGNOSTIC/C_SUMMARY_RUN1.csv': ['arm', 'scenario', 'test'],
 'results/DIAGNOSTIC/DIAG_P2E_PHI_TERCILES.csv': ['scenario', 'test', 'phi_tercile'],
 'results/DOMINANT_TRIAL_2HARP/DOMINANT_HARP_FITS_SHA256.csv': ['file'],
 'results/EXPLORATORY/FACTORIAL_BY_RECORD.csv.gz': ['HARPNUM', 'T_REC', 'M', 'G', 'C'],
 'results/EXPLORATORY/FACTORIAL_EFFECTS_BY_RECORD_SUMMARY.csv': ['quantity', 'kind', 'term'],
 'results/EXPLORATORY/FACTORIAL_G_EFFECT_BY_INTENSITY.csv': ['decile_abs_sbl'],
 'results/EXPLORATORY/FACTORIAL_REPRODUCTION.csv': ['column', 'kind', 'combination'],
 'results/EXPLORATORY/FACTORIAL_SBL_SUMS.csv': ['sample', 'term', 'M', 'G', 'C'],
 'results/EXPLORATORY/FACTORIAL_TILT_SIMPLE_EFFECTS.csv': ['factor', 'fixed'],
 'results/EXPLORATORY/FACTORIAL_VALIDITY.csv': ['item'],
 'results/EXPLORATORY/HALE_TRANSITIONS.csv': ['item'],
 'results/EXPLORATORY/P3_C1_C2_COMMON_SUBSET.csv': ['comparison'],
 'results/EXPLORATORY/PRIMARY_VS_CONTROL.csv': ['item'],
 'results/P1/CYCLE_BOUNDARY_FITS.csv': ['window', 'start'],
 'results/P2/P2B_CALIBRATION.csv': ['rho', 'test', 'scheme'],
 'results/P2/P2B_CALIBRATION_RUN2_N100.csv': ['rho', 'test', 'scheme'],
 'results/P2/P2B_MOVING_BLOCKS.csv': ['test', 'group', 'block_length'],
 'results/P2/P2B_RESIDUAL_ACF.csv': ['test', 'lag'],
 'results/P2/P2E_DEVELOPMENT_ESTIMATORS.csv': ['sc', 'k', 'test', 'est'],
 'results/P2/P2E_VALIDATION_RAW.csv.gz': ['scenario', 'k', 'beta_frac', 'test'],
 'results/P2/P2_T0_POWER.csv': ['test', 'beta_over_gamma0'],
 'results/P3/P3_BARD_CRITERIA.csv': ['criterion'],
 'results/P3/P3_BARD_MATCHES.csv': ['set', 'comparison', 'row'],
 'results/P3/P3_BARD_SELECTION.csv': ['set', 'step'],
 'results/P3/P3_BARD_SUMMARY.csv': ['set', 'comparison'],
 'results/P3/P3_RANDOM_CONTROL.csv': ['set', 'rep']}

EXACT = set('''HARPNUM CR cyc cycle cycle_common cycle_new cycle_old NOAA_NUM NOAA_AR
QUALITY QUALITY_cat qual_0x80 key_CAR_ROT family_id family_rank p1d_family_rank
recurrence_of rank row seed seed_synthetic test variant sample group scenario k
in_S valid_bl valid_legacy valid_v84 valid_changed complete_series validation_passed
accepted accepted_rule app applicable mandatory passed ok robust finite
inputs_finite units_finite units_aligned generator_ok sims_finite resim_finite
mc_finite mc_false exact_false false_analytic false_exact_gen false_exact_obs
hale_sign leading_sign expected_leading_sign hale_legacy hale_v83 hale_v84
hale_changed hale_same hale_ours_rec hale_bard_rec b_leading_geom s_bl_same_sign
concordant predicted_sign point_estimate_ok ci95_within scenario_ok kept_M kept_B
phi_at_boundary kappa_at_boundary sigma_u_at_boundary sigma_x_at_lower
phi_not_estimable kappa_not_estimable too_few_cr
n nmask npos nneg count counts catalogues catalogues_with_wrap regions_T3
regions_wrapped tests scenarios false false_total false_supported false_opposite
false_predicted_dir false_opposite_dir false_predicted_direction false_opposite_direction
false_p2e false_oracle false_gen false_obs false_mc errors error not_decided_count
fp_count decisions_changed verdicts_changed c0_le_0_total na_with_c0_gt_0
na_with_c0_le_0 mc_discordant resim_verdict
Year Month Day Hour Minute Second DayAfterChrist ReferenceDay
M M1_border_pixels M3_big_neg M3_big_pos M3_components_neg M3_components_pos
P2_n_comparable P1_repro_cycle
HH_23n HH_23s HH_24n HH_24s AH_23n AH_23s AH_24n AH_24s
Cycle23n Cycle23s Cycle24n Cycle24s Hale AntiHale LeadingPolarity
'''.split())
EXACT.update('mean_small sigma_u_at_boundary false_obs_applicable group_n grid_len first_seen_on_disk reale controllo noaa_num NOAA_ARS BMRLabel PlotSize activity effect beta_frac beta_over_gamma0 seed_synthetic'.split())
EXACT_PREFIXES = ('verdict','n_','paired_')
EXACT_SUFFIXES = ('_flag','_possible','_evaluable','_same_sign')
COUNT_STATS = ('_mean','_median','_q10','_q90','_p10','_p90','_std')
TEST_VALUE = set('beta beta_obs beta_obs_A beta_gen beta_lin beta_true beta_diff mu_true null_mean null_sd estimate bias sd m_model'.split())
TEST_VALUE.update(['ci95_lo','ci95_hi','ci975_lo','ci975_hi','lo','hi'])
TEST_VARIANCE = set('v_true v_model v_ind_true v_tmp_true v_ind_model v_tmp_model sum_a2_ee2 sigma_u2 sigma_u2_hat sigma_u2_true sigma_u2_used sigma_x2 c0 c1 sw2_N sw2_S'.split())
DIMENSIONLESS = set('''acf band coslat sintilt p_new phase_max b_hat b_true var_b
var_z var_z_gen var_z_obs mean_z se_var_z z z_gen z_obs z_vs_nominal stat
ks_p p_low p_high p_pred p_oracle A_p_oracle A_p_pred fraction
false_positive false_positive_p2 false_positive_p2b coverage95 coverage975 power
detection_fraction false_positive_fraction flux_ratio flux_ratio_med median_flux_ratio
median_separation_ratio ratio s_bl_ratio dlog10_phi dsep_rel max_rel rel_S rel_own
repro_s_bl_rel_diff C1_repro_rel_dd_vs_measure R1_lon
sigma_u2_hat_over_true imbalance_ours bard_imbalance imbal_ours_med imbal_bard_med
diff_median spearman_R_phi_hat corr_phi_hat_T3_T5 corr_z loglik neg_reml
var_a a_hat a_true top_fraction nbar phi_med
'''.split())


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


def read(root, f):
    return pd.read_csv(root / f, low_memory=False, keep_default_na=False,
                       na_values=['', 'nan', 'NaN'])


def base_stat(col):
    for suffix in ('_mean','_median','_std','_q10','_q90','_p10','_p90'):
        if col.endswith(suffix):
            return col[:-len(suffix)]
    return col


def policy(col, context, numeric, key):
    """Semantic rules; never derive a tolerance or a type from observed magnitudes."""
    if PROV.fullmatch(col):
        return 'provenance', '', None, 'verificare separatamente, senza ignorare gli hash degli input'
    if col in key:
        return 'exact_key', '', None, 'identificativo della riga; mancanti espliciti se previsti'
    if col == 'sha256':
        return 'exact', '', None, 'impronta del file controllato'
    if col == 'status':
        return 'exact', '', None, 'stato scientifico dichiarato: non metadato Git intercambiabile'
    if not numeric:
        return 'exact', '', None, 'testo, data scientifica o valore eterogeneo; nessuna esclusione implicita'
    # A mean/quantile of counts is continuous; raw counts remain exact even if
    # stored as float because other rows are missing.
    is_count_summary = col.startswith('n_') and col.endswith(COUNT_STATS)
    if not is_count_summary and (col in EXACT or col.startswith(EXACT_PREFIXES)
                                or col.endswith(EXACT_SUFFIXES) or col.endswith(('_n_degenerate','_predicted_dir','_opposite_dir','_predicted_direction','_opposite_direction'))
                                or (col.startswith('leg_') and col[4:] in EXACT)
                                or 'leading_' in col or col.endswith('_hale_sign') or col == 'hale_sign_cat'):
        return 'exact', '', None, 'conteggio, flag o decisione definito semanticamente'
    test, quantity = context.get('test'), context.get('quantity')
    tscale = (ETA if test == 'T5' and quantity != 'S*'
              else 1.0 if test == 'T4' or quantity == 'S*' else GAMMA)
    tunit = ('G/Mx' if test == 'T5' and quantity != 'S*'
             else 'cm' if quantity == 'S*' else 'deg')
    base = base_stat(col)
    if col.startswith('gamma0'):
        return 'scaled', 'deg', GAMMA, 'coefficiente Joy: stessa scala fissa di pianificazione 24 gradi'
    if col == 'se_var_z':
        return 'scaled', '1', 1.0, 'errore standard della varianza di z sotto la normale, non di una frequenza'
    if col == 'se' or col.startswith('se_') or col in ('mc_se','C1_se'):
        return 'scaled', '1', 1.0, 'errore Monte Carlo di una frequenza nei file attuali; non SE della pendenza'
    if col == 'sig':
        return 'exact', '', None, 'materiale storico: sig non ha un produttore recuperato, confronto esatto'
    if col in ('phi','phi_mean','phi_median','phi_q10','phi_q90') and context.get('_file','').startswith(('results/DIAGNOSTIC/','results/P2F_PILOT/','results/P2/')):
        return 'scaled', '1', 1.0, 'persistenza AR, distinta dal flusso magnetico'
    if col.startswith('eta_bar'):
        return 'scaled', 'G/Mx', ETA, 'scala fissa eta_bar del protocollo P2f, non stimata dalla tabella'
    if base in TEST_VARIANCE:
        if test in ('T3','T5'):
            return 'scaled', f'({tunit})^2', tscale**2, 'varianza nella scala della risposta del test'
        return 'exact', '', None, 'varianza senza test identificato: confronto conservativo esatto'
    if col in TEST_VALUE:
        if test in ('T0','T1','T2','T3','T4','T5'):
            return 'scaled', tunit, tscale, 'scala della pendenza/risposta; S* distinto da D*'
        return 'exact', '', None, 'valore eterogeneo o senza test: confronto conservativo esatto'
    if col == 'phi' or base.startswith('phi_') or col in ('phi_mx','phi_pos_mx','phi_neg_mx'):
        # phi means flux in the P1 catalogues, but AR persistence in diagnostics.
        if col == 'phi' or base in ('phi_hat','phi_true','phi_raw','phi_used','phi_mean','phi_median','phi_q10','phi_q90'):
            return 'scaled', '1', 1.0, 'persistenza AR adimensionale'
    if col == 'P1_repro_s_bl':
        return 'scaled', 'Mx cm', 1.0, 'valore P1 ricalcolato, non scarto relativo'
    if ('s_bl' in col or col in ('abs_sbl','group_sum_abs','group_sum_net','sum_net','sum_abs_cells',
                               'net_without_top','top_net','sum_pos','sum_neg','sum_abs','effect_on_total',
                               'median_abs_effect_cells')) and not any(x in col for x in ('ratio','rel_','share','same','repro','over_')):
        return 'scaled', 'Mx cm', 1.0, 'unita fisica S_BL; nessuna scala ricavata dai valori osservati'
    if col in ('USFLUX','key_USFLUX','PFlux','NFlux','BMRFlux','bard_flux','max_usflux','phi_mx','phi_pos_mx','phi_neg_mx',
               'M2_flux_in','M2_flux_out','P1_phi','bmap1_phi','thr300_phi','phi_P1_cat','sum_phi','phi_med','phi_median') or col.startswith('leg_phi_') or col.startswith('sum_phi_mx'):
        return 'scaled', 'Mx', 1.0, 'unita di flusso; i grandi float non sono conteggi'
    if col in ('d_cm','leg_d_cm','d_P1_cat','P1_d','bmap1_d','thr300_d','C1_d_uniform'):
        return 'scaled', 'cm', 1.0, 'distanza fisica'
    if col in ('d_axial_g','d_axial_bal_g','cum_d_bal_g','d_star','sum_abs_d_bal') or col.startswith(('sum_d_g','sum_d_bal')):
        return 'scaled', 'G', 1.0, 'proxy del dipolo prima del trasporto'
    if col.startswith(('gamma0','lat_','lon_','key_LAT_','key_LON_')) or col in ('gamma','lat_legacy','lat_v84','LAT_FWT','LON_FWT','Tilt_rel','Tilt_abs','delta','delta_med','dtilt','tilt_P1_cat','P1_tilt','bmap1_tilt','thr300_tilt','C1_tilt_uniform','b_gamma','b_asin','mu_old','mu_new','sd_old','sd_new','lat_p50','dlat','dlon','abs_lat_med','sep_deg_med','bard_sep_med','key_CRLN_OBS','abs_lon_primary','abs_lon_control','max_abs_y_minus_gamma','C1_repro_abs_dtilt_vs_measure') or col.startswith(('tilt_','leg_tilt_')) or col.endswith(('_deg','_dtilt','_deg_ci95_lo','_deg_ci95_hi')):
        return 'scaled', 'deg', 1.0, 'angolo espresso in gradi'
    if col in ('dt_days','abs_dt_days','dt_h','dt_h_med'):
        return 'scaled', 'day' if 'days' in col else 'h', 1.0, 'intervallo temporale, distinto da una data identificativa'
    if is_count_summary:
        return 'scaled', '1', 1.0, 'statistica continua di conteggi; non un conteggio grezzo'
    if base in DIMENSIONLESS or base.startswith(('kappa','phi_hat','phi_true','phi_raw','var_b','var_a')) or col.startswith(('frac_','fraction','coverage','power','R_','ratio','share_','rel_','corr_','spearman_','rho_','p_pred','p_oracle','C1_false_among_applicable')) or col.endswith(('_frac','_mc_se','_in_se','_rel','_ratio','_over_sd','_over_net','_over_median_abs_A','_in_global_medians','_relative_to_own')) or col in ('f','leg_sintilt','P1_imbalance','w_old','w_new','max_abs_z_gen_minus_obs','discordant_max_abs_z_margin') or (col.startswith('false_') and any(x in col for x in ('frac','among','upper95','positive'))):
        return 'scaled', '1', 1.0, 'quantita adimensionale'
    return 'exact', '', None, 'regola conservativa: semantica non classificata; nessuna tolleranza automatica'


def selftest():
    def p(col, test=None, quantity=None, numeric=True, key=()):
        return policy(col, dict(test=test, quantity=quantity), numeric, key)
    assert p('gamma0', 'T0')[2] == GAMMA
    assert p('gamma0_c24', 'T3')[2] == GAMMA
    assert p('gamma0_c25', 'T3')[2] == GAMMA
    assert p('status', numeric=False)[0] == 'exact'
    assert 'varianza di z' in p('se_var_z')[3]
    assert p('se_var_z')[2] == 1.0
    assert p('estimate', 'T5')[2] == ETA
    assert p('v_true', 'T5')[2] == ETA**2
    assert p('sigma_x2_mean', 'T5')[2] == ETA**2
    assert p('v_true', 'T3')[2] == GAMMA**2
    assert p('estimate', 'T5', 'S*')[1:3] == ('cm', 1.0)
    assert p('estimate', 'T4')[2] == 1.0
    assert p('phi_mx')[0:3] == ('scaled', 'Mx', 1.0)
    assert p('P1_repro_s_bl')[1] == 'Mx cm'
    assert p('n_cells')[0] == 'exact'
    assert p('n_varfun_mean')[0] == 'scaled'
    assert p('passed')[0] == 'exact'
    assert p('accepted')[0] == 'exact'
    assert p('verdict', numeric=False)[0] == 'exact'
    assert p('value')[0] == 'exact'
    assert p('sha256', numeric=False)[0] == 'exact'
    assert p('sha256_P2')[0] == 'provenance'
    assert p('effect', key=('effect',))[0] == 'exact_key'
    assert p('sig','T5')[0] == 'exact'
    assert p('se','T5')[2] == 1.0
    def near(a, b, S):
        return abs(a-b) <= NORMALIZED_ATOL*S + RTOL*max(abs(a), abs(b))
    assert not near(1e-25,9e-25,ETA)
    assert not near(0.0,1e-30,ETA)
    assert near(1e-25,1e-25*(1+1e-10),ETA)
    assert not near(1e-50,9e-50,ETA**2)
    print('29 semantic/numeric policy checks passed; no scientific data or simulation used')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    ap.add_argument('--out-dir', type=Path)
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    root = args.root.resolve()
    out = args.out_dir or root / 'docs'
    out.mkdir(parents=True, exist_ok=True)
    snapshot = git(root, 'rev-parse', 'HEAD')
    files = git(root, 'ls-files', 'results/*.csv', 'results/*.csv.gz', 'figures/*.csv').splitlines()
    keys, scales, refs = [], [], []
    for f in files:
        d = read(root, f)
        if f in MANUAL:
            key = MANUAL[f]
            if any(c not in d for c in key) or d.duplicated(key).any():
                raise ValueError(f'chiave naturale non valida: {f}: {key}')
            method = 'naturale esplicita'
        elif len(d) == 0:
            key, method = [], 'tabella vuota: identita di schema e zero righe'
        else:
            ids = [c for c in ID if c in d]
            key = next((ids[:i] for i in range(1,len(ids)+1) if not d.duplicated(ids[:i]).any()), None)
            if key is None:
                raise ValueError(f'manca chiave per {f}')
            method = 'identificativi di schema, unicita verificata'
        prov = [c for c in d if PROV.fullmatch(c)]
        keys.append(dict(file=f,rows=len(d),key=';'.join(key),key_status=method,
                         provenance_cols=';'.join(prov)))
        group_cols = [c for c in ('test','quantity') if c in d]
        groups = d.groupby(group_cols,dropna=False,sort=True) if group_cols and len(d) else [((),d)]
        for group, frame in groups:
            vals = group if isinstance(group,tuple) else (group,)
            context = {c:None if pd.isna(v) else str(v) for c,v in zip(group_cols, vals)}
            selector = json.dumps(context,ensure_ascii=False,sort_keys=True)
            for col in d:
                mode,unit,S,reason = policy(col,dict(context, _file=f),pd.api.types.is_numeric_dtype(d[col]),key)
                scales.append(dict(file=f,column=col,selector=selector,mode=mode,unit=unit,
                                   scale_S=S,normalized_atol=NORMALIZED_ATOL if mode=='scaled' else None,
                                   rtol=RTOL if mode=='scaled' else None,reason=reason))
        ref = git(root,'log','-1','--format=%H','--',f)
        blob = git(root,'rev-parse',f'{ref}:{f}')
        if git(root,'hash-object',f) != blob:
            raise ValueError(f'riferimento tracciato modificato nella copia di lavoro: {f}')
        recorded = sorted(set(d.git_commit.dropna().astype(str))) if 'git_commit' in d else []
        dirty = sorted(set(d.git_dirty.dropna().astype(str))) if 'git_dirty' in d else []
        note = ('commit registrato nel file: verificare che sia quello del produttore, non ereditato dagli input'
                if recorded else 'nessun commit del codice nel file: produttore da ricostruire; non inventare provenienza')
        effective, evidence = '', ''
        if 'P2B_CALIBRATION_RUN1_N40' in f:
            effective = git(root,'rev-parse','2134f86')
            evidence = 'results/P2/P2B_CALIBRATION_RUN1_N40.json: codice equivalente dichiarato; colonna git_commit = HEAD finale'
        elif 'P2B_CALIBRATION_RUN2_N100' in f:
            effective = git(root,'rev-parse','637c482')
            evidence = 'results/P2/P2B_CALIBRATION_RUN2_N100.json: codice equivalente dichiarato; colonna git_commit = HEAD finale'
        if any(x not in ('0','0.0') for x in dirty):
            note += '; albero originale non pulito: il solo commit non ricostruisce le modifiche locali'
        refs.append(dict(file=f,inventory_commit=snapshot,reference_commit=ref,reference_blob=blob,
                         recorded_code_commits=';'.join(recorded),recorded_git_dirty=';'.join(dirty),
                         effective_code_commit_declared=effective,evidence=evidence,note=note))
    for name,rows in [('REPRO_COMPARISON_KEYS_DRAFT.csv',keys),('REPRO_COMPARISON_SCALES_DRAFT.csv',scales),('REPRO_GIT_REFERENCES_DRAFT.csv',refs)]:
        pd.DataFrame(rows).to_csv(out/name,index=False)
    print(json.dumps(dict(files=len(keys),policies=len(scales),keys=dict(pd.Series([r['key_status'] for r in keys]).value_counts()),
                          modes=dict(pd.Series([r['mode'] for r in scales]).value_counts())),default=int,ensure_ascii=False))


if __name__ == '__main__':
    main()
