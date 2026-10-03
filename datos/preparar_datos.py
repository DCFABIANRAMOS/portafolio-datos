"""
Preparación de datos del portafolio
------------------------------------
Convierte los archivos originales de cada fuente en las tablas resumidas que consume
el laboratorio SQL del portafolio, y las deja en un único archivo JSON.

Los archivos de datos no están en este repositorio: cada uno se descarga de su fuente
oficial. Coloca todos en una carpeta y pásala como argumento.

    descargas/
      10_000_Empresas_mas_Grandes_del_Pais.csv     datos.gov.co (Supersociedades)
      Meteorite_Landings.csv                       data.nasa.gov
      iris.data                                    archive.ics.uci.edu/dataset/53/iris
      online_retail_II.xlsx                        archive.ics.uci.edu/dataset/502
      API_NY.GDP.PCAP.CD_*.csv                     data.worldbank.org (uno por indicador)

Uso:  python preparar_datos.py descargas/ salida.json

Autor: Dumar Fabián Castañeda Ramos
"""

import collections
import csv
import glob
import json
import os
import sys

import pandas as pd


# --------------------------------------------------------------------------- utilidades

def a_numero(texto):
    """'$ 1,234.56' -> 1234.56. El archivo de Supersociedades usa coma de miles."""
    t = texto.replace("$", "").replace(",", "").strip()
    negativo = t.startswith("-")
    t = t.lstrip("-")
    return (-1 if negativo else 1) * float(t) if t else None


def buscar(carpeta, patron):
    encontrados = glob.glob(os.path.join(carpeta, patron))
    return encontrados[0] if encontrados else None


# ------------------------------------------------------------------------ supersociedades

def preparar_supersociedades(ruta):
    """Normaliza en dos tablas (sociedades y financieros) y arma los resúmenes.

    Separar los datos fijos de la empresa de sus cifras anuales evita repetir la razón
    social cinco veces y convierte la consulta en un JOIN por NIT.
    """
    sociedades, financieros = {}, []
    with open(ruta, encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            nit = fila["NIT"].replace(",", "")
            sociedades.setdefault(nit, [
                nit, fila["RAZÓN SOCIAL"].strip(), fila["SUPERVISOR"].strip(),
                fila["MACROSECTOR"].strip(), fila["REGIÓN"].strip(),
                fila["DEPARTAMENTO DOMICILIO"].strip(), fila["CIUDAD DOMICILIO"].strip(),
                int(fila["CIIU"].replace(",", "")),
            ])
            financieros.append([
                nit, int(fila["Año de Corte"].replace(",", "")),
                a_numero(fila["INGRESOS OPERACIONALES"]), a_numero(fila["GANANCIA (PÉRDIDA)"]),
                a_numero(fila["TOTAL ACTIVOS"]), a_numero(fila["TOTAL PASIVOS"]),
                a_numero(fila["TOTAL PATRIMONIO"]),
            ])

    por = {nit: s for nit, s in sociedades.items()}

    def agrupar(indice_sociedad):
        """Suma las cinco cifras por la columna indicada de la tabla de sociedades."""
        acumulado = collections.defaultdict(lambda: [0, 0.0, 0.0, 0.0, 0.0, 0.0])
        for nit, anio, ing, gan, act, pas, pat in financieros:
            clave = (por[nit][indice_sociedad], anio)
            fila = acumulado[clave]
            fila[0] += 1
            for i, valor in enumerate((ing, gan, act, pas, pat)):
                fila[i + 1] += valor
        return [[k[0], k[1], v[0]] + [round(x, 2) for x in v[1:]] for k, v in sorted(acumulado.items())]

    # Los indicadores se calculan sobre las sumas por grupo, nunca empresa por empresa:
    # las cifras vienen redondeadas a dos decimales en billones y en las empresas
    # medianas eso distorsiona cualquier razón financiera.
    return {
        "sociedades": list(sociedades.values()),
        "financieros": financieros,
        "empresas_sector": agrupar(3),
        "empresas_region": agrupar(4),
        "empresas_supervisor": agrupar(2),
    }


# ---------------------------------------------------------------------------- meteoritos

def preparar_meteoritos(ruta):
    filas = []
    with open(ruta, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            try:
                masa = float(r["mass (g)"]) if r["mass (g)"] else None
            except ValueError:
                masa = None
            try:
                anio = int(float(r["year"][:4])) if r["year"] else None
            except ValueError:
                anio = None
            filas.append([
                int(r["id"]), r["name"], r["recclass"], masa, anio,
                float(r["reclat"]) if r["reclat"] else None,
                float(r["reclong"]) if r["reclong"] else None,
                "vista" if r["fall"] == "Fell" else "hallada",
                r["nametype"],
            ])
    return {"meteoritos": filas}


# ---------------------------------------------------------------------------------- iris

def preparar_iris(ruta):
    """Usa bezdekIris.data si está disponible: el propio UCI documenta que las muestras
    35 y 38 del archivo iris.data tienen valores equivocados."""
    corregido = os.path.join(os.path.dirname(ruta), "bezdekIris.data")
    elegido = corregido if os.path.exists(corregido) else ruta
    filas = []
    for linea in open(elegido, encoding="utf-8"):
        p = linea.strip().split(",")
        if len(p) == 5:
            filas.append([float(p[0]), float(p[1]), float(p[2]), float(p[3]), p[4].replace("Iris-", "")])
    return {"iris": filas}


# -------------------------------------------------------------------------- tienda online

def preparar_retail(ruta):
    """Online Retail II: dos hojas de Excel, un millón de transacciones.

    Limpieza: se excluyen las facturas canceladas (empiezan por C), las cantidades y
    precios no positivos. Las devoluciones se guardan aparte porque son información,
    no basura.
    """
    hojas = pd.ExcelFile(ruta)
    df = pd.concat([pd.read_excel(hojas, h) for h in hojas.sheet_names], ignore_index=True)
    df["cancelada"] = df["Invoice"].astype(str).str.startswith("C")
    df["monto"] = df["Quantity"] * df["Price"]
    ventas = df[(~df.cancelada) & (df.Quantity > 0) & (df.Price > 0)].copy()
    devoluciones = df[df.cancelada].copy()
    ventas["mes"] = ventas.InvoiceDate.dt.strftime("%Y-%m")
    devoluciones["mes"] = devoluciones.InvoiceDate.dt.strftime("%Y-%m")

    mes = ventas.groupby("mes").agg(pedidos=("Invoice", "nunique"), lineas=("Invoice", "size"),
                                    clientes=("Customer ID", "nunique"), monto=("monto", "sum"))
    mes["devoluciones"] = -devoluciones.groupby("mes").monto.sum().reindex(mes.index).fillna(0)

    clientes = ventas.dropna(subset=["Customer ID"]).groupby("Customer ID").agg(
        pais=("Country", "first"), pedidos=("Invoice", "nunique"), lineas=("Invoice", "size"),
        monto=("monto", "sum"), primera=("InvoiceDate", "min"), ultima=("InvoiceDate", "max"))

    return {
        "retail_mes": [[m, int(r.pedidos), int(r.lineas), int(r.clientes),
                        round(r.monto, 2), round(r.devoluciones, 2)] for m, r in mes.iterrows()],
        "retail_clientes": [[int(i), r.pais, int(r.pedidos), int(r.lineas), round(r.monto, 2),
                             r.primera.strftime("%Y-%m-%d"), r.ultima.strftime("%Y-%m-%d")]
                            for i, r in clientes.iterrows()],
    }


# -------------------------------------------------------------------------- banco mundial

INDICADORES = {
    "NY.GDP.PCAP.CD": "pib_per_capita",
    "NY.GDP.MKTP.KD.ZG": "crecimiento_pib_pct",
    "FP.CPI.TOTL.ZG": "inflacion_pct",
    "SL.UEM.TOTL.ZS": "desempleo_pct",
    "PA.NUS.FCRF": "tasa_cambio",
    "BX.KLT.DINV.WD.GD.ZS": "ied_pct_pib",
    "GC.TAX.TOTL.GD.ZS": "ingresos_tributarios_pct_pib",
    "GC.XPN.TOTL.GD.ZS": "gasto_publico_pct_pib",
    "GC.DOD.TOTL.GD.ZS": "deuda_pct_pib",
}


def preparar_banco_mundial(carpeta):
    """Cada zip del Banco Mundial trae los años como columnas y cuatro líneas de
    encabezado sueltas antes de la tabla real."""
    datos = collections.defaultdict(dict)
    nombres = {}
    for ruta in glob.glob(os.path.join(carpeta, "API_*.csv")):
        codigo = os.path.basename(ruta).split("_DS2")[0][4:]
        if codigo not in INDICADORES:
            continue
        columna = INDICADORES[codigo]
        filas = list(csv.reader(open(ruta, encoding="utf-8-sig")))
        encabezado = next(f for f in filas if f and f[0] == "Country Name")
        años = {i: int(c) for i, c in enumerate(encabezado) if c.strip().isdigit()}
        for f in filas[filas.index(encabezado) + 1:]:
            if len(f) < 5:
                continue
            nombres[f[1]] = f[0]
            for i, anio in años.items():
                valor = f[i].strip() if i < len(f) else ""
                if valor:
                    datos[(f[1], anio)][columna] = float(valor)

    columnas = list(INDICADORES.values())
    economia = [[c, a] + [round(d[k], 4) if k in d else None for k in columnas]
                for (c, a), d in sorted(datos.items())]
    return {"economia": economia, "paises_mundo": [[c, n] for c, n in sorted(nombres.items())]}


# ---------------------------------------------------------------------------------- main

def main(carpeta, salida):
    tablas = {}
    tareas = [
        ("Supersociedades", "*Empresas*.csv", preparar_supersociedades),
        ("Meteoritos", "Meteorite_Landings.csv", preparar_meteoritos),
        ("Iris", "iris.data", preparar_iris),
        ("Online Retail II", "online_retail_II.xlsx", preparar_retail),
    ]
    for nombre, patron, funcion in tareas:
        ruta = buscar(carpeta, patron)
        if not ruta:
            print(f"  falta {nombre} ({patron}), se omite")
            continue
        tablas.update(funcion(ruta))
        print(f"  {nombre}: listo")

    if glob.glob(os.path.join(carpeta, "API_*.csv")):
        tablas.update(preparar_banco_mundial(carpeta))
        print("  Banco Mundial: listo")

    with open(salida, "w", encoding="utf-8") as f:
        json.dump(tablas, f, ensure_ascii=False, separators=(",", ":"))

    print("\nTablas generadas:")
    for nombre, filas in tablas.items():
        print(f"  {nombre:24} {len(filas):>8,} filas")
    print(f"\nArchivo: {salida} ({os.path.getsize(salida) / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("Uso: python preparar_datos.py carpeta_descargas/ salida.json")
    main(sys.argv[1], sys.argv[2])
