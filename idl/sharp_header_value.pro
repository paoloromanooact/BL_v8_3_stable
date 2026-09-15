FUNCTION sharp_header_value, hdr, key, DEFAULT=default, FOUND=found
  ;+
  ; NAME:
  ;   sharp_header_value
  ;
  ; PURPOSE:
  ;   Return a header keyword value from either:
  ;     1) a SolarSoft/read_sdo header STRUCTURE, or
  ;     2) a standard FITS header string array usable by SXPAR.
  ;
  ; INPUTS:
  ;   hdr : IDL structure from read_sdo, or FITS header string array
  ;   key : keyword name, e.g. 'CRVAL2'
  ;
  ; KEYWORDS:
  ;   DEFAULT : value returned if keyword is absent
  ;   FOUND   : output byte, 1 if keyword found, 0 otherwise
  ;-
  COMPILE_OPT idl2, strictarr

  found = 0B
  ukey = STRUPCASE(STRTRIM(key, 2))

  ;------------------------------------------------------------
  ; Case 1: read_sdo / SSW header structure.
  ; IDL structure tags are accessed through their tag index.
  ;------------------------------------------------------------
  IF SIZE(hdr, /TYPE) EQ 8 THEN BEGIN
    tags = TAG_NAMES(hdr)
    itag = WHERE(STRUPCASE(tags) EQ ukey, ntag)
    IF ntag GT 0 THEN BEGIN
      found = 1B
      RETURN, hdr.(itag[0])
    ENDIF
  ENDIF

  ;------------------------------------------------------------
  ; Case 2: FITS header string array. Prefer SXPAR if available.
  ;------------------------------------------------------------
  CATCH, err
  IF err EQ 0 THEN BEGIN
    value = SXPAR(hdr, ukey, COUNT=count)
    IF count GT 0 THEN BEGIN
      CATCH, /CANCEL
      found = 1B
      RETURN, value
    ENDIF
  ENDIF
  CATCH, /CANCEL

  IF N_ELEMENTS(default) GT 0 THEN RETURN, default
  MESSAGE, 'Keyword not found in header: ' + ukey
END
