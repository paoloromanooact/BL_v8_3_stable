FUNCTION sharp_sintilt_1ar, pos_centroid, neg_centroid, LEADING_SIGN=leading_sign, $
                            TILT_DEG=tilt_deg, LEAD_CENTROID=lead_centroid, $
                            FOLLOW_CENTROID=follow_centroid

  COMPILE_OPT idl2, strictarr

  IF N_ELEMENTS(pos_centroid) NE 2 THEN MESSAGE, 'pos_centroid must have 2 elements'
  IF N_ELEMENTS(neg_centroid) NE 2 THEN MESSAGE, 'neg_centroid must have 2 elements'

  IF N_ELEMENTS(leading_sign) EQ 0 THEN $
    MESSAGE, 'Specify LEADING_SIGN=+1 or -1'

  IF FIX(leading_sign) EQ 1 THEN BEGIN

    lead_centroid   = DOUBLE(pos_centroid)
    follow_centroid = DOUBLE(neg_centroid)

  ENDIF ELSE IF FIX(leading_sign) EQ -1 THEN BEGIN

    lead_centroid   = DOUBLE(neg_centroid)
    follow_centroid = DOUBLE(pos_centroid)

  ENDIF ELSE BEGIN

    MESSAGE, 'LEADING_SIGN must be +1 or -1'

  ENDELSE

  sintilt = sharp_sintilt_from_centroids_1ar(lead_centroid, follow_centroid, $
                                             TILT_DEG=tilt_deg)

  RETURN, sintilt

END
