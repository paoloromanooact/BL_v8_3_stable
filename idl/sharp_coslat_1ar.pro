FUNCTION sharp_coslat_1ar, latitude_deg
  COMPILE_OPT idl2, strictarr
  RETURN, COS(DOUBLE(latitude_deg)*!DPI/180D)
END
