-- Meteoritos (NASA)
-- Portafolio: https://sites.google.com/view/dcfabianramos

-- met
SELECT (anio / 50) * 50 AS periodo,
       COUNT(*) AS caidas
FROM meteoritos
WHERE caida = 'vista' AND anio BETWEEN 1800 AND 2013
GROUP BY periodo
ORDER BY periodo
;

-- met2
SELECT nombre, clase, anio,
       ROUND(masa_g / 1000, 1) AS masa_kg
FROM meteoritos
WHERE caida = 'vista' AND masa_g IS NOT NULL
ORDER BY masa_g DESC
LIMIT 10
;

-- met_hallazgo
SELECT caida,
       COUNT(*) AS meteoritos,
       ROUND(SUM(masa_g) / 1000000.0, 1) AS masa_total_t,
       MIN(anio) AS primer_anio,
       MAX(anio) AS ultimo_anio
FROM meteoritos
GROUP BY caida
;
