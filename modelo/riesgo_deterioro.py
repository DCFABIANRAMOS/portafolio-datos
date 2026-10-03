"""
Predicción de deterioro financiero en empresas colombianas
----------------------------------------------------------
Fuente: Superintendencia de Sociedades, "10.000 Empresas más Grandes del País"
        https://www.datos.gov.co/Comercio-Industria-y-Turismo/10-000-Empresas-mas-Grandes-del-Pa-s/6cat-2gcs
        Cortes 2021 a 2025. Cifras en billones de pesos, redondeadas a dos decimales.

Qué predice: que una empresa sana en el año t reporte pérdida o patrimonio negativo en t+1.
             No es quiebra jurídica; es una señal contable de alarma (el patrimonio negativo
             es causal de disolución en Colombia).

Uso:  python riesgo_deterioro.py ruta/al/archivo.csv

Autor: Dumar Fabián Castañeda Ramos
"""

import sys
import csv
import collections

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NUMERICAS = ["margen", "endeud", "roa", "roe", "rot_act", "var_ing", "anios_lista", "log_tam"]
CATEGORICAS = ["macro", "region"]


def a_numero(texto):
    """Convierte '$ 1,234.56' a float. El archivo usa coma como separador de miles."""
    t = texto.replace("$", "").replace(",", "").strip()
    negativo = t.startswith("-")
    t = t.lstrip("-")
    return (-1 if negativo else 1) * float(t) if t else None


def cargar(ruta):
    """Lee el CSV y lo organiza como {nit: {anio: cifras}}."""
    panel = collections.defaultdict(dict)
    info = {}
    with open(ruta, encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            nit = fila["NIT"].replace(",", "")
            anio = int(fila["Año de Corte"].replace(",", ""))
            panel[nit][anio] = dict(
                ing=a_numero(fila["INGRESOS OPERACIONALES"]),
                gan=a_numero(fila["GANANCIA (PÉRDIDA)"]),
                act=a_numero(fila["TOTAL ACTIVOS"]),
                pas=a_numero(fila["TOTAL PASIVOS"]),
                pat=a_numero(fila["TOTAL PATRIMONIO"]),
            )
            info[nit] = dict(macro=fila["MACROSECTOR"].strip(), region=fila["REGIÓN"].strip())
    return panel, info


def construir_pares(panel, info):
    """Un registro por empresa y año, con los indicadores de t y el desenlace en t+1.

    Solo entran empresas sanas en t (con utilidad y patrimonio positivos): predecir el
    deterioro de una que ya está mal no tiene valor práctico.
    """
    filas = []
    for nit, años in panel.items():
        orden = sorted(años)
        for y in orden:
            if y + 1 not in años:
                continue
            a, b = años[y], años[y + 1]
            if a["gan"] < 0 or a["pat"] <= 0 or a["ing"] <= 0 or a["act"] <= 0:
                continue
            previo = años.get(y - 1)
            filas.append(dict(
                nit=nit, anio=y,
                margen=a["gan"] / a["ing"],
                endeud=a["pas"] / a["act"],
                roa=a["gan"] / a["act"],
                roe=a["gan"] / a["pat"],
                rot_act=a["ing"] / a["act"],
                var_ing=(a["ing"] - previo["ing"]) / previo["ing"] if previo and previo["ing"] > 0 else 0.0,
                tam=a["ing"],
                anios_lista=sum(1 for z in orden if z <= y),
                macro=info[nit]["macro"], region=info[nit]["region"],
                objetivo=1 if (b["gan"] < 0 or b["pat"] < 0) else 0,
            ))
    df = pd.DataFrame(filas)
    df["log_tam"] = np.log10(df["tam"].clip(lower=0.01))
    return df


def evaluar(df, etiqueta, sin_tamanio=False):
    """Entrena con 2021-2022 y evalúa con 2023-2024.

    La separación es temporal, no aleatoria: con una partición al azar el modelo vería
    el futuro de la misma empresa y el resultado saldría inflado.
    """
    numericas = [c for c in NUMERICAS if not (sin_tamanio and c == "log_tam")]
    entreno = df[df.anio <= 2022]
    prueba = df[df.anio >= 2023]

    preparacion = ColumnTransformer([
        ("num", StandardScaler(), numericas),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAS),
    ])

    resultados = {}
    for nombre, algoritmo in [
        ("logistica", LogisticRegression(max_iter=2000, class_weight="balanced")),
        ("bosque", RandomForestClassifier(n_estimators=400, min_samples_leaf=20,
                                          class_weight="balanced", random_state=0, n_jobs=-1)),
    ]:
        modelo = make_pipeline(preparacion, algoritmo).fit(entreno[numericas + CATEGORICAS], entreno.objetivo)
        puntaje = modelo.predict_proba(prueba[numericas + CATEGORICAS])[:, 1]
        resultados[nombre] = (roc_auc_score(prueba.objetivo, puntaje), puntaje, modelo)

    # La exactitud no sirve con un 3 % de positivos: diciendo "nadie se deteriora" se acierta
    # el 97 %. Por eso se mide con AUC y con cuántos casos captura el 5 % más riesgoso.
    puntaje = resultados["logistica"][1]
    corte = int(len(prueba) * 0.05)
    peores = np.argsort(-puntaje)[:corte]
    lift = prueba.objetivo.values[peores].mean() / prueba.objetivo.mean()

    print(f"{etiqueta:38} AUC logística {resultados['logistica'][0]:.3f} | "
          f"AUC bosque {resultados['bosque'][0]:.3f} | lift 5% {lift:.1f}x")
    return resultados


def tabla_deciles(df, resultados):
    prueba = df[df.anio >= 2023].copy()
    prueba["prob"] = resultados["logistica"][1]
    prueba["decil"] = pd.qcut(prueba.prob, 10, labels=range(10, 0, -1)).astype(int)
    tabla = prueba.groupby("decil").agg(
        empresas=("objetivo", "size"), casos=("objetivo", "sum"), tasa=("objetivo", "mean")
    ).sort_index()
    tabla["tasa"] = (tabla["tasa"] * 100).round(2)
    tabla["lift"] = (tabla["tasa"] / (prueba.objetivo.mean() * 100)).round(2)
    return tabla


def main(ruta):
    panel, info = cargar(ruta)
    df = construir_pares(panel, info)
    print(f"Pares año a año: {len(df):,} | casos de deterioro: {df.objetivo.sum():,} "
          f"({df.objetivo.mean() * 100:.1f} %)\n")

    resultados = evaluar(df, "todas las variables")
    evaluar(df, "sin la variable de tamaño", sin_tamanio=True)
    grandes = df[df.tam >= 0.12]
    evaluar(grandes, "solo empresas de tamaño comparable")

    print("\nReferencia: reglas de pulgar de un solo indicador")
    prueba = df[df.anio >= 2023]
    print(f"  endeudamiento alto  AUC {roc_auc_score(prueba.objetivo, prueba.endeud):.3f}")
    print(f"  margen bajo         AUC {roc_auc_score(prueba.objetivo, -prueba.margen):.3f}")

    print("\nTasa de deterioro por décimo de riesgo (1 = más riesgoso)")
    print(tabla_deciles(df, resultados).to_string())

    # Por qué el tamaño engaña: con cifras redondeadas a dos decimales en billones, las
    # empresas pequeñas casi nunca pueden mostrar un valor negativo. El modelo aprende ese
    # artefacto de medición y no una verdad económica.
    df["gan_abs"] = (df.margen * df.tam).abs()
    cuartil = pd.qcut(df.tam, 4)
    print("\nPorcentaje de empresas cuya ganancia redondea a 0,00 billones, por cuartil de tamaño")
    print((df.assign(cero=df.gan_abs < 0.005)
             .groupby(cuartil, observed=True).cero.mean().mul(100).round(1)).to_string())


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Uso: python riesgo_deterioro.py ruta/al/archivo.csv")
    main(sys.argv[1])
