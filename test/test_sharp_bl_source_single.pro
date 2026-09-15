PRO test_sharp_bl_source_single, br_file, THRESHOLD=threshold, $
                                 MAX_ABS_BR=max_abs_br, BITMAP_FILE=bitmap_file, $
                                 BMAP_MIN=bmap_min, NO_BITMAP=no_bitmap, $
                                 LEADING_SIGN=leading_sign, HALE_SIGN=hale_sign, $
                                 AUTO_SIGNS=auto_signs, LEADING_SIDE=leading_side, $
                                 DATE_STRING=date_string, USE_MRDFITS=use_mrdfits
  ;+
  ; NAME:
  ;   test_sharp_bl_source_single
  ;
  ; PURPOSE:
  ;   Test the single-AR BL-source pipeline on one SHARP CEA Br FITS file.
  ;   V7 also tries to read the matching SHARP bitmap file automatically.
  ;
  ; EXAMPLES:
  ;   test_sharp_bl_source_single, file, THRESHOLD=100D, MAX_ABS_BR=10000D
  ;   test_sharp_bl_source_single, file, BITMAP_FILE='...bitmap.fits'
  ;   test_sharp_bl_source_single, file, /NO_BITMAP
  ;-
  COMPILE_OPT idl2, strictarr

  IF N_ELEMENTS(br_file) EQ 0 THEN MESSAGE, 'Provide a SHARP CEA Br FITS filename.'
  IF N_ELEMENTS(threshold) EQ 0 THEN threshold = 100D
  IF N_ELEMENTS(max_abs_br) EQ 0 THEN max_abs_br = 10000D
  IF N_ELEMENTS(bmap_min) EQ 0 THEN bmap_min = 1D
  IF N_ELEMENTS(date_string) EQ 0 THEN date_string = br_file

  IF KEYWORD_SET(use_mrdfits) THEN BEGIN
    br_map = MRDFITS(br_file, 1, hdr)
  ENDIF ELSE BEGIN
    read_sdo, br_file, hdr, br_map, /UNCOMP_DELETE
  ENDELSE

  sz = SIZE(br_map, /DIMENSIONS)
  nx = sz[0]
  ny = sz[1]

  used_bitmap = 0
  IF ~KEYWORD_SET(no_bitmap) THEN BEGIN
    IF N_ELEMENTS(bitmap_file) EQ 0 THEN bitmap_file = sharp_find_bitmap_file(br_file)
    IF bitmap_file NE '' THEN BEGIN
      IF KEYWORD_SET(use_mrdfits) THEN BEGIN
        bitmap = MRDFITS(bitmap_file, 1, bhdr)
      ENDIF ELSE BEGIN
        read_sdo, bitmap_file, bhdr, bitmap, /UNCOMP_DELETE
      ENDELSE
      IF TOTAL(ABS(SIZE(bitmap, /DIMENSIONS)-sz)) EQ 0 THEN used_bitmap = 1 ELSE used_bitmap = 0
    ENDIF
  ENDIF

  lat_map_deg = sharp_cea_latitude_map_from_header(hdr, NX=nx, NY=ny, SINLAT_MAP=sinlat_map)
  pixel_area_cm2 = sharp_cea_pixel_area_from_header(hdr, PIXSCALE_CM=pixscale_cm)

  IF used_bitmap THEN BEGIN
    mask = sharp_build_mask_1ar(br_map, bitmap, THRESHOLD=0D, $
                                MAX_ABS_BR=max_abs_br, BMAP_MIN=bmap_min, NVALID=nmask)
    phi = sharp_flux_1ar(br_map, pixel_area_cm2, MASK=mask, THRESHOLD=threshold, $
                         MAX_ABS_BR=max_abs_br, NPIX=npix_flux)
    d = sharp_polarity_separation_1ar(br_map, MASK=mask, THRESHOLD=threshold, $
                                      MAX_ABS_BR=max_abs_br, PIXSCALE_CM=pixscale_cm, $
                                      POS_CENTROID=cp, NEG_CENTROID=cn, $
                                      NPOS=npos, NNEG=nneg, NVALID=nvalid)
    coslat = sharp_coslat_from_map_1ar(lat_map_deg, MASK=mask, BR_MAP=br_map, $
                                       THRESHOLD=threshold, MAX_ABS_BR=max_abs_br, $
                                       LAT_MEAN=lat_mean)
  ENDIF ELSE BEGIN
    mask = sharp_build_mask_1ar(br_map, THRESHOLD=0D, MAX_ABS_BR=max_abs_br, NVALID=nmask)
    phi = sharp_flux_1ar(br_map, pixel_area_cm2, MASK=mask, THRESHOLD=threshold, $
                         MAX_ABS_BR=max_abs_br, NPIX=npix_flux)
    d = sharp_polarity_separation_1ar(br_map, MASK=mask, THRESHOLD=threshold, $
                                      MAX_ABS_BR=max_abs_br, PIXSCALE_CM=pixscale_cm, $
                                      POS_CENTROID=cp, NEG_CENTROID=cn, $
                                      NPOS=npos, NNEG=nneg, NVALID=nvalid)
    coslat = sharp_coslat_from_map_1ar(lat_map_deg, MASK=mask, BR_MAP=br_map, $
                                       THRESHOLD=threshold, MAX_ABS_BR=max_abs_br, $
                                       LAT_MEAN=lat_mean)
  ENDELSE

  sharp_plot_polarity_centroids_1ar, br_map, cp, cn, MASK=mask, RANGE=1500D

  need_auto = KEYWORD_SET(auto_signs)
  IF N_ELEMENTS(leading_sign) EQ 0 THEN need_auto = 1B
  IF N_ELEMENTS(hale_sign) EQ 0 THEN need_auto = 1B

  IF FINITE(d) AND FINITE(lat_mean) THEN BEGIN
    IF need_auto THEN BEGIN
      sharp_auto_leading_hale, cp, cn, lat_mean, date_string, $
                               LEADING_SIGN=leading_sign, HALE_SIGN=hale_sign, $
                               EXPECTED_LEADING_SIGN=expected_leading_sign, $
                               CYCLE=cycle, LEADING_SIDE=leading_side
    ENDIF ELSE BEGIN
      expected_leading_sign = sharp_expected_leading_sign(date_string, lat_mean, CYCLE=cycle)
    ENDELSE

    sintilt = sharp_sintilt_1ar(cp, cn, LEADING_SIGN=leading_sign, TILT_DEG=tilt_deg)
    s_bl_core = sharp_bl_source_core_1ar(phi, d, coslat, sintilt, HALE_SIGN=hale_sign)
  ENDIF ELSE BEGIN
    cycle = sharp_cycle_from_date(date_string)
    expected_leading_sign = 0
    leading_sign = 0
    hale_sign = 0
    tilt_deg = !VALUES.D_NAN
    sintilt = !VALUES.D_NAN
    s_bl_core = !VALUES.D_NAN
  ENDELSE

  IF used_bitmap THEN BEGIN
    s_bl_wrap = sharp_bl_source_1ar(br_map, lat_map_deg, pixel_area_cm2, $
                                    BMAP=bitmap, THRESHOLD=threshold, $
                                    MAX_ABS_BR=max_abs_br, BMAP_MIN=bmap_min, $
                                    PIXSCALE_CM=pixscale_cm, $
                                    LEADING_SIGN=leading_sign, HALE_SIGN=hale_sign, $
                                    DATE_STRING=date_string, LEADING_SIDE=leading_side)
  ENDIF ELSE BEGIN
    s_bl_wrap = sharp_bl_source_1ar(br_map, lat_map_deg, pixel_area_cm2, $
                                    THRESHOLD=threshold, MAX_ABS_BR=max_abs_br, $
                                    PIXSCALE_CM=pixscale_cm, $
                                    LEADING_SIGN=leading_sign, HALE_SIGN=hale_sign, $
                                    DATE_STRING=date_string, LEADING_SIDE=leading_side)
  ENDELSE

  PRINT, ' '
  PRINT, '===== TEST SHARP BL SOURCE SINGLE V7 ====='
  PRINT, 'File                   = ', br_file
  PRINT, 'Bitmap file            = ', bitmap_file
  PRINT, 'Used bitmap            = ', used_bitmap
  PRINT, 'Dimensions             = ', nx, ny
  PRINT, 'Threshold [G]          = ', threshold
  PRINT, 'Max |Br| [G]           = ', max_abs_br
  PRINT, 'Bmap min             = ', bmap_min
  PRINT, 'Pixel area [cm^2]      = ', pixel_area_cm2
  PRINT, 'Pixscale [cm/pixel]    = ', pixscale_cm
  PRINT, 'N mask / valid         = ', nmask, nvalid
  PRINT, 'Npix + / -             = ', npos, nneg
  PRINT, 'Phi [Mx]               = ', phi
  PRINT, 'd [cm]                 = ', d
  PRINT, 'lat_mean [deg]         = ', lat_mean
  PRINT, 'cos(lat)               = ', coslat
  PRINT, 'Tilt [deg]             = ', tilt_deg
  PRINT, 'sin(tilt)              = ', sintilt
  PRINT, 'Centroid + [x,y]       = ', cp
  PRINT, 'Centroid - [x,y]       = ', cn
  PRINT, 'Cycle                  = ', cycle
  PRINT, 'Expected leading sign  = ', expected_leading_sign
  PRINT, 'Leading sign           = ', leading_sign
  PRINT, 'Hale sign              = ', hale_sign
  IF N_ELEMENTS(leading_side) GT 0 THEN PRINT, 'Leading side           = ', leading_side ELSE PRINT, 'Leading side           = XMAX default'
  PRINT, 'S_BL core              = ', s_bl_core
  PRINT, 'S_BL wrapper           = ', s_bl_wrap
  PRINT, 'Wrapper-core diff      = ', s_bl_wrap - s_bl_core
  PRINT, '=========================================='
END
