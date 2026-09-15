FUNCTION sharp_coslat_from_map_1ar, lat_map_deg, MASK=mask, BR_MAP=br_map, $
                                    THRESHOLD=threshold, MAX_ABS_BR=max_abs_br, $
                                    LAT_MEAN=lat_mean, NVALID=nvalid
  COMPILE_OPT idl2, strictarr

  sz = SIZE(lat_map_deg, /DIMENSIONS)
  IF N_ELEMENTS(sz) NE 2 THEN MESSAGE, 'lat_map_deg must be a 2D array'
  IF N_ELEMENTS(threshold) EQ 0 THEN threshold = 0D

  IF N_ELEMENTS(br_map) GT 0 THEN BEGIN
    IF TOTAL(ABS(SIZE(br_map, /DIMENSIONS)-sz)) NE 0 THEN MESSAGE, 'BR_MAP dimension mismatch'
    use_mask = sharp_build_mask_1ar(br_map, MASK=mask, THRESHOLD=threshold, $
                                    MAX_ABS_BR=max_abs_br, NVALID=nvalid)
    weighted = 1B
  ENDIF ELSE BEGIN
    use_mask = BYTE(FINITE(lat_map_deg))
    IF N_ELEMENTS(mask) GT 0 THEN BEGIN
      IF TOTAL(ABS(SIZE(mask, /DIMENSIONS)-sz)) NE 0 THEN MESSAGE, 'MASK dimension mismatch'
      use_mask = use_mask AND BYTE(mask NE 0)
    ENDIF
    weighted = 0B
  ENDELSE

  use_mask = use_mask AND BYTE(FINITE(lat_map_deg))
  idx = WHERE(use_mask NE 0, nvalid)

  IF nvalid EQ 0 THEN BEGIN
    lat_mean = !VALUES.D_NAN
    RETURN, !VALUES.D_NAN
  ENDIF

  lat_vals = DOUBLE(lat_map_deg[idx])

  IF weighted THEN BEGIN
    w = ABS(DOUBLE(br_map[idx]))
    sw = TOTAL(w, /DOUBLE)
    IF sw LE 0D THEN BEGIN
      lat_mean = !VALUES.D_NAN
      RETURN, !VALUES.D_NAN
    ENDIF
    lat_mean = TOTAL(lat_vals * w, /DOUBLE) / sw
  ENDIF ELSE BEGIN
    lat_mean = TOTAL(lat_vals, /DOUBLE) / DOUBLE(nvalid)
  ENDELSE

  RETURN, COS(lat_mean * !DPI / 180D)
END
