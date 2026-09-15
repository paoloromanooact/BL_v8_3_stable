FUNCTION sharp_find_bitmap_file, br_file, BITMAP_DIR=bitmap_dir
  ; Return matching SHARP bitmap filename for a Br filename, or '' if not found.
  COMPILE_OPT idl2, strictarr

  IF N_ELEMENTS(br_file) EQ 0 THEN RETURN, ''

  base = FILE_BASENAME(br_file)
  dir = FILE_DIRNAME(br_file)
  IF N_ELEMENTS(bitmap_dir) GT 0 THEN dir = bitmap_dir

  candidates = STRARR(4)
  candidates[0] = STRJOIN(STRSPLIT(base, '.Br.fits', /EXTRACT), '.bitmap.fits')
  candidates[1] = STRJOIN(STRSPLIT(base, '.Br.fits.gz', /EXTRACT), '.bitmap.fits.gz')
  candidates[2] = STRJOIN(STRSPLIT(base, '.Br.', /EXTRACT), '.bitmap.')
  candidates[3] = STRJOIN(STRSPLIT(base, 'Br', /EXTRACT), 'bitmap')

  FOR i=0, N_ELEMENTS(candidates)-1 DO BEGIN
    f = FILEPATH(candidates[i], ROOT_DIR=dir)
    found = FILE_SEARCH(f, COUNT=nfound)
    IF nfound GT 0 THEN RETURN, found[0]
  ENDFOR

  ; More flexible fallback: same HARP/date prefix, bitmap suffix.
  prefix = base
  p = STRPOS(prefix, '.Br.fits')
  IF p GE 0 THEN prefix = STRMID(prefix, 0, p)
  p = STRPOS(prefix, '.Br')
  IF p GE 0 THEN prefix = STRMID(prefix, 0, p)
  found = FILE_SEARCH(FILEPATH(prefix + '*.bitmap.fits*', ROOT_DIR=dir), COUNT=nfound)
  IF nfound GT 0 THEN RETURN, found[0]

  RETURN, ''
END
