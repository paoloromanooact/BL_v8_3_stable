FUNCTION sharp_expected_leading_sign, date_string, latitude_deg, CYCLE=cycle
  ;+
  ; NAME:
  ;   sharp_expected_leading_sign
  ;
  ; PURPOSE:
  ;   Expected Hale-law sign of the leading polarity for a given date and hemisphere.
  ;
  ; OUTPUT:
  ;   +1 : expected leading polarity is positive
  ;   -1 : expected leading polarity is negative
  ;
  ; CONVENTION IMPLEMENTED:
  ;   Cycle 24: North leading negative, South leading positive
  ;   Cycle 25: North leading positive, South leading negative
  ;-
  COMPILE_OPT idl2, strictarr

  cycle = sharp_cycle_from_date(date_string)

  hemi = 1
  IF DOUBLE(latitude_deg) LT 0D THEN hemi = -1

  IF (cycle MOD 2) EQ 1 THEN BEGIN
    ; Odd cycles, e.g. 25: North +, South -
    expected = hemi
  ENDIF ELSE BEGIN
    ; Even cycles, e.g. 24: North -, South +
    expected = -hemi
  ENDELSE

  RETURN, expected
END
