-- Tienda en línea (UCI Online Retail II)
-- Portafolio: https://sites.google.com/view/dcfabianramos

-- ret_concentracion
WITH ordenados AS (
  SELECT cliente_id, monto,
         NTILE(10) OVER (ORDER BY monto DESC) AS decil
  FROM retail_clientes
)
SELECT decil,
       COUNT(*) AS clientes,
       ROUND(SUM(monto), 0) AS monto,
       ROUND(100.0 * SUM(monto) / (SELECT SUM(monto) FROM ordenados), 1) AS pct_ventas
FROM ordenados
GROUP BY decil
ORDER BY decil
;

-- ret_mes
SELECT mes, pedidos, clientes,
       ROUND(monto, 0) AS monto,
       ROUND(AVG(monto) OVER (
         ORDER BY mes ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 0) AS media_movil_3m,
       ROUND(100.0 * (monto - LAG(monto, 12) OVER (ORDER BY mes))
             / LAG(monto, 12) OVER (ORDER BY mes), 1) AS vs_anio_anterior_pct
FROM retail_mes
ORDER BY mes
;

-- ret_devoluciones
SELECT pais, clientes, pedidos,
       ROUND(monto, 0) AS ventas,
       ROUND(100.0 * devoluciones / monto, 1) AS tasa_devolucion_pct
FROM retail_pais
WHERE pedidos >= 50
ORDER BY tasa_devolucion_pct DESC
;

-- ret_productos
SELECT descripcion, unidades,
       ROUND(monto, 0) AS monto,
       RANK() OVER (ORDER BY monto DESC) AS puesto
FROM retail_productos
ORDER BY puesto
LIMIT 10
;

-- ret_clientes
SELECT cliente_id, pais, pedidos,
       ROUND(monto, 0) AS monto,
       primera_compra, ultima_compra,
       ROUND(monto / pedidos, 0) AS ticket_medio
FROM retail_clientes
ORDER BY monto DESC
LIMIT 10
;
