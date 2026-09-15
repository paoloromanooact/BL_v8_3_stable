FUNCTION sharp_cycle_from_date, date_string
  ;+
  ; NAME:
  ;   sharp_cycle_from_date
  ;
  ; PURPOSE:
  ;   Return the solar cycle number for HMI-era SHARP dates.
  ;   This helper is intentionally simple and currently supports the
  ;   cycles needed for HMI/SHARP work:
  ;     cycle 24 before 2019 December
  ;     cycle 25 from 2019 December onward
  ;
  ; INPUT:
  ;   date_string : date-like string, e.g. '20240508',
  ;                 '2024.05.08_03:12:00_TAI', or a SHARP filename.
  ;-
  COMPILE_OPT idl2, strictarr

  digits = sharp_digits_from_string(date_string)

  ; If a full filename is passed, the first digits can be from '720s' or HARPNUM.
  ; Prefer the first 8-digit block that looks like YYYYMMDD with year 20xx.
  year = -1
  month = -1

  n = STRLEN(digits)
  IF n LT 8 THEN MESSAGE, 'Could not parse date_string: ' + STRING(date_string)

  FOR i = 0L, n-8L DO BEGIN
    block = STRMID(digits, i, 8)
    yy = FIX(STRMID(block, 0, 4))
    mm = FIX(STRMID(block, 4, 2))
    dd = FIX(STRMID(block, 6, 2))
    IF (yy GE 2010) AND (yy LE 2035) AND (mm GE 1) AND (mm LE 12) AND $
       (dd GE 1) AND (dd LE 31) THEN BEGIN
      year = yy
      month = mm
      BREAK
    ENDIF
  ENDFOR

  IF year LT 0 THEN BEGIN
    year = FIX(STRMID(digits, 0, 4))
    month = FIX(STRMID(digits, 4, 2))
  ENDIF

  IF (year GT 2019) OR ((year EQ 2019) AND (month GE 12)) THEN RETURN, 25

  RETURN, 24
END
