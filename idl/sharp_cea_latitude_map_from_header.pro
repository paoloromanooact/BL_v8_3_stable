FUNCTION sharp_cea_latitude_map_from_header, hdr, NX=nx, NY=ny, SINLAT_MAP=sinlat_map
  ;+
  ; NAME:
  ;   sharp_cea_latitude_map_from_header
  ;
  ; PURPOSE:
  ;   Build heliographic latitude map [deg] for an HMI SHARP CEA image.
  ;   Compatible with both standard FITS headers and read_sdo header structs.
  ;
  ; CEA FORMULA:
  ;   sin(lat_j) = sin(CRVAL2) + (j_1based - CRPIX2) * CDELT2 * pi/180
  ;   lat_j      = asin(sin(lat_j))
  ;
  ; INPUT:
  ;   hdr : FITS header string array or read_sdo structure.
  ;
  ; KEYWORDS:
  ;   NX, NY      : optional dimensions. If absent, uses NAXIS1/NAXIS2,
  ;                 falling back to ZNAXIS1/ZNAXIS2.
  ;   SINLAT_MAP  : returned 2D map of sin(latitude).
  ;
  ; OUTPUT:
  ;   2D latitude map [deg].
  ;-
  COMPILE_OPT idl2, strictarr

  IF N_ELEMENTS(nx) EQ 0 THEN BEGIN
    nxv = sharp_header_value(hdr, 'NAXIS1', FOUND=f1)
    IF ~f1 THEN nxv = sharp_header_value(hdr, 'ZNAXIS1')
    nx = LONG(nxv)
  ENDIF

  IF N_ELEMENTS(ny) EQ 0 THEN BEGIN
    nyv = sharp_header_value(hdr, 'NAXIS2', FOUND=f2)
    IF ~f2 THEN nyv = sharp_header_value(hdr, 'ZNAXIS2')
    ny = LONG(nyv)
  ENDIF

  crpix2 = DOUBLE(sharp_header_value(hdr, 'CRPIX2'))
  crval2 = DOUBLE(sharp_header_value(hdr, 'CRVAL2'))
  cdelt2 = DOUBLE(sharp_header_value(hdr, 'CDELT2'))

  j = DINDGEN(ny) + 1D
  sinlat_1d = SIN(crval2 * !DPI / 180D) + (j - crpix2) * cdelt2 * !DPI / 180D

  ; Numerical safety.
  sinlat_1d = sinlat_1d > (-1D)
  sinlat_1d = sinlat_1d < ( 1D)

  lat_1d = ASIN(sinlat_1d) * 180D / !DPI

  lat_map = REBIN(REFORM(lat_1d, 1, ny), nx, ny)
  sinlat_map = REBIN(REFORM(sinlat_1d, 1, ny), nx, ny)

  RETURN, lat_map
END
