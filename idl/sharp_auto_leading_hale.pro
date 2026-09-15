PRO sharp_auto_leading_hale, pos_centroid, neg_centroid, latitude_deg, date_string, $
                             LEADING_SIGN=leading_sign, HALE_SIGN=hale_sign, $
                             EXPECTED_LEADING_SIGN=expected_leading_sign, $
                             CYCLE=cycle, LEADING_SIDE=leading_side
  ;+
  ; NAME:
  ;   sharp_auto_leading_hale
  ;
  ; PURPOSE:
  ;   Determine automatically:
  ;     1) which magnetic polarity is geometrically leading;
  ;     2) whether the AR is Hale-oriented or anti-Hale.
  ;
  ; INPUTS:
  ;   pos_centroid : [x,y] centroid of positive polarity
  ;   neg_centroid : [x,y] centroid of negative polarity
  ;   latitude_deg : AR latitude in degrees
  ;   date_string  : date-like string or filename
  ;
  ; KEYWORDS:
  ;   LEADING_SIDE : which side of the CEA patch is treated as leading.
  ;                  Default = 'XMAX', which reproduces the tested example
  ;                  where the negative polarity at larger x was leading.
  ;                  Accepted values:
  ;                    'XMAX' or 'RIGHT' : larger x is leading
  ;                    'XMIN' or 'LEFT'  : smaller x is leading
  ;                    'WEST'            : alias for XMAX by default here
  ;                    'EAST'            : alias for XMIN by default here
  ;
  ; OUTPUT KEYWORDS:
  ;   LEADING_SIGN          : +1 if positive polarity is leading, -1 if negative
  ;   HALE_SIGN             : +1 if Hale, -1 if anti-Hale
  ;   EXPECTED_LEADING_SIGN : Hale-law expected leading sign
  ;   CYCLE                 : solar cycle number used
  ;-
  COMPILE_OPT idl2, strictarr

  IF N_ELEMENTS(pos_centroid) NE 2 THEN MESSAGE, 'pos_centroid must have 2 elements'
  IF N_ELEMENTS(neg_centroid) NE 2 THEN MESSAGE, 'neg_centroid must have 2 elements'
  IF N_ELEMENTS(date_string) EQ 0 THEN MESSAGE, 'date_string is required for automatic Hale sign'

  IF N_ELEMENTS(leading_side) EQ 0 THEN leading_side = 'XMAX'
  side = STRUPCASE(STRTRIM(leading_side, 2))

  CASE side OF
    'XMAX': x_larger_is_leading = 1B
    'RIGHT': x_larger_is_leading = 1B
    'WEST': x_larger_is_leading = 1B
    'XMIN': x_larger_is_leading = 0B
    'LEFT': x_larger_is_leading = 0B
    'EAST': x_larger_is_leading = 0B
    ELSE: MESSAGE, 'LEADING_SIDE must be XMAX, XMIN, RIGHT, LEFT, WEST, or EAST'
  ENDCASE

  IF x_larger_is_leading THEN BEGIN
    IF DOUBLE(pos_centroid[0]) GT DOUBLE(neg_centroid[0]) THEN BEGIN
      leading_sign = +1
    ENDIF ELSE BEGIN
      leading_sign = -1
    ENDELSE
  ENDIF ELSE BEGIN
    IF DOUBLE(pos_centroid[0]) LT DOUBLE(neg_centroid[0]) THEN BEGIN
      leading_sign = +1
    ENDIF ELSE BEGIN
      leading_sign = -1
    ENDELSE
  ENDELSE

  expected_leading_sign = sharp_expected_leading_sign(date_string, latitude_deg, CYCLE=cycle)

  IF FIX(leading_sign) EQ FIX(expected_leading_sign) THEN BEGIN
    hale_sign = +1
  ENDIF ELSE BEGIN
    hale_sign = -1
  ENDELSE
END
