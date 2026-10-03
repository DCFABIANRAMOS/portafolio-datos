# Portafolio de análisis de datos

Dumar Fabián Castañeda Ramos

Contador público, especialista en Visual Analytics y Big Data. Aquí está el código detrás
de mi portafolio: las consultas SQL de cada proyecto y el script del modelo predictivo.

**Portafolio en línea:** https://sites.google.com/view/dcfabianramos  
**LinkedIn:** https://www.linkedin.com/in/dcfabianramos  
**GitHub:** https://github.com/dcfabianramos

## Proyectos

| Proyecto | Pregunta | Técnicas |
|---|---|---|
| Empresas de Colombia | ¿Qué sectores ganan más por cada peso que venden? | Agregación, `LAG`, `RANK`, CTE |
| Riesgo de deterioro | ¿Se puede ver venir el deterioro un año antes? | Regresión logística, bosque aleatorio, validación temporal |
| Economía mundial | ¿Dónde está Colombia frente a sus pares? | `JOIN`, `RANK`, `LAG` |
| Tienda en línea | ¿De quién depende de verdad el negocio? | `NTILE`, media móvil, limpieza |
| Meteoritos | ¿Cuándo se vieron caer más meteoritos? | Filtrado, agrupación por periodo |
| Iris | ¿Qué tan separables son las especies? | Estadística descriptiva por grupo |

## Contenido

- `consultas/`: las consultas SQL de cada proyecto, en SQLite. Son las mismas que se
  ejecutan en el laboratorio del portafolio.
- `modelo/analisis_riesgo.ipynb`: el cuaderno con la exploración paso a paso, los gráficos
  y las conclusiones. Es el mejor punto de entrada al proyecto, porque GitHub lo muestra ya
  ejecutado y no hay que correr nada.
- `modelo/riesgo_deterioro.py`: el mismo análisis como script, reproducible desde el CSV original.
- `datos/preparar_datos.py`: convierte los archivos originales de las cinco fuentes en las
  tablas que consume el laboratorio SQL del portafolio.
- `requirements.txt`: las librerías necesarias.
- `portafolio/`: la página completa en un solo archivo HTML, en dos versiones: `portafolio-completa.html` y `portafolio-ligera.html`.

## Fuentes de datos

Ninguna está incluida en este repositorio: se descargan de su sitio oficial.

| Fuente | Dataset | Dónde |
|---|---|---|
| Superintendencia de Sociedades | 10.000 Empresas más Grandes del País (50.000 registros, 2021-2025) | [datos.gov.co](https://www.datos.gov.co/Comercio-Industria-y-Turismo/10-000-Empresas-mas-Grandes-del-Pa-s/6cat-2gcs) |
| Banco Mundial | World Development Indicators (9 indicadores, 265 países, desde 1960) | [data.worldbank.org](https://data.worldbank.org/) |
| UCI | Online Retail II (1.067.371 transacciones) e Iris | [archive.ics.uci.edu](https://archive.ics.uci.edu/) |
| NASA | Meteorite Landings (45.716 registros) | [data.nasa.gov](https://data.nasa.gov/dataset/meteorite-landings) |

## Cómo correr el modelo

```bash
pip install pandas numpy scikit-learn
python modelo/riesgo_deterioro.py ruta/al/archivo_supersociedades.csv
```

Imprime el desempeño de cada variante del modelo, la tabla de riesgo por décimos y la
comprobación del artefacto de redondeo que explica buena parte del resultado.

## Resultado del modelo, en corto

El modelo completo alcanza un AUC de 0,777, pero al quitar la variable de tamaño cae a
0,660, y entre empresas de tamaño comparable queda en 0,667. La razón: las cifras vienen
redondeadas a dos decimales en billones de pesos, y el 90 % de las empresas más pequeñas
tiene una ganancia que redondea a 0,00, así que casi nunca registra un valor negativo. El
modelo aprendió ese artefacto de medición antes que la salud financiera.

Sirve para priorizar revisiones, no para decidir: el décimo más riesgoso concentra 3,5
veces más casos que el promedio. Faltan activos y pasivos corrientes, así que no hay
razón corriente ni prueba ácida, que son las variables clásicas de estos modelos.
