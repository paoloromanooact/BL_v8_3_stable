
PRO sharp_rgb_draw_point, img, x, y, r, g, b
  COMPILE_OPT idl2, strictarr
  sz = SIZE(img, /DIMENSIONS)
  nx = sz[1] & ny = sz[2]
  xi = LONG(ROUND(x)) & yi = LONG(ROUND(y))
  IF (xi LT 0) OR (xi GE nx) OR (yi LT 0) OR (yi GE ny) THEN RETURN
  img[0, xi, yi] = BYTE(r)
  img[1, xi, yi] = BYTE(g)
  img[2, xi, yi] = BYTE(b)
END

PRO sharp_rgb_draw_line, img, x1, y1, x2, y2, r, g, b, THICK=thick
  COMPILE_OPT idl2, strictarr
  IF N_ELEMENTS(thick) EQ 0 THEN thick = 1L
  dx = DOUBLE(x2) - DOUBLE(x1)
  dy = DOUBLE(y2) - DOUBLE(y1)
  n = LONG(CEIL(MAX([ABS(dx), ABS(dy)]))) + 1L
  IF n LT 1 THEN n = 1L
  FOR i=0L, n DO BEGIN
    t = DOUBLE(i) / DOUBLE(n > 1L)
    x = DOUBLE(x1) + t*dx
    y = DOUBLE(y1) + t*dy
    FOR ox=-LONG(thick), LONG(thick) DO BEGIN
      FOR oy=-LONG(thick), LONG(thick) DO BEGIN
        sharp_rgb_draw_point, img, x+ox, y+oy, r, g, b
      ENDFOR
    ENDFOR
  ENDFOR
END

PRO sharp_rgb_draw_cross, img, x, y, r, g, b, SIZE=size, THICK=thick
  COMPILE_OPT idl2, strictarr
  IF N_ELEMENTS(size) EQ 0 THEN size = 8L
  IF N_ELEMENTS(thick) EQ 0 THEN thick = 1L
  sharp_rgb_draw_line, img, x-size, y, x+size, y, r, g, b, THICK=thick
  sharp_rgb_draw_line, img, x, y-size, x, y+size, r, g, b, THICK=thick
END

PRO sharp_rgb_overlay_boundary, img, mask, x0, y0, plot_w, plot_h, r, g, b, THICK=thick
  COMPILE_OPT idl2, strictarr
  IF N_ELEMENTS(mask) EQ 0 THEN RETURN
  IF N_ELEMENTS(thick) EQ 0 THEN thick = 0L
  sz = SIZE(mask, /DIMENSIONS)
  IF N_ELEMENTS(sz) NE 2 THEN RETURN
  scaled = CONGRID(BYTE(mask NE 0), plot_w, plot_h, /INTERP)
  bb = BYTE(scaled GT 0)
  inner = bb AND SHIFT(bb,1,0) AND SHIFT(bb,-1,0) AND SHIFT(bb,0,1) AND SHIFT(bb,0,-1)
  edge = bb AND BYTE(inner EQ 0)
  idx = WHERE(edge NE 0, nidx)
  IF nidx EQ 0 THEN RETURN
  xs = idx MOD plot_w
  ys = idx / plot_w
  FOR k=0L, nidx-1L DO BEGIN
    xx = x0 + xs[k]
    yy = y0 + ys[k]
    FOR ox=-LONG(thick), LONG(thick) DO BEGIN
      FOR oy=-LONG(thick), LONG(thick) DO BEGIN
        sharp_rgb_draw_point, img, xx+ox, yy+oy, r, g, b
      ENDFOR
    ENDFOR
  ENDFOR
END

PRO sharp_write_diagnostic_info, outfile, title, phi, separation, tilt_deg, tilt_reduced_deg, $
                                 hale_sign, valid_bl, quality_string, reason
  COMPILE_OPT idl2, strictarr
  txtfile = outfile + '.txt'
  OPENW, lun, txtfile, /GET_LUN
  PRINTF, lun, 'title: ', title
  IF N_ELEMENTS(reason) GT 0 THEN PRINTF, lun, 'reason: ', reason
  IF N_ELEMENTS(quality_string) GT 0 THEN PRINTF, lun, 'quality: ', quality_string
  IF N_ELEMENTS(phi) GT 0 THEN PRINTF, lun, 'phi_mx: ', sharp_num_to_string(phi)
  IF N_ELEMENTS(separation) GT 0 THEN PRINTF, lun, 'separation_cm: ', sharp_num_to_string(separation)
  IF N_ELEMENTS(tilt_deg) GT 0 THEN PRINTF, lun, 'tilt_raw_deg: ', sharp_num_to_string(tilt_deg)
  IF N_ELEMENTS(tilt_reduced_deg) GT 0 THEN PRINTF, lun, 'tilt_reduced_deg: ', sharp_num_to_string(tilt_reduced_deg)
  IF N_ELEMENTS(hale_sign) GT 0 THEN PRINTF, lun, 'hale_sign: ', STRTRIM(STRING(hale_sign),2)
  IF N_ELEMENTS(valid_bl) GT 0 THEN PRINTF, lun, 'valid_bl: ', STRTRIM(STRING(valid_bl),2)
  FREE_LUN, lun
END

PRO sharp_make_bl_diagnostic_png, br_map, pos_centroid, neg_centroid, $
                                  BMAP=bmap, ANALYSIS_MASK=analysis_mask, $
                                  OUTFILE=outfile, TITLE=title, RANGE=range, $
                                  TILT_DEG=tilt_deg, TILT_REDUCED_DEG=tilt_reduced_deg, $
                                  PHI=phi, SEPARATION=separation, S_BL=s_bl, $
                                  HALE_SIGN=hale_sign, VALID_BL=valid_bl, $
                                  QUALITY_STRING=quality_string, REASON=reason
  ;+
  ; NAME:
  ;   sharp_make_bl_diagnostic_png
  ; PURPOSE:
  ;   Robust diagnostic PNG writer that does not use TVSCL/TVRD. It writes a
  ;   true-color RGB PNG directly from arrays, with fixed Br contrast and
  ;   overlays for the SHARP bitmap boundary, analysis mask boundary, polarity
  ;   centroids, and the centroid-connecting segment.
  ; NOTES:
  ;   Color convention:
  ;     green/cyan boundary = SHARP bitmap
  ;     red/orange boundary = analysis mask |Br| threshold
  ;     yellow cross        = positive centroid
  ;     blue/cyan cross     = negative centroid
  ;     blue line           = positive-negative segment
  ;   Text metadata is saved in a sidecar .txt file because direct PNG drawing
  ;   is more reliable for long batch runs.
  ;-
  COMPILE_OPT idl2, strictarr

  sz = SIZE(br_map, /DIMENSIONS)
  IF N_ELEMENTS(sz) NE 2 THEN MESSAGE, 'br_map must be 2D'
  nx = sz[0] & ny = sz[1]
  IF N_ELEMENTS(outfile) EQ 0 THEN outfile = 'sharp_bl_diagnostic.png'
  IF N_ELEMENTS(title) EQ 0 THEN title = 'SHARP BL diagnostic'
  IF N_ELEMENTS(range) EQ 0 THEN maxabs = 1500D ELSE maxabs = DOUBLE(range)
  IF maxabs LE 0D THEN maxabs = 1500D

  xsize = 1200L
  ysize = 780L
  margin = 30L
  footer = 70L
  avail_w = xsize - 2L*margin
  avail_h = ysize - 2L*margin - footer
  scale = DOUBLE(avail_w)/DOUBLE(nx)
  IF DOUBLE(avail_h)/DOUBLE(ny) LT scale THEN scale = DOUBLE(avail_h)/DOUBLE(ny)
  plot_w = LONG(nx*scale)
  plot_h = LONG(ny*scale)
  IF plot_w LT 1L THEN plot_w = 1L
  IF plot_h LT 1L THEN plot_h = 1L
  x0 = LONG((xsize - plot_w)/2L)
  y0 = footer + LONG((avail_h - plot_h)/2L)

  canvas = BYTARR(3, xsize, ysize) + 255B

  ; Build clean grayscale Br image with fixed symmetric contrast.
  clean = DOUBLE(br_map)
  bad = WHERE(~FINITE(clean), nbad)
  IF nbad GT 0 THEN clean[bad] = 0D
  gray = BYTSCL(clean, MIN=-maxabs, MAX=maxabs, TOP=255)
  img = CONGRID(gray, plot_w, plot_h, /INTERP)

  ; Put grayscale into RGB canvas.
  FOR c=0,2 DO canvas[c, x0:x0+plot_w-1L, y0:y0+plot_h-1L] = img

  ; Boundaries.
  IF N_ELEMENTS(bmap) GT 0 THEN BEGIN
    sharp_rgb_overlay_boundary, canvas, BYTE(bmap GT 0), x0, y0, plot_w, plot_h, 0B, 220B, 220B, THICK=1
  ENDIF
  IF N_ELEMENTS(analysis_mask) GT 0 THEN BEGIN
    sharp_rgb_overlay_boundary, canvas, analysis_mask, x0, y0, plot_w, plot_h, 255B, 80B, 0B, THICK=1
  ENDIF

  sx = DOUBLE(plot_w) / DOUBLE(nx)
  sy = DOUBLE(plot_h) / DOUBLE(ny)
  have_pos = (N_ELEMENTS(pos_centroid) EQ 2) AND FINITE(pos_centroid[0]) AND FINITE(pos_centroid[1])
  have_neg = (N_ELEMENTS(neg_centroid) EQ 2) AND FINITE(neg_centroid[0]) AND FINITE(neg_centroid[1])

  IF have_pos THEN BEGIN
    px = x0 + pos_centroid[0]*sx
    py = y0 + pos_centroid[1]*sy
    sharp_rgb_draw_cross, canvas, px, py, 255B, 255B, 0B, SIZE=10, THICK=1
  ENDIF
  IF have_neg THEN BEGIN
    qx = x0 + neg_centroid[0]*sx
    qy = y0 + neg_centroid[1]*sy
    sharp_rgb_draw_cross, canvas, qx, qy, 0B, 180B, 255B, SIZE=10, THICK=1
  ENDIF
  IF have_pos AND have_neg THEN BEGIN
    sharp_rgb_draw_line, canvas, px, py, qx, qy, 0B, 80B, 255B, THICK=1
  ENDIF

  ; Small color legend strips in footer.
  sharp_rgb_draw_line, canvas, 30, 35, 120, 35, 0B, 220B, 220B, THICK=2
  sharp_rgb_draw_line, canvas, 30, 55, 120, 55, 255B, 80B, 0B, THICK=2
  sharp_rgb_draw_cross, canvas, 170, 35, 255B, 255B, 0B, SIZE=8, THICK=1
  sharp_rgb_draw_cross, canvas, 170, 55, 0B, 180B, 255B, SIZE=8, THICK=1

  WRITE_PNG, outfile, canvas
  sharp_write_diagnostic_info, outfile, title, phi, separation, tilt_deg, tilt_reduced_deg, $
                               hale_sign, valid_bl, quality_string, reason
END
