FUNCTION sharp_bl_quality_flag, phi, separation, lat_mean, coslat, sintilt, s_bl, npos, nneg, nmask, $
                                VALID_BL=valid_bl, FLAG_STRING=flag_string
  ;+
  ; NAME:
  ;   sharp_bl_quality_flag
  ; PURPOSE:
  ;   Return a compact quality flag for one BL-source measurement.
  ;
  ; FLAG CODES:
  ;   0 = OK
  ;   1 = no positive polarity above threshold
  ;   2 = no negative polarity above threshold
  ;   3 = no usable polarities above threshold
  ;   4 = invalid/empty analysis mask
  ;   5 = invalid flux
  ;   6 = invalid geometry/tilt/source
  ;-
  COMPILE_OPT idl2, strictarr

  valid_bl = 0
  flag_string = 'UNKNOWN'

  IF N_ELEMENTS(nmask) EQ 0 THEN nmask = 0
  IF N_ELEMENTS(npos) EQ 0 THEN npos = 0
  IF N_ELEMENTS(nneg) EQ 0 THEN nneg = 0

  IF nmask LE 0 THEN BEGIN
    flag_string = 'EMPTY_MASK'
    RETURN, 4
  ENDIF

  IF (npos LE 0) AND (nneg LE 0) THEN BEGIN
    flag_string = 'NO_POLARITIES'
    RETURN, 3
  ENDIF

  IF npos LE 0 THEN BEGIN
    flag_string = 'NO_POSITIVE'
    RETURN, 1
  ENDIF

  IF nneg LE 0 THEN BEGIN
    flag_string = 'NO_NEGATIVE'
    RETURN, 2
  ENDIF

  IF ~FINITE(phi) THEN BEGIN
    flag_string = 'BAD_FLUX'
    RETURN, 5
  ENDIF

  IF (~FINITE(separation)) OR (~FINITE(lat_mean)) OR (~FINITE(coslat)) OR $
     (~FINITE(sintilt)) OR (~FINITE(s_bl)) THEN BEGIN
    flag_string = 'BAD_GEOMETRY'
    RETURN, 6
  ENDIF

  valid_bl = 1
  flag_string = 'OK'
  RETURN, 0
END
