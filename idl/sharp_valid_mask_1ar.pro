FUNCTION sharp_valid_mask_1ar, br_map, MASK=mask, THRESHOLD=threshold, $
                              MAX_ABS_BR=max_abs_br, NVALID=nvalid
  ; Backward-compatible validity mask without bitmap keywords.
  ; For bitmap support use sharp_build_mask_1ar, br_map, bmap, ...
  COMPILE_OPT idl2, strictarr
  RETURN, sharp_build_mask_1ar(br_map, MASK=mask, THRESHOLD=threshold, $
                               MAX_ABS_BR=max_abs_br, NVALID=nvalid)
END
