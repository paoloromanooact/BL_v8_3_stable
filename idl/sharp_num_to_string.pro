FUNCTION sharp_num_to_string, value
  ; Return a compact numeric string for CSV output.
  COMPILE_OPT idl2, strictarr

  IF N_ELEMENTS(value) EQ 0 THEN RETURN, ''
  IF SIZE(value, /TYPE) EQ 7 THEN RETURN, STRTRIM(value, 2)

  v = DOUBLE(value[0])
  IF ~FINITE(v) THEN RETURN, 'NaN'

  av = ABS(v)
  IF (av GT 0D AND av LT 1D-3) OR (av GE 1D5) THEN BEGIN
    RETURN, STRTRIM(STRING(v, FORMAT='(E16.8)'), 2)
  ENDIF ELSE BEGIN
    RETURN, STRTRIM(STRING(v, FORMAT='(F18.8)'), 2)
  ENDELSE
END
