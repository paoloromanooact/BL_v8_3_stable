FUNCTION sharp_bl_source_1ar, br_map, lat_map_deg, pixel_area_cm2, $
                              MASK=external_mask, BMAP=bmap, THRESHOLD=threshold, $
                              MAX_ABS_BR=max_abs_br, BMAP_MIN=bmap_min, $
                              PIXSCALE_CM=pixscale_cm, X_MAP=x_map, Y_MAP=y_map, $
                              LEADING_SIGN=leading_sign, HALE_SIGN=hale_sign, $
                              DATE_STRING=date_string, AUTO_SIGNS=auto_signs, $
                              LEADING_SIDE=leading_side, $
                              EXPECTED_LEADING_SIGN=expected_leading_sign, $
                              CYCLE=cycle, DEBUG=debug
  ;+
  ; NAME:
  ;   sharp_bl_source_1ar
  ;
  ; PURPOSE:
  ;   Compute the BL-source proxy for one SHARP AR at one time.
  ;
  ; V7 NOTE:
  ;   The common mask is built once using sharp_build_mask_1ar.
  ;   The SHARP bitmap, if available, is supplied with BMAP=, not BITMAP=,
  ;   to avoid IDL keyword ambiguity.
  ;-
  COMPILE_OPT idl2, strictarr

  IF N_ELEMENTS(threshold) EQ 0 THEN threshold = 100D
  IF N_ELEMENTS(max_abs_br) EQ 0 THEN max_abs_br = 10000D
  IF N_ELEMENTS(bmap_min) EQ 0 THEN bmap_min = 1D

  IF N_ELEMENTS(bmap) GT 0 THEN BEGIN
    analysis_mask = sharp_build_mask_1ar(br_map, bmap, MASK=external_mask, $
                                         THRESHOLD=0D, MAX_ABS_BR=max_abs_br, $
                                         BMAP_MIN=bmap_min, NVALID=nmask)
  ENDIF ELSE BEGIN
    analysis_mask = sharp_build_mask_1ar(br_map, MASK=external_mask, $
                                         THRESHOLD=0D, MAX_ABS_BR=max_abs_br, $
                                         NVALID=nmask)
  ENDELSE

  phi = sharp_flux_1ar(br_map, pixel_area_cm2, MASK=analysis_mask, $
                       THRESHOLD=threshold, MAX_ABS_BR=max_abs_br, NPIX=npix_flux)

  d = sharp_polarity_separation_1ar(br_map, MASK=analysis_mask, $
                                    THRESHOLD=threshold, MAX_ABS_BR=max_abs_br, $
                                    PIXSCALE_CM=pixscale_cm, X_MAP=x_map, Y_MAP=y_map, $
                                    POS_CENTROID=cp, NEG_CENTROID=cn, $
                                    NPOS=npos, NNEG=nneg, NVALID=nvalid)

  coslat = sharp_coslat_from_map_1ar(lat_map_deg, MASK=analysis_mask, BR_MAP=br_map, $
                                     THRESHOLD=threshold, MAX_ABS_BR=max_abs_br, $
                                     LAT_MEAN=lat_mean)

  need_auto = KEYWORD_SET(auto_signs)
  IF N_ELEMENTS(leading_sign) EQ 0 THEN need_auto = 1B
  IF N_ELEMENTS(hale_sign) EQ 0 THEN need_auto = 1B

  IF need_auto THEN BEGIN
    IF N_ELEMENTS(date_string) EQ 0 THEN $
      MESSAGE, 'DATE_STRING is required when using /AUTO_SIGNS or omitted signs'

    sharp_auto_leading_hale, cp, cn, lat_mean, date_string, $
                             LEADING_SIGN=leading_sign, HALE_SIGN=hale_sign, $
                             EXPECTED_LEADING_SIGN=expected_leading_sign, $
                             CYCLE=cycle, LEADING_SIDE=leading_side
  ENDIF ELSE BEGIN
    IF N_ELEMENTS(date_string) GT 0 THEN $
      expected_leading_sign = sharp_expected_leading_sign(date_string, lat_mean, CYCLE=cycle)
  ENDELSE

  sintilt = sharp_sintilt_1ar(cp, cn, LEADING_SIGN=leading_sign, TILT_DEG=tilt_deg)
  s_bl = sharp_bl_source_core_1ar(phi, d, coslat, sintilt, HALE_SIGN=hale_sign)

  IF KEYWORD_SET(debug) THEN BEGIN
    PRINT, '--- DEBUG BL SOURCE V7 ---'
    PRINT, 'Flux [Mx]              = ', phi
    PRINT, 'Separation             = ', d
    PRINT, 'lat_mean [deg]         = ', lat_mean
    PRINT, 'cos(lambda)            = ', coslat
    PRINT, 'tilt [deg]             = ', tilt_deg
    PRINT, 'sin(alpha)             = ', sintilt
    PRINT, 'centroid +             = ', cp
    PRINT, 'centroid -             = ', cn
    PRINT, 'nmask                  = ', nmask
    PRINT, 'nvalid                 = ', nvalid
    PRINT, 'npos/nneg              = ', npos, nneg
    PRINT, 'leading_sign           = ', leading_sign
    PRINT, 'hale_sign              = ', hale_sign
    IF N_ELEMENTS(expected_leading_sign) GT 0 THEN PRINT, 'expected_leading_sign  = ', expected_leading_sign
    IF N_ELEMENTS(cycle) GT 0 THEN PRINT, 'cycle                  = ', cycle
    PRINT, 'S_BL                   = ', s_bl
  ENDIF

  RETURN, s_bl
END
