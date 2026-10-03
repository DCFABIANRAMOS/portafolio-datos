-- Iris (UCI)
-- Portafolio: https://sites.google.com/view/dcfabianramos

-- iris
SELECT especie,
       ROUND(AVG(largo_petalo), 2) AS largo_prom,
       ROUND(AVG(ancho_petalo), 2) AS ancho_prom,
       COUNT(*) AS flores
FROM iris
GROUP BY especie
ORDER BY largo_prom
;
