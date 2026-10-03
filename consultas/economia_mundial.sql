-- Economía mundial (Banco Mundial)
-- Portafolio: https://sites.google.com/view/dcfabianramos

-- pib
SELECT p.pais,
       a.pib_per_capita AS pib_2021,
       b.pib_per_capita AS pib_2025,
       ROUND((b.pib_per_capita - a.pib_per_capita)
             / a.pib_per_capita * 100, 1) AS crecimiento_pct
FROM paises_mundo p
JOIN economia a ON a.codigo = p.codigo AND a.anio = 2021
JOIN economia b ON b.codigo = p.codigo AND b.anio = 2025
WHERE p.codigo IN ('COL', 'PER', 'BRA', 'MEX')
ORDER BY crecimiento_pct DESC
;

-- mundo_rank
WITH ranking AS (
  SELECT e.codigo, e.pib_per_capita,
         RANK() OVER (ORDER BY e.pib_per_capita DESC) AS puesto,
         COUNT(*) OVER () AS paises
  FROM economia e
  JOIN paises_mundo p ON p.codigo = e.codigo AND p.es_pais = 1
  WHERE e.anio = 2024 AND e.pib_per_capita IS NOT NULL
)
SELECT p.pais, p.grupo_ingreso,
       ROUND(r.pib_per_capita, 0) AS pib_pc_usd,
       r.puesto, r.paises
FROM ranking r
JOIN paises_mundo p ON p.codigo = r.codigo
WHERE r.puesto <= 5 OR r.codigo IN ('COL','PER','BRA','MEX','CHL','ARG')
ORDER BY r.puesto
;

-- mundo_pares
SELECT p.pais,
       ROUND(e.pib_per_capita, 0) AS pib_pc_usd,
       e.inflacion_pct, e.desempleo_pct,
       e.ied_pct_pib, e.deuda_pct_pib
FROM economia e
JOIN paises_mundo p ON p.codigo = e.codigo
WHERE e.anio = 2024
  AND p.region = 'Latin America & Caribbean'
  AND p.grupo_ingreso = 'Upper middle income'
ORDER BY pib_pc_usd DESC
;

-- mundo_fiscal
SELECT p.pais, p.grupo_ingreso,
       e.ingresos_tributarios_pct_pib AS tributos_pct_pib,
       e.deuda_pct_pib,
       ROUND(e.deuda_pct_pib / e.ingresos_tributarios_pct_pib, 1) AS deuda_sobre_tributos
FROM economia e
JOIN paises_mundo p ON p.codigo = e.codigo AND p.es_pais = 1
WHERE e.anio = 2023
  AND e.ingresos_tributarios_pct_pib IS NOT NULL
  AND e.deuda_pct_pib IS NOT NULL
ORDER BY deuda_sobre_tributos DESC
;

-- mundo_colombia
SELECT anio,
       ROUND(pib_per_capita, 0) AS pib_pc_usd,
       crecimiento_pib_pct, inflacion_pct, desempleo_pct,
       ROUND(tasa_cambio, 0) AS pesos_por_dolar,
       ingresos_tributarios_pct_pib, deuda_pct_pib,
       ROUND(100.0 * (pib_per_capita - LAG(pib_per_capita) OVER (ORDER BY anio))
             / LAG(pib_per_capita) OVER (ORDER BY anio), 1) AS variacion_pib_pc_pct
FROM economia
WHERE codigo = 'COL' AND anio >= 2000
ORDER BY anio
;

-- mundo_inflacion
SELECT p.pais, p.region,
       e.inflacion_pct,
       ROUND(e.pib_per_capita, 0) AS pib_pc_usd
FROM economia e
JOIN paises_mundo p ON p.codigo = e.codigo AND p.es_pais = 1
WHERE e.anio = 2024 AND e.inflacion_pct IS NOT NULL
ORDER BY e.inflacion_pct DESC
LIMIT 10
;

-- indicadores
SELECT columna, nombre, fuente, definicion
FROM indicadores
ORDER BY columna
;
