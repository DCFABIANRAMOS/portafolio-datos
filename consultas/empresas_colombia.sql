-- Empresas de Colombia (Supersociedades)
-- Portafolio: https://sites.google.com/view/dcfabianramos

-- emp
SELECT macrosector,
       ROUND(SUM(ingresos), 1) AS ingresos_bn,
       ROUND(100.0 * SUM(ganancia) / SUM(ingresos), 1) AS margen_pct,
       ROUND(100.0 * SUM(pasivos) / SUM(activos), 1) AS endeudamiento_pct,
       ROUND(100.0 * SUM(ganancia) / SUM(activos), 1) AS roa_pct,
       ROUND(100.0 * SUM(ganancia) / SUM(patrimonio), 1) AS roe_pct
FROM empresas_sector
WHERE anio = 2025
GROUP BY macrosector
ORDER BY margen_pct DESC
;

-- emp_ciiu
SELECT ciiu, macrosector, empresas,
       ROUND(ingresos, 1) AS ingresos_bn,
       ROUND(100.0 * ganancia / ingresos, 1) AS margen_pct,
       empresa_ejemplo
FROM actividades
WHERE anio = 2025 AND empresas >= 10
ORDER BY margen_pct DESC
LIMIT 10
;

-- emp_minero
SELECT anio,
       ROUND(ingresos, 1) AS ingresos_bn,
       ROUND(100.0 * ganancia / ingresos, 1) AS margen_pct,
       ROUND(100.0 * ganancia / ingresos
             - LAG(100.0 * ganancia / ingresos) OVER (ORDER BY anio), 1) AS cambio_pp
FROM empresas_sector
WHERE macrosector = 'MINERO'
ORDER BY anio
;

-- emp_region
SELECT region, empresas,
       ROUND(ingresos, 1) AS ingresos_bn,
       ROUND(100.0 * ganancia / ingresos, 1) AS margen_pct,
       ROUND(100.0 * pasivos / activos, 1) AS endeudamiento_pct,
       RANK() OVER (ORDER BY 100.0 * ganancia / ingresos DESC) AS puesto
FROM empresas_region
WHERE anio = 2025
ORDER BY puesto
;

-- emp_top
SELECT nombre, macrosector,
       ROUND(ingresos, 2) AS ingresos_bn,
       ROUND(100.0 * ganancia / ingresos, 1) AS margen_pct,
       ROUND(100.0 * pasivos / activos, 1) AS endeudamiento_pct
FROM empresas_top
WHERE anio = 2025 AND ingresos >= 2
ORDER BY margen_pct DESC
LIMIT 10
;

-- emp_perdidas
SELECT anio,
       COUNT(*) AS empresas,
       SUM(CASE WHEN ganancia < 0 THEN 1 ELSE 0 END) AS con_perdida,
       ROUND(100.0 * SUM(CASE WHEN ganancia < 0 THEN 1 ELSE 0 END)
             / COUNT(*), 1) AS pct_con_perdida
FROM financieros
GROUP BY anio
ORDER BY anio
;

-- emp_mediana
WITH ordenado AS (
  SELECT s.macrosector, f.ingresos,
         ROW_NUMBER() OVER (PARTITION BY s.macrosector ORDER BY f.ingresos) AS pos,
         COUNT(*) OVER (PARTITION BY s.macrosector) AS n
  FROM financieros f
  JOIN sociedades s ON s.nit = f.nit
  WHERE f.anio = 2025
)
SELECT macrosector, n AS empresas,
       ROUND(ingresos, 2) AS ingresos_mediana_bn
FROM ordenado
WHERE pos = (n + 1) / 2
ORDER BY ingresos_mediana_bn DESC
;

-- emp_buscar
SELECT s.nombre, s.ciudad, f.anio,
       f.ingresos, f.ganancia,
       ROUND(100.0 * f.ganancia / f.ingresos, 1) AS margen_pct
FROM financieros f
JOIN sociedades s ON s.nit = f.nit
WHERE s.nombre LIKE '%ECOPETROL%'
ORDER BY f.anio
;

-- emp_supervisor
SELECT s.supervisor,
       COUNT(*) AS empresas,
       ROUND(SUM(f.ingresos), 1) AS ingresos_bn,
       ROUND(100.0 * SUM(f.ganancia) / SUM(f.ingresos), 1) AS margen_pct,
       ROUND(100.0 * SUM(f.pasivos) / SUM(f.activos), 1) AS endeudamiento_pct
FROM financieros f
JOIN sociedades s ON s.nit = f.nit
WHERE f.anio = 2025
GROUP BY s.supervisor
ORDER BY ingresos_bn DESC
;
