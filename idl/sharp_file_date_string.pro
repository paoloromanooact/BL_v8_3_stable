FUNCTION sharp_file_date_string, filename, HDR=hdr
  ; Return a date-like string usable by sharp_cycle_from_date.
  ; Prefer T_REC from header; fallback to filename digits.
  COMPILE_OPT idl2, strictarr

  IF N_ELEMENTS(hdr) GT 0 THEN BEGIN
    trec = sharp_string_from_header(hdr, 'T_REC', DEFAULT='')
    IF STRLEN(trec) GT 0 THEN RETURN, trec
  ENDIF

  RETURN, filename
END
