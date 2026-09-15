FUNCTION sharp_flux_1ar, br_map, pixel_area_cm2, MASK=mask, $
                        THRESHOLD=threshold, MAX_ABS_BR=max_abs_br, $
                        SIGNED=signed, NPIX=npix
  COMPILE_OPT idl2, strictarr
  sz = SIZE(br_map, /DIMENSIONS)
  IF N_ELEMENTS(sz) NE 2 THEN MESSAGE, 'br_map must be a 2D array'
  IF N_ELEMENTS(threshold) EQ 0 THEN threshold = 0D

  use_mask = sharp_build_mask_1ar(br_map, MASK=mask, THRESHOLD=threshold, $
                                  MAX_ABS_BR=max_abs_br, NVALID=npix)
  IF npix EQ 0 THEN RETURN, 0D
  idx = WHERE(use_mask NE 0, count)

  IF N_ELEMENTS(pixel_area_cm2) EQ 1 THEN BEGIN
    area_vals = DBLARR(count) + DOUBLE(pixel_area_cm2)
  ENDIF ELSE BEGIN
    IF TOTAL(ABS(SIZE(pixel_area_cm2, /DIMENSIONS)-sz)) NE 0 THEN MESSAGE, 'pixel_area_cm2 dimension mismatch'
    area_vals = DOUBLE(pixel_area_cm2[idx])
  ENDELSE

  br_vals = DOUBLE(br_map[idx])
  IF KEYWORD_SET(signed) THEN flux = TOTAL(br_vals * area_vals, /DOUBLE) ELSE flux = TOTAL(ABS(br_vals) * area_vals, /DOUBLE)
  RETURN, flux
END
