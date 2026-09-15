FUNCTION sharp_sintilt_from_centroids_1ar, lead_centroid, follow_centroid, TILT_DEG=tilt_deg
  COMPILE_OPT idl2, strictarr
  IF N_ELEMENTS(lead_centroid) NE 2 THEN MESSAGE,'lead_centroid must be [x,y]'
  IF N_ELEMENTS(follow_centroid) NE 2 THEN MESSAGE,'follow_centroid must be [x,y]'
  dx=DOUBLE(follow_centroid[0])-DOUBLE(lead_centroid[0])
  dy=DOUBLE(follow_centroid[1])-DOUBLE(lead_centroid[1])
  norm=SQRT(dx*dx+dy*dy)
  IF norm LE 0D THEN BEGIN tilt_deg=!VALUES.D_NAN & RETURN,!VALUES.D_NAN & ENDIF
  tilt_deg=ATAN(dy,dx)*180D/!DPI
  RETURN, dy/norm
END
