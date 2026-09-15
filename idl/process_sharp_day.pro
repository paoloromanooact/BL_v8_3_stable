PRO process_sharp_day, input_dir, OUTPUT_CSV=output_csv, THRESHOLD=threshold, $
                       MAX_ABS_BR=max_abs_br, BMAP_MIN=bmap_min, $
                       LEADING_SIDE=leading_side, PATTERN=pattern, $
                       BITMAP_DIR=bitmap_dir, NO_BITMAP=no_bitmap, $
                       USE_MRDFITS=use_mrdfits, VERBOSE=verbose, $
                       TILT_WARN_DEG=tilt_warn_deg
  ;+
  ; NAME:
  ;   process_sharp_day
  ;
  ; PURPOSE:
  ;   Process all SHARP CEA Br FITS files in one directory and write a CSV
  ;   containing one BL-source measurement per file.
  ;
  ; V8 CHANGES:
  ;   - process_sharp_day performs only scientific processing and CSV output
  ;   - graphical diagnostics are separated into plot_sharp_diagnostics_from_csv
  ;   - builds the analysis mask once per file with sharp_build_mask_1ar
  ;-
  COMPILE_OPT idl2, strictarr

  IF N_ELEMENTS(input_dir) EQ 0 THEN MESSAGE, 'Provide input_dir.'
  IF N_ELEMENTS(threshold) EQ 0 THEN threshold = 1000D
  IF N_ELEMENTS(max_abs_br) EQ 0 THEN max_abs_br = 10000D
  IF N_ELEMENTS(bmap_min) EQ 0 THEN bmap_min = 1D
  IF N_ELEMENTS(pattern) EQ 0 THEN pattern = '*.Br.fits*'
  IF N_ELEMENTS(output_csv) EQ 0 THEN output_csv = 'sharp_bl_day.csv'
  IF N_ELEMENTS(tilt_warn_deg) EQ 0 THEN tilt_warn_deg = 60D

  search_pattern = FILEPATH(pattern, ROOT_DIR=input_dir)
  files = FILE_SEARCH(search_pattern, COUNT=nfiles)

  IF nfiles EQ 0 THEN BEGIN
    PRINT, 'No files found: ', search_pattern
    RETURN
  ENDIF

  OPENW, lun, output_csv, /GET_LUN

  header_line = 'filename,bitmap_file,used_bitmap,harpnum,t_rec,date_string,nx,ny,threshold_g,max_abs_br,bmap_min,' + $
                'nmask,nvalid,npos,nneg,phi_mx,separation_cm,lat_mean_deg,coslat,tilt_raw_deg,tilt_reduced_deg,sintilt,' + $
                'pos_x,pos_y,neg_x,neg_y,cycle,expected_leading_sign,leading_sign,hale_sign,s_bl,' + $
                'valid_bl,quality_flag,quality_string,suspicious_flag,diagnostic_reason'
  PRINTF, lun, header_line

  FOR i = 0L, nfiles-1L DO BEGIN

    file = files[i]

    CATCH, err
    IF err NE 0 THEN BEGIN
      CATCH, /CANCEL
      PRINT, 'ERROR processing file: ', file
      PRINT, 'IDL error code: ', err
      PRINT, 'IDL error msg : ', !ERROR_STATE.MSG
      PRINT, 'Continuing with next file.'
      CONTINUE
    ENDIF

    IF KEYWORD_SET(verbose) THEN PRINT, 'Processing ', i+1, '/', nfiles, ': ', file

    IF KEYWORD_SET(use_mrdfits) THEN BEGIN
      br_map = MRDFITS(file, 1, hdr)
    ENDIF ELSE BEGIN
      read_sdo, file, hdr, br_map, /UNCOMP_DELETE
    ENDELSE

    sz = SIZE(br_map, /DIMENSIONS)
    nx = sz[0]
    ny = sz[1]

    used_bitmap = 0
    bitmap_file = ''
    IF ~KEYWORD_SET(no_bitmap) THEN BEGIN
      bitmap_file = sharp_find_bitmap_file(file, BITMAP_DIR=bitmap_dir)
      IF bitmap_file NE '' THEN BEGIN
        IF KEYWORD_SET(verbose) THEN PRINT, '  bitmap: ', bitmap_file
        IF KEYWORD_SET(use_mrdfits) THEN BEGIN
          bmap = MRDFITS(bitmap_file, 1, bhdr)
        ENDIF ELSE BEGIN
          read_sdo, bitmap_file, bhdr, bmap, /UNCOMP_DELETE
        ENDELSE
        IF TOTAL(ABS(SIZE(bmap, /DIMENSIONS)-sz)) EQ 0 THEN BEGIN
          used_bitmap = 1
        ENDIF ELSE BEGIN
          PRINT, '  WARNING: bitmap dimension mismatch, ignoring bitmap.'
          used_bitmap = 0
        ENDELSE
      ENDIF ELSE BEGIN
        IF KEYWORD_SET(verbose) THEN PRINT, '  bitmap: not found, using Br validity mask only.'
      ENDELSE
    ENDIF

    lat_map_deg = sharp_cea_latitude_map_from_header(hdr, NX=nx, NY=ny)
    pixel_area_cm2 = sharp_cea_pixel_area_from_header(hdr, PIXSCALE_CM=pixscale_cm)

    IF used_bitmap THEN BEGIN
      analysis_mask = sharp_build_mask_1ar(br_map, bmap, THRESHOLD=0D, $
                                           MAX_ABS_BR=max_abs_br, BMAP_MIN=bmap_min, $
                                           NVALID=nmask)
    ENDIF ELSE BEGIN
      analysis_mask = sharp_build_mask_1ar(br_map, THRESHOLD=0D, $
                                           MAX_ABS_BR=max_abs_br, NVALID=nmask)
    ENDELSE

    phi = sharp_flux_1ar(br_map, pixel_area_cm2, MASK=analysis_mask, $
                         THRESHOLD=threshold, MAX_ABS_BR=max_abs_br, NPIX=npix_flux)

    d = sharp_polarity_separation_1ar(br_map, MASK=analysis_mask, THRESHOLD=threshold, $
                                      MAX_ABS_BR=max_abs_br, PIXSCALE_CM=pixscale_cm, $
                                      POS_CENTROID=cp, NEG_CENTROID=cn, $
                                      NPOS=npos, NNEG=nneg, NVALID=nvalid)

    coslat = sharp_coslat_from_map_1ar(lat_map_deg, MASK=analysis_mask, BR_MAP=br_map, $
                                       THRESHOLD=threshold, MAX_ABS_BR=max_abs_br, $
                                       LAT_MEAN=lat_mean)

    date_string = sharp_file_date_string(file, HDR=hdr)

    IF FINITE(d) AND FINITE(lat_mean) THEN BEGIN
      sharp_auto_leading_hale, cp, cn, lat_mean, date_string, $
                               LEADING_SIGN=leading_sign, HALE_SIGN=hale_sign, $
                               EXPECTED_LEADING_SIGN=expected_leading_sign, $
                               CYCLE=cycle, LEADING_SIDE=leading_side
      sintilt = sharp_sintilt_1ar(cp, cn, LEADING_SIGN=leading_sign, TILT_DEG=tilt_deg)
      tilt_reduced_deg = sharp_reduce_tilt_deg(tilt_deg)
      s_bl = sharp_bl_source_core_1ar(phi, d, coslat, sintilt, HALE_SIGN=hale_sign)
    ENDIF ELSE BEGIN
      cycle = sharp_cycle_from_date(date_string)
      expected_leading_sign = 0
      leading_sign = 0
      hale_sign = 0
      tilt_deg = !VALUES.D_NAN
      tilt_reduced_deg = !VALUES.D_NAN
      sintilt = !VALUES.D_NAN
      s_bl = !VALUES.D_NAN
      cp = [!VALUES.D_NAN, !VALUES.D_NAN]
      cn = [!VALUES.D_NAN, !VALUES.D_NAN]
    ENDELSE

    quality_flag = sharp_bl_quality_flag(phi, d, lat_mean, coslat, sintilt, s_bl, $
                                         npos, nneg, nmask, VALID_BL=valid_bl, $
                                         FLAG_STRING=quality_string)

    suspicious_flag = 0
    diagnostic_reason = 'NONE'
    IF valid_bl EQ 0 THEN BEGIN
      suspicious_flag = 1
      diagnostic_reason = quality_string
    ENDIF ELSE BEGIN
      IF hale_sign EQ -1 THEN BEGIN
        suspicious_flag = 1
        diagnostic_reason = 'ANTI_HALE'
      ENDIF
      IF ABS(tilt_reduced_deg) GT tilt_warn_deg THEN BEGIN
        suspicious_flag = 1
        IF diagnostic_reason EQ 'NONE' THEN diagnostic_reason = 'LARGE_TILT' ELSE $
          diagnostic_reason = diagnostic_reason + '+LARGE_TILT'
      ENDIF
    ENDELSE

    ; V8: diagnostics are generated after processing, from the CSV.

    harpnum = sharp_string_from_header(hdr, 'HARPNUM', DEFAULT='')
    t_rec = sharp_string_from_header(hdr, 'T_REC', DEFAULT='')

    line = FILE_BASENAME(file) + ',' + FILE_BASENAME(bitmap_file) + ',' + STRTRIM(STRING(used_bitmap), 2) + ',' + $
           harpnum + ',' + t_rec + ',' + date_string + ',' + $
           STRTRIM(STRING(nx), 2) + ',' + STRTRIM(STRING(ny), 2) + ',' + $
           sharp_num_to_string(threshold) + ',' + sharp_num_to_string(max_abs_br) + ',' + sharp_num_to_string(bmap_min) + ',' + $
           STRTRIM(STRING(nmask), 2) + ',' + STRTRIM(STRING(nvalid), 2) + ',' + $
           STRTRIM(STRING(npos), 2) + ',' + STRTRIM(STRING(nneg), 2) + ',' + $
           sharp_num_to_string(phi) + ',' + sharp_num_to_string(d) + ',' + $
           sharp_num_to_string(lat_mean) + ',' + sharp_num_to_string(coslat) + ',' + $
           sharp_num_to_string(tilt_deg) + ',' + sharp_num_to_string(tilt_reduced_deg) + ',' + $
           sharp_num_to_string(sintilt) + ',' + $
           sharp_num_to_string(cp[0]) + ',' + sharp_num_to_string(cp[1]) + ',' + $
           sharp_num_to_string(cn[0]) + ',' + sharp_num_to_string(cn[1]) + ',' + $
           STRTRIM(STRING(cycle), 2) + ',' + STRTRIM(STRING(expected_leading_sign), 2) + ',' + $
           STRTRIM(STRING(leading_sign), 2) + ',' + STRTRIM(STRING(hale_sign), 2) + ',' + $
           sharp_num_to_string(s_bl) + ',' + STRTRIM(STRING(valid_bl), 2) + ',' + $
           STRTRIM(STRING(quality_flag), 2) + ',' + quality_string + ',' + $
           STRTRIM(STRING(suspicious_flag), 2) + ',' + diagnostic_reason

    PRINTF, lun, line

    CATCH, /CANCEL

  ENDFOR

  FREE_LUN, lun

  PRINT, 'Processed files: ', nfiles
  PRINT, 'Wrote CSV: ', output_csv

END
