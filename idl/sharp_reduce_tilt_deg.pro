FUNCTION sharp_reduce_tilt_deg, tilt_deg
  ;+
  ; NAME:
  ;   sharp_reduce_tilt_deg
  ; PURPOSE:
  ;   Reduce a raw tilt angle to the interval [-90,+90] degrees.
  ;   This keeps the bipole axis readable while preserving sin(alpha)
  ;   through the separately stored sintilt value.
  ;-
  COMPILE_OPT idl2, strictarr

  IF ~FINITE(tilt_deg) THEN RETURN, !VALUES.D_NAN

  a = DOUBLE(tilt_deg)

  ; Bring to [-180,+180]
  WHILE a GT 180D DO a = a - 360D
  WHILE a LE -180D DO a = a + 360D

  ; Then fold axis direction into [-90,+90]
  IF a GT 90D THEN a = a - 180D
  IF a LT -90D THEN a = a + 180D

  RETURN, a
END
