PRO sharp_plot_bl_diagnostics, br_map, pos_centroid, neg_centroid, $
                               OUTFILE=outfile, MASK=mask, TITLE=title, $
                               RANGE=range, TILT_DEG=tilt_deg, $
                               TILT_REDUCED_DEG=tilt_reduced_deg, $
                               PHI=phi, SEPARATION=separation, S_BL=s_bl, $
                               HALE_SIGN=hale_sign, VALID_BL=valid_bl
  ;+
  ; NAME:
  ;   sharp_plot_bl_diagnostics
  ; PURPOSE:
  ;   Plot a SHARP Br map with polarity centroids and their connecting axis.
  ;   If OUTFILE is supplied, save a PNG image.
  ; NOTES:
  ;   This is a lightweight IDL/SSW diagnostic. Colors are device-dependent.
  ;-
  COMPILE_OPT idl2, strictarr

  sz = SIZE(br_map, /DIMENSIONS)
  IF N_ELEMENTS(sz) NE 2 THEN MESSAGE, 'br_map must be a 2D array'
  nx = sz[0]
  ny = sz[1]

  IF N_ELEMENTS(title) EQ 0 THEN title = 'SHARP BL diagnostic'
  IF N_ELEMENTS(range) EQ 0 THEN maxabs = 1500D ELSE maxabs = DOUBLE(range)

  old_device = !D.NAME
  save_to_file = (N_ELEMENTS(outfile) GT 0)

  IF save_to_file THEN BEGIN
    SET_PLOT, 'Z'
    DEVICE, SET_RESOLUTION=[900,700], Z_BUFFER=0
  ENDIF ELSE BEGIN
    WINDOW, /FREE, XSIZE=900, YSIZE=700, TITLE=title
  ENDELSE

  LOADCT, 0, /SILENT
  img = BYTSCL(br_map, MIN=-maxabs, MAX=maxabs, TOP=254)
  TVSCL, img

  IF N_ELEMENTS(mask) GT 0 THEN BEGIN
    CONTOUR, mask, /OVERPLOT, LEVELS=[0.5], C_THICK=2
  ENDIF

  IF (N_ELEMENTS(pos_centroid) EQ 2) AND (N_ELEMENTS(neg_centroid) EQ 2) THEN BEGIN
    IF FINITE(pos_centroid[0]) AND FINITE(pos_centroid[1]) THEN $
      PLOTS, pos_centroid[0], pos_centroid[1], PSYM=4, SYMSIZE=2.5, THICK=3
    IF FINITE(neg_centroid[0]) AND FINITE(neg_centroid[1]) THEN $
      PLOTS, neg_centroid[0], neg_centroid[1], PSYM=1, SYMSIZE=2.5, THICK=3
    IF FINITE(pos_centroid[0]) AND FINITE(pos_centroid[1]) AND $
       FINITE(neg_centroid[0]) AND FINITE(neg_centroid[1]) THEN $
      PLOTS, [pos_centroid[0], neg_centroid[0]], [pos_centroid[1], neg_centroid[1]], THICK=3
  ENDIF

  y0 = ny - 25
  XYOUTS, 15, y0, title, /DEVICE, CHARSIZE=1.2
  y0 = y0 - 22
  IF N_ELEMENTS(tilt_reduced_deg) GT 0 THEN BEGIN
    XYOUTS, 15, y0, 'tilt_red = ' + sharp_num_to_string(tilt_reduced_deg) + ' deg', /DEVICE, CHARSIZE=1.0
    y0 = y0 - 18
  ENDIF
  IF N_ELEMENTS(tilt_deg) GT 0 THEN BEGIN
    XYOUTS, 15, y0, 'tilt_raw = ' + sharp_num_to_string(tilt_deg) + ' deg', /DEVICE, CHARSIZE=1.0
    y0 = y0 - 18
  ENDIF
  IF N_ELEMENTS(phi) GT 0 THEN BEGIN
    XYOUTS, 15, y0, 'Phi = ' + sharp_num_to_string(phi), /DEVICE, CHARSIZE=1.0
    y0 = y0 - 18
  ENDIF
  IF N_ELEMENTS(separation) GT 0 THEN BEGIN
    XYOUTS, 15, y0, 'd = ' + sharp_num_to_string(separation), /DEVICE, CHARSIZE=1.0
    y0 = y0 - 18
  ENDIF
  IF N_ELEMENTS(s_bl) GT 0 THEN BEGIN
    XYOUTS, 15, y0, 'SBL = ' + sharp_num_to_string(s_bl), /DEVICE, CHARSIZE=1.0
    y0 = y0 - 18
  ENDIF
  IF N_ELEMENTS(hale_sign) GT 0 THEN BEGIN
    XYOUTS, 15, y0, 'hale_sign = ' + STRTRIM(STRING(hale_sign), 2), /DEVICE, CHARSIZE=1.0
    y0 = y0 - 18
  ENDIF
  IF N_ELEMENTS(valid_bl) GT 0 THEN BEGIN
    XYOUTS, 15, y0, 'valid_bl = ' + STRTRIM(STRING(valid_bl), 2), /DEVICE, CHARSIZE=1.0
  ENDIF

  IF save_to_file THEN BEGIN
    image = TVRD(TRUE=1)
    WRITE_PNG, outfile, image
    SET_PLOT, old_device
  ENDIF
END
