PRO plot_sharp_diagnostics_from_csv, csv_file, DATA_DIR=data_dir, OUT_DIR=out_dir, $
                                      HARP=harp_select, ANTI_HALE=anti_hale, $
                                      SUSPICIOUS=suspicious, INVALID=invalid, $
                                      TILT_GT=tilt_gt, LIMIT=limit, $
                                      USE_MRDFITS=use_mrdfits, RANGE=range, VERBOSE=verbose
  ;+
  ; NAME:
  ;   plot_sharp_diagnostics_from_csv
  ; PURPOSE:
  ;   Generate diagnostic PNGs after process_sharp_day has completed. This
  ;   routine reads the CSV, selects rows, reopens the corresponding Br files,
  ;   and writes PNG plots. Plot failures do not affect the scientific CSV.
  ; EXAMPLES:
  ;   plot_sharp_diagnostics_from_csv, csv, DATA_DIR=data_dir, /SUSPICIOUS
  ;   plot_sharp_diagnostics_from_csv, csv, DATA_DIR=data_dir, /ANTI_HALE
  ;   plot_sharp_diagnostics_from_csv, csv, DATA_DIR=data_dir, HARP=11152
  ;-
  COMPILE_OPT idl2, strictarr

  IF N_ELEMENTS(csv_file) EQ 0 THEN MESSAGE, 'Provide csv_file.'
  IF N_ELEMENTS(data_dir) EQ 0 THEN data_dir = FILE_DIRNAME(csv_file)
  IF N_ELEMENTS(out_dir) EQ 0 THEN out_dir = FILE_DIRNAME(csv_file) + '/diagnostics'
  IF N_ELEMENTS(limit) EQ 0 THEN limit = 1000000L
  IF N_ELEMENTS(tilt_gt) EQ 0 THEN tilt_gt = !VALUES.D_NAN
  IF ~FILE_TEST(out_dir, /DIRECTORY) THEN FILE_MKDIR, out_dir

  OPENR, lun, csv_file, /GET_LUN
  header = ''
  READF, lun, header
  fields = STRSPLIT(header, ',', /EXTRACT)

  c_filename = sharp_csv_column_index(fields, 'filename')
  c_bitmap_file = sharp_csv_column_index(fields, 'bitmap_file')
  c_threshold = sharp_csv_column_index(fields, 'threshold_g')
  c_max_abs_br = sharp_csv_column_index(fields, 'max_abs_br')
  c_bmap_min = sharp_csv_column_index(fields, 'bmap_min')
  c_harp = sharp_csv_column_index(fields, 'harpnum')
  c_posx = sharp_csv_column_index(fields, 'pos_x')
  c_posy = sharp_csv_column_index(fields, 'pos_y')
  c_negx = sharp_csv_column_index(fields, 'neg_x')
  c_negy = sharp_csv_column_index(fields, 'neg_y')
  c_tilt_raw = sharp_csv_column_index(fields, 'tilt_raw_deg')
  c_tilt_red = sharp_csv_column_index(fields, 'tilt_reduced_deg')
  c_phi = sharp_csv_column_index(fields, 'phi_mx')
  c_sep = sharp_csv_column_index(fields, 'separation_cm')
  c_sbl = sharp_csv_column_index(fields, 's_bl')
  c_hale = sharp_csv_column_index(fields, 'hale_sign')
  c_valid = sharp_csv_column_index(fields, 'valid_bl')
  c_qstr = sharp_csv_column_index(fields, 'quality_string')
  c_susp = sharp_csv_column_index(fields, 'suspicious_flag')
  c_reason = sharp_csv_column_index(fields, 'diagnostic_reason')

  IF c_filename LT 0 THEN MESSAGE, 'CSV missing filename column.'

  nmade = 0L
  line = ''
  WHILE ~EOF(lun) DO BEGIN
    READF, lun, line
    IF STRLEN(STRTRIM(line,2)) EQ 0 THEN CONTINUE
    vals = STRSPLIT(line, ',', /EXTRACT)
    IF N_ELEMENTS(vals) LE c_filename THEN CONTINUE

    select = 0
    IF ~(KEYWORD_SET(anti_hale) OR KEYWORD_SET(suspicious) OR KEYWORD_SET(invalid) OR $
         (N_ELEMENTS(harp_select) GT 0) OR FINITE(tilt_gt)) THEN select = 1

    IF KEYWORD_SET(anti_hale) AND (c_hale GE 0) THEN IF FIX(vals[c_hale]) EQ -1 THEN select = 1
    IF KEYWORD_SET(suspicious) AND (c_susp GE 0) THEN IF FIX(vals[c_susp]) EQ 1 THEN select = 1
    IF KEYWORD_SET(invalid) AND (c_valid GE 0) THEN IF FIX(vals[c_valid]) EQ 0 THEN select = 1
    IF (N_ELEMENTS(harp_select) GT 0) AND (c_harp GE 0) THEN BEGIN
      IF STRTRIM(vals[c_harp],2) EQ STRTRIM(STRING(harp_select),2) THEN select = 1
    ENDIF
    IF FINITE(tilt_gt) AND (c_tilt_red GE 0) THEN BEGIN
      tr = DOUBLE(vals[c_tilt_red])
      IF FINITE(tr) THEN IF ABS(tr) GT tilt_gt THEN select = 1
    ENDIF

    IF select EQ 0 THEN CONTINUE

    br_file = FILEPATH(vals[c_filename], ROOT_DIR=data_dir)
    IF ~FILE_TEST(br_file) THEN BEGIN
      PRINT, 'Missing Br file: ', br_file
      CONTINUE
    ENDIF

    CATCH, err
    IF err NE 0 THEN BEGIN
      CATCH, /CANCEL
      PRINT, 'ERROR plotting: ', br_file
      PRINT, 'IDL error msg: ', !ERROR_STATE.MSG
      CONTINUE
    ENDIF

    IF KEYWORD_SET(verbose) THEN PRINT, 'Plotting: ', br_file
    IF KEYWORD_SET(use_mrdfits) THEN BEGIN
      br_map = MRDFITS(br_file, 1, hdr)
    ENDIF ELSE BEGIN
      read_sdo, br_file, hdr, br_map, /UNCOMP_DELETE
    ENDELSE

    cp = [!VALUES.D_NAN, !VALUES.D_NAN]
    cn = [!VALUES.D_NAN, !VALUES.D_NAN]
    IF (c_posx GE 0) AND (c_posy GE 0) THEN cp = [DOUBLE(vals[c_posx]), DOUBLE(vals[c_posy])]
    IF (c_negx GE 0) AND (c_negy GE 0) THEN cn = [DOUBLE(vals[c_negx]), DOUBLE(vals[c_negy])]

    tilt_raw = !VALUES.D_NAN & tilt_red = !VALUES.D_NAN
    phi = !VALUES.D_NAN & sep = !VALUES.D_NAN & sbl = !VALUES.D_NAN
    hale = 0 & valid = 0
    qstr = '' & reason = ''
    IF c_tilt_raw GE 0 THEN tilt_raw = DOUBLE(vals[c_tilt_raw])
    IF c_tilt_red GE 0 THEN tilt_red = DOUBLE(vals[c_tilt_red])
    IF c_phi GE 0 THEN phi = DOUBLE(vals[c_phi])
    IF c_sep GE 0 THEN sep = DOUBLE(vals[c_sep])
    IF c_sbl GE 0 THEN sbl = DOUBLE(vals[c_sbl])
    IF c_hale GE 0 THEN hale = FIX(vals[c_hale])
    IF c_valid GE 0 THEN valid = FIX(vals[c_valid])
    IF c_qstr GE 0 THEN qstr = vals[c_qstr]
    IF c_reason GE 0 THEN reason = vals[c_reason]

    png_name = vals[c_filename] + '.diagnostic.png'
    png_name = STRJOIN(STRSPLIT(png_name, '/', /EXTRACT), '_')
    outfile = FILEPATH(png_name, ROOT_DIR=out_dir)
    title = vals[c_filename]
    IF c_harp GE 0 THEN title = 'HARP ' + vals[c_harp] + '  ' + vals[c_filename]

    ; Reopen bitmap if available and rebuild the exact analysis mask used by process_sharp_day.
    have_bmap = 0B
    bmap = 0
    analysis_mask = 0
    IF c_bitmap_file GE 0 THEN BEGIN
      bfile = FILEPATH(vals[c_bitmap_file], ROOT_DIR=data_dir)
      IF FILE_TEST(bfile) THEN BEGIN
        IF KEYWORD_SET(use_mrdfits) THEN BEGIN
          bmap = MRDFITS(bfile, 1, bhdr)
        ENDIF ELSE BEGIN
          read_sdo, bfile, bhdr, bmap, /UNCOMP_DELETE
        ENDELSE
        have_bmap = 1B
      ENDIF
    ENDIF

    th = 100D & mab = 10000D & bmmin = 1D
    IF c_threshold GE 0 THEN th = DOUBLE(vals[c_threshold])
    IF c_max_abs_br GE 0 THEN mab = DOUBLE(vals[c_max_abs_br])
    IF c_bmap_min GE 0 THEN bmmin = DOUBLE(vals[c_bmap_min])

    IF have_bmap THEN BEGIN
      analysis_mask = sharp_build_mask_1ar(br_map, bmap, THRESHOLD=th, MAX_ABS_BR=mab, BMAP_MIN=bmmin)
    ENDIF ELSE BEGIN
      analysis_mask = sharp_build_mask_1ar(br_map, THRESHOLD=th, MAX_ABS_BR=mab)
    ENDELSE

    IF N_ELEMENTS(range) GT 0 THEN BEGIN
      IF have_bmap THEN BEGIN
        sharp_make_bl_diagnostic_png, br_map, cp, cn, BMAP=bmap, ANALYSIS_MASK=analysis_mask, $
                                      OUTFILE=outfile, TITLE=title, RANGE=range, $
                                      TILT_DEG=tilt_raw, TILT_REDUCED_DEG=tilt_red, $
                                      PHI=phi, SEPARATION=sep, S_BL=sbl, HALE_SIGN=hale, $
                                      VALID_BL=valid, QUALITY_STRING=qstr, REASON=reason
      ENDIF ELSE BEGIN
        sharp_make_bl_diagnostic_png, br_map, cp, cn, ANALYSIS_MASK=analysis_mask, $
                                      OUTFILE=outfile, TITLE=title, RANGE=range, $
                                      TILT_DEG=tilt_raw, TILT_REDUCED_DEG=tilt_red, $
                                      PHI=phi, SEPARATION=sep, S_BL=sbl, HALE_SIGN=hale, $
                                      VALID_BL=valid, QUALITY_STRING=qstr, REASON=reason
      ENDELSE
    ENDIF ELSE BEGIN
      IF have_bmap THEN BEGIN
        sharp_make_bl_diagnostic_png, br_map, cp, cn, BMAP=bmap, ANALYSIS_MASK=analysis_mask, $
                                      OUTFILE=outfile, TITLE=title, $
                                      TILT_DEG=tilt_raw, TILT_REDUCED_DEG=tilt_red, $
                                      PHI=phi, SEPARATION=sep, S_BL=sbl, HALE_SIGN=hale, $
                                      VALID_BL=valid, QUALITY_STRING=qstr, REASON=reason
      ENDIF ELSE BEGIN
        sharp_make_bl_diagnostic_png, br_map, cp, cn, ANALYSIS_MASK=analysis_mask, $
                                      OUTFILE=outfile, TITLE=title, $
                                      TILT_DEG=tilt_raw, TILT_REDUCED_DEG=tilt_red, $
                                      PHI=phi, SEPARATION=sep, S_BL=sbl, HALE_SIGN=hale, $
                                      VALID_BL=valid, QUALITY_STRING=qstr, REASON=reason
      ENDELSE
    ENDELSE

    nmade = nmade + 1L
    CATCH, /CANCEL
    IF nmade GE limit THEN BREAK
  ENDWHILE
  FREE_LUN, lun
  PRINT, 'Diagnostic PNGs written: ', nmade
  PRINT, 'Output directory: ', out_dir
END
