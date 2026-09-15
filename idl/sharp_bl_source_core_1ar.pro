FUNCTION sharp_bl_source_core_1ar, flux, separation, coslat, sintilt, HALE_SIGN=hale_sign
  COMPILE_OPT idl2, strictarr
  IF N_ELEMENTS(hale_sign) EQ 0 THEN hale_sign=1
  IF ~FINITE(flux) OR ~FINITE(separation) OR ~FINITE(coslat) OR ~FINITE(sintilt) THEN RETURN,!VALUES.D_NAN
  RETURN, DOUBLE(hale_sign)*DOUBLE(flux)*DOUBLE(separation)*DOUBLE(coslat)*DOUBLE(sintilt)
END
