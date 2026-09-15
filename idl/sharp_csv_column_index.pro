FUNCTION sharp_csv_column_index, header_fields, name
  COMPILE_OPT idl2, strictarr
  idx = WHERE(STRLOWCASE(header_fields) EQ STRLOWCASE(name), n)
  IF n EQ 0 THEN RETURN, -1L
  RETURN, idx[0]
END
