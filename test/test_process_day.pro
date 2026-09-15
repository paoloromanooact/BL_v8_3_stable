PRO test_process_day, PROJECT_ROOT=project_root, DATA_SUBDIR=data_subdir, $
                     OUTPUT_NAME=output_name, THRESHOLD=threshold, $
                     MAX_ABS_BR=max_abs_br, BMAP_MIN=bmap_min, LEADING_SIDE=leading_side

  COMPILE_OPT idl2, strictarr

  IF N_ELEMENTS(project_root) EQ 0 THEN MESSAGE, 'Set PROJECT_ROOT to the repository root directory.'
  IF N_ELEMENTS(data_subdir) EQ 0 THEN data_subdir = 'data/20240508_0312'
  IF N_ELEMENTS(output_name) EQ 0 THEN output_name = 'sharp_bl_test.csv'
  IF N_ELEMENTS(threshold) EQ 0 THEN threshold = 100D
  IF N_ELEMENTS(max_abs_br) EQ 0 THEN max_abs_br = 10000D
  IF N_ELEMENTS(bmap_min) EQ 0 THEN bmap_min = 1D
  IF N_ELEMENTS(leading_side) EQ 0 THEN leading_side = 'XMAX'

  data_dir = project_root + '/' + data_subdir
  output_csv = project_root + '/output/' + output_name

  process_sharp_day, data_dir, OUTPUT_CSV=output_csv, THRESHOLD=threshold, $
                     MAX_ABS_BR=max_abs_br, BMAP_MIN=bmap_min, $
                     LEADING_SIDE=leading_side, /VERBOSE
END
