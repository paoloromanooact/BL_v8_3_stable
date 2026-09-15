FUNCTION sharp_build_mask_1ar, br_map, bmap, MASK=mask, $
                              THRESHOLD=threshold, MAX_ABS_BR=max_abs_br, $
                              BMAP_MIN=bmap_min, NVALID=nvalid
  ;+
  ; NAME:
  ;   sharp_build_mask_1ar
  ;
  ; PURPOSE:
  ;   Build a common analysis mask for one SHARP CEA Br map.
  ;   The SHARP bitmap is passed as a positional argument to avoid
  ;   IDL keyword ambiguity with BITMAP / BITMAP_MIN.
  ;
  ; INPUTS:
  ;   br_map : 2D Br map [G]
  ;   bmap   : optional positional 2D bitmap map. Pass it as the second
  ;            argument when available. If omitted, only Br validity and MASK
  ;            are used.
  ;
  ; KEYWORDS:
  ;   MASK       : optional external mask, same dimensions as br_map
  ;   THRESHOLD  : optional |Br| threshold [G]. If >0, keeps |Br| >= THRESHOLD
  ;   MAX_ABS_BR : optional maximum allowed |Br| [G]. Suggested: 10000D
  ;   BMAP_MIN   : if bmap is supplied, keeps bmap >= BMAP_MIN. Default = 1D
  ;   NVALID     : output number of selected pixels
  ;-
  COMPILE_OPT idl2, strictarr

  sz = SIZE(br_map, /DIMENSIONS)
  IF N_ELEMENTS(sz) NE 2 THEN MESSAGE, 'br_map must be a 2D array'

  use_mask = BYTE(FINITE(br_map))

  IF N_ELEMENTS(max_abs_br) GT 0 THEN BEGIN
    IF DOUBLE(max_abs_br) GT 0D THEN $
      use_mask = use_mask AND BYTE(ABS(br_map) LE DOUBLE(max_abs_br))
  ENDIF

  IF N_ELEMENTS(mask) GT 0 THEN BEGIN
    IF TOTAL(ABS(SIZE(mask, /DIMENSIONS)-sz)) NE 0 THEN MESSAGE, 'MASK dimension mismatch'
    use_mask = use_mask AND BYTE(mask NE 0)
  ENDIF

  IF N_ELEMENTS(bmap) GT 0 THEN BEGIN
    IF TOTAL(ABS(SIZE(bmap, /DIMENSIONS)-sz)) NE 0 THEN MESSAGE, 'bmap dimension mismatch'
    IF N_ELEMENTS(bmap_min) EQ 0 THEN bmap_min = 1D
    use_mask = use_mask AND BYTE(FINITE(bmap)) AND BYTE(bmap GE DOUBLE(bmap_min))
  ENDIF

  IF N_ELEMENTS(threshold) GT 0 THEN BEGIN
    IF DOUBLE(threshold) GT 0D THEN $
      use_mask = use_mask AND BYTE(ABS(br_map) GE DOUBLE(threshold))
  ENDIF

  idx = WHERE(use_mask NE 0, nvalid)
  RETURN, use_mask
END
