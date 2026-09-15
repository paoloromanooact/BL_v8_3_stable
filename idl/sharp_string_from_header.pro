FUNCTION sharp_string_from_header, hdr, key, DEFAULT=default
  ; Return a header keyword as a trimmed string. Works with read_sdo structs.
  COMPILE_OPT idl2, strictarr

  IF N_ELEMENTS(default) EQ 0 THEN default = ''

  CATCH, err
  IF err NE 0 THEN BEGIN
    CATCH, /CANCEL
    RETURN, STRING(default)
  ENDIF

  val = sharp_header_value(hdr, key, DEFAULT=default, FOUND=found)
  CATCH, /CANCEL

  IF found EQ 0 THEN RETURN, STRING(default)
  RETURN, STRTRIM(STRING(val), 2)
END
