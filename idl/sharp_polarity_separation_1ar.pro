FUNCTION sharp_polarity_separation_1ar, br_map, MASK=mask, $
                                         THRESHOLD=threshold, MAX_ABS_BR=max_abs_br, $
                                         PIXSCALE_CM=pixscale_cm, $
                                         X_MAP=x_map, Y_MAP=y_map, $
                                         POS_CENTROID=pos_centroid, NEG_CENTROID=neg_centroid, $
                                         NPOS=npos, NNEG=nneg, NVALID=nvalid
  ; Computes flux-weighted polarity-centroid separation.
  COMPILE_OPT idl2, strictarr

  sz = SIZE(br_map, /DIMENSIONS)
  IF N_ELEMENTS(sz) NE 2 THEN MESSAGE, 'br_map must be a 2D array'
  nx = sz[0]
  ny = sz[1]
  IF N_ELEMENTS(threshold) EQ 0 THEN threshold = 0D

  use_mask = sharp_build_mask_1ar(br_map, MASK=mask, THRESHOLD=0D, $
                                  MAX_ABS_BR=max_abs_br, NVALID=nvalid)

  IF (N_ELEMENTS(x_map) GT 0) XOR (N_ELEMENTS(y_map) GT 0) THEN MESSAGE, 'Supply both X_MAP and Y_MAP'
  use_maps = (N_ELEMENTS(x_map) GT 0)

  IF use_maps THEN BEGIN
    IF TOTAL(ABS(SIZE(x_map, /DIMENSIONS)-sz)) NE 0 THEN MESSAGE, 'X_MAP dimension mismatch'
    IF TOTAL(ABS(SIZE(y_map, /DIMENSIONS)-sz)) NE 0 THEN MESSAGE, 'Y_MAP dimension mismatch'
    use_mask = use_mask AND BYTE(FINITE(x_map)) AND BYTE(FINITE(y_map))
  ENDIF ELSE BEGIN
    x_map = REBIN(DINDGEN(nx), nx, ny)
    y_map = TRANSPOSE(REBIN(DINDGEN(ny), ny, nx))
  ENDELSE

  pos_mask = use_mask AND BYTE(br_map GE threshold)
  neg_mask = use_mask AND BYTE(br_map LE -threshold)

  ipos = WHERE(pos_mask NE 0, npos)
  ineg = WHERE(neg_mask NE 0, nneg)

  IF (npos EQ 0) OR (nneg EQ 0) THEN BEGIN
    pos_centroid = [!VALUES.D_NAN, !VALUES.D_NAN]
    neg_centroid = [!VALUES.D_NAN, !VALUES.D_NAN]
    RETURN, !VALUES.D_NAN
  ENDIF

  wpos = DOUBLE(br_map[ipos])
  wneg = ABS(DOUBLE(br_map[ineg]))
  swp = TOTAL(wpos, /DOUBLE)
  swn = TOTAL(wneg, /DOUBLE)

  IF (swp LE 0D) OR (swn LE 0D) THEN BEGIN
    pos_centroid = [!VALUES.D_NAN, !VALUES.D_NAN]
    neg_centroid = [!VALUES.D_NAN, !VALUES.D_NAN]
    RETURN, !VALUES.D_NAN
  ENDIF

  xcp = TOTAL(DOUBLE(x_map[ipos]) * wpos, /DOUBLE) / swp
  ycp = TOTAL(DOUBLE(y_map[ipos]) * wpos, /DOUBLE) / swp
  xcn = TOTAL(DOUBLE(x_map[ineg]) * wneg, /DOUBLE) / swn
  ycn = TOTAL(DOUBLE(y_map[ineg]) * wneg, /DOUBLE) / swn

  pos_centroid = [xcp, ycp]
  neg_centroid = [xcn, ycn]

  d = SQRT((xcp-xcn)^2 + (ycp-ycn)^2)
  IF (~use_maps) AND (N_ELEMENTS(pixscale_cm) GT 0) THEN d = d * DOUBLE(pixscale_cm)
  RETURN, d
END
