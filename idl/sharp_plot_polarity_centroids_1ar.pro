PRO sharp_plot_polarity_centroids_1ar, br_map, pos_centroid, neg_centroid, $
                                       MASK=mask, TITLE=title, $
                                       RANGE=range, COLORBAR=colorbar

  COMPILE_OPT idl2, strictarr

  sz = SIZE(br_map, /DIMENSIONS)
  IF N_ELEMENTS(sz) NE 2 THEN MESSAGE, 'br_map deve essere un array 2D'

  IF N_ELEMENTS(pos_centroid) NE 2 THEN MESSAGE, 'pos_centroid deve avere 2 elementi'
  IF N_ELEMENTS(neg_centroid) NE 2 THEN MESSAGE, 'neg_centroid deve avere 2 elementi'

  IF N_ELEMENTS(title) EQ 0 THEN title = 'SHARP Br: polarity centroids'

  ; Range simmetrico per visualizzazione
  IF N_ELEMENTS(range) EQ 0 THEN BEGIN
    maxabs = MAX(ABS(br_map), /NAN)
  ENDIF ELSE BEGIN
    maxabs = DOUBLE(range)
  ENDELSE

  img = BYTSCL(br_map, MIN=-maxabs, MAX=maxabs, TOP=254)

  WINDOW, /FREE, XSIZE=900, YSIZE=700, TITLE=title

  ; Mostra magnetogramma
  TVSCL, img

  ; Sovrapponi maschera, se presente
  IF N_ELEMENTS(mask) GT 0 THEN BEGIN
    CONTOUR, mask, /OVERPLOT, LEVELS=[0.5], C_THICK=2,/DEV
  ENDIF
loadct,1

  ; Baricentro positivo
  PLOTS, pos_centroid[0], pos_centroid[1], PSYM=4, SYMSIZE=2.5, THICK=3., /DEV, color=150

loadct,3
  ; Baricentro negativo
  PLOTS, neg_centroid[0], neg_centroid[1], PSYM=4, SYMSIZE=2.5, THICK=3., /DEV, color=150

loadct,0
  ; Segmento tra i due centroidi
  PLOTS, [pos_centroid[0], neg_centroid[0]], $
         [pos_centroid[1], neg_centroid[1]], THICK=3,/DEV

  ; Etichette
  XYOUTS, pos_centroid[0] + 5, pos_centroid[1] + 5, 'B+', CHARSIZE=1.5, /DEV
  XYOUTS, neg_centroid[0] + 5, neg_centroid[1] + 5, 'B-', CHARSIZE=1.5, /DEV


END
