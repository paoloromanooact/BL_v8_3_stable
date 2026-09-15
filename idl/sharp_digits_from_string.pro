FUNCTION sharp_digits_from_string, input_string
  ;+
  ; NAME:
  ;   sharp_digits_from_string
  ;
  ; PURPOSE:
  ;   Return only the decimal digits contained in input_string.
  ;   Useful for dates such as:
  ;     '2024.05.08_03:12:00_TAI'
  ;     '20240508'
  ;     'hmi.sharp_cea_720s.11149.20240508_031200_TAI.Br.fits'
  ;-
  COMPILE_OPT idl2, strictarr

  s = STRING(input_string)
  out = ''

  FOR i = 0L, STRLEN(s)-1L DO BEGIN
    c = STRMID(s, i, 1)
    IF (c GE '0') AND (c LE '9') THEN out = out + c
  ENDFOR

  RETURN, out
END
