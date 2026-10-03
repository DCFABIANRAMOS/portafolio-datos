-- Modelo de riesgo de deterioro
-- Portafolio: https://sites.google.com/view/dcfabianramos

-- rie_deciles
SELECT decil, empresas, casos,
       tasa_deterioro_pct,
       lift AS veces_sobre_el_promedio,
       SUM(casos) OVER (ORDER BY decil) AS casos_acumulados,
       ROUND(100.0 * SUM(casos) OVER (ORDER BY decil)
             / (SELECT SUM(casos) FROM riesgo_deciles), 1) AS pct_capturado
FROM riesgo_deciles
ORDER BY decil
;

-- rie_modelos
SELECT modelo, auc, lift_top5
FROM riesgo_modelos
ORDER BY auc DESC
;

-- rie_perfil
SELECT variable, grupo, desde, hasta, empresas, tasa_deterioro_pct
FROM riesgo_perfil
WHERE variable = 'Endeudamiento' OR variable = 'Macrosector'
ORDER BY variable, tasa_deterioro_pct DESC
;

-- rie_casos
SELECT empresa, macrosector, anio_base, anio_evento,
       ingresos AS ingresos_bn, margen_pct, endeudamiento_pct
FROM riesgo_casos
ORDER BY ingresos DESC
LIMIT 15
;
