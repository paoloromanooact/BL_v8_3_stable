FUNCTION sharp_cea_pixel_area_from_header, hdr, PIXSCALE_CM=pixscale_cm
  ;+
  ; NAME:
  ;   sharp_cea_pixel_area_from_header
  ;
  ; PURPOSE:
  ;   Estimate constant CEA pixel area [cm^2] from SHARP header CDELT1/CDELT2.
  ;   Compatible with both standard FITS headers and read_sdo header structs.
  ;
  ; NOTES:
  ;   SHARP CEA maps use cylindrical equal-area coordinates. For a first
  ;   BL-source proxy, the pixel area can be treated as constant:
  ;     A_pix = R_sun^2 * dphi * dmu
  ;   where dphi = CDELT1*pi/180 and dmu = CDELT2*pi/180.
  ;   This assumes CDELT1 and CDELT2 are in degrees.
  ;-
  COMPILE_OPT idl2, strictarr

  rsun_cm = 6.957D10

  cdelt1 = ABS(DOUBLE(sharp_header_value(hdr, 'CDELT1')))
  cdelt2 = ABS(DOUBLE(sharp_header_value(hdr, 'CDELT2')))

  dphi = cdelt1 * !DPI / 180D
  dmu  = cdelt2 * !DPI / 180D

  pixscale_cm = rsun_cm * SQRT(dphi * dmu)
  RETURN, rsun_cm^2 * dphi * dmu
END
