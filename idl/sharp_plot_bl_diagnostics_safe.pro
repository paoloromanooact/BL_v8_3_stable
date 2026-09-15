PRO sharp_plot_bl_diagnostics_safe, br_map, pos_centroid, neg_centroid, $
                                    OUTFILE=outfile, TITLE=title, RANGE=range, $
                                    TILT_DEG=tilt_deg, TILT_REDUCED_DEG=tilt_reduced_deg, $
                                    PHI=phi, SEPARATION=separation, S_BL=s_bl, $
                                    HALE_SIGN=hale_sign, VALID_BL=valid_bl, $
                                    QUALITY_STRING=quality_string, REASON=reason
  ;+
  ; NAME:
  ;   sharp_plot_bl_diagnostics_safe
  ; PURPOSE:
  ;   Save a robust PNG diagnostic for one SHARP Br map. The image is scaled
  ;   to the plotting device before TV is called, avoiding TVSCL coordinate
  ;   errors for large CEA patches.
  ;-
  COMPILE_OPT idl2, strictarr

  sz = SIZE(br_map, /DIMENSIONS)
  IF N_ELEMENTS(sz) NE 2 THEN MESSAGE, 'br_map must be a 2D array'
  nx = sz[0] & ny = sz[1]

  IF N_ELEMENTS(title) EQ 0 THEN title = 'SHARP BL diagnostic'
  IF N_ELEMENTS(range) EQ 0 THEN maxabs = 1500D ELSE maxabs = DOUBLE(range)
  IF N_ELEMENTS(outfile) EQ 0 THEN outfile = 'sharp_bl_diagnostic.png'

  old_device = !D.NAME
  SET_PLOT, 'Z'

  xsize = 1000L
  ysize = 760L
  DEVICE, SET_RESOLUTION=[xsize, ysize], Z_BUFFER=0
  ERASE, 255
  LOADCT, 0, /SILENT

  margin_l = 30D
  margin_b = 150D
  margin_r = 30D
  margin_t = 30D
  avail_w = DOUBLE(xsize) - margin_l - margin_r
  avail_h = DOUBLE(ysize) - margin_b - margin_t

  scale = avail_w / DOUBLE(nx)
  IF (avail_h / DOUBLE(ny)) LT scale THEN scale = avail_h / DOUBLE(ny)
  plot_w = LONG(nx * scale)
  plot_h = LONG(ny * scale)
  IF plot_w LT 1 THEN plot_w = 1
  IF plot_h LT 1 THEN plot_h = 1

  x0 = LONG((DOUBLE(xsize) - plot_w) / 2D)
  y0 = LONG(ysize - margin_t - plot_h)

  img = BYTSCL(br_map, MIN=-maxabs, MAX=maxabs, TOP=254)
  img2 = CONGRID(img, plot_w, plot_h, /INTERP)
  TV, img2, x0, y0, /DEVICE

  ; Convert data coordinates to device coordinates.
  sx = DOUBLE(plot_w) / DOUBLE(nx)
  sy = DOUBLE(plot_h) / DOUBLE(ny)

  have_pos = (N_ELEMENTS(pos_centroid) EQ 2) AND FINITE(pos_centroid[0]) AND FINITE(pos_centroid[1])
  have_neg = (N_ELEMENTS(neg_centroid) EQ 2) AND FINITE(neg_centroid[0]) AND FINITE(neg_centroid[1])

  IF have_pos THEN BEGIN
    px = x0 + pos_centroid[0] * sx
    py = y0 + pos_centroid[1] * sy
    PLOTS, px, py, /DEVICE, PSYM=4, SYMSIZE=2.5, THICK=3, COLOR=254
    XYOUTS, px + 8, py + 8, 'B+', /DEVICE, CHARSIZE=1.1, COLOR=254
  ENDIF

  IF have_neg THEN BEGIN
    nxp = x0 + neg_centroid[0] * sx
    nyp = y0 + neg_centroid[1] * sy
    PLOTS, nxp, nyp, /DEVICE, PSYM=1, SYMSIZE=2.5, THICK=3, COLOR=254
    XYOUTS, nxp + 8, nyp + 8, 'B-', /DEVICE, CHARSIZE=1.1, COLOR=254
  ENDIF

  IF have_pos AND have_neg THEN BEGIN
    PLOTS, [px, nxp], [py, nyp], /DEVICE, THICK=3, COLOR=254
  ENDIF

  ytxt = 120L
  XYOUTS, 30, ytxt, title, /DEVICE, CHARSIZE=1.15, COLOR=254
  ytxt = ytxt - 18
  IF N_ELEMENTS(reason) GT 0 THEN BEGIN
    XYOUTS, 30, ytxt, 'reason = ' + STRTRIM(reason, 2), /DEVICE, CHARSIZE=0.95, COLOR=254
    ytxt = ytxt - 16
  ENDIF
  IF N_ELEMENTS(quality_string) GT 0 THEN BEGIN
    XYOUTS, 30, ytxt, 'quality = ' + STRTRIM(quality_string, 2), /DEVICE, CHARSIZE=0.95, COLOR=254
    ytxt = ytxt - 16
  ENDIF
  IF N_ELEMENTS(tilt_reduced_deg) GT 0 THEN BEGIN
    XYOUTS, 30, ytxt, 'tilt_red = ' + sharp_num_to_string(tilt_reduced_deg) + ' deg', /DEVICE, CHARSIZE=0.95, COLOR=254
    ytxt = ytxt - 16
  ENDIF
  IF N_ELEMENTS(tilt_deg) GT 0 THEN BEGIN
    XYOUTS, 30, ytxt, 'tilt_raw = ' + sharp_num_to_string(tilt_deg) + ' deg', /DEVICE, CHARSIZE=0.95, COLOR=254
    ytxt = ytxt - 16
  ENDIF
  IF N_ELEMENTS(phi) GT 0 THEN BEGIN
    XYOUTS, 30, ytxt, 'Phi = ' + sharp_num_to_string(phi), /DEVICE, CHARSIZE=0.95, COLOR=254
    ytxt = ytxt - 16
  ENDIF
  IF N_ELEMENTS(separation) GT 0 THEN BEGIN
    XYOUTS, 30, ytxt, 'd = ' + sharp_num_to_string(separation), /DEVICE, CHARSIZE=0.95, COLOR=254
    ytxt = ytxt - 16
  ENDIF
  IF N_ELEMENTS(s_bl) GT 0 THEN BEGIN
    XYOUTS, 30, ytxt, 'SBL = ' + sharp_num_to_string(s_bl), /DEVICE, CHARSIZE=0.95, COLOR=254
    ytxt = ytxt - 16
  ENDIF
  IF N_ELEMENTS(hale_sign) GT 0 THEN BEGIN
    XYOUTS, 30, ytxt, 'hale_sign = ' + STRTRIM(STRING(hale_sign), 2), /DEVICE, CHARSIZE=0.95, COLOR=254
    ytxt = ytxt - 16
  ENDIF
  IF N_ELEMENTS(valid_bl) GT 0 THEN BEGIN
    XYOUTS, 30, ytxt, 'valid_bl = ' + STRTRIM(STRING(valid_bl), 2), /DEVICE, CHARSIZE=0.95, COLOR=254
  ENDIF

  image = TVRD(TRUE=1)
  WRITE_PNG, outfile, image
  SET_PLOT, old_device
END
