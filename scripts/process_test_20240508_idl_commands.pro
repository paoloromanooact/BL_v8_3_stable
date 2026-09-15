; Start IDL from the repository root before running this batch.
CD, CURRENT=project_root
CD, project_root + '/idl'
.compile *.pro

data_dir = project_root + '/data/20240508_0312'
csv_file = project_root + '/output/sharp_bl_20240508_0312.csv'

process_sharp_day, data_dir, $
  OUTPUT_CSV=csv_file, $
  THRESHOLD=100D, MAX_ABS_BR=10000D, BMAP_MIN=1D, $
  LEADING_SIDE='XMAX', /VERBOSE

plot_sharp_diagnostics_from_csv, csv_file, DATA_DIR=data_dir, $
  OUT_DIR=project_root + '/output/diagnostics_suspicious', $
  /SUSPICIOUS, /VERBOSE
