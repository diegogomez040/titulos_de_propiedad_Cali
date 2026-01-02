import streamlit as st
import pandas as pd
import plotly.express as px

#Obtención de datos
@st.cache_data(show_spinner=True)
def cargar_datos():
    url = "https://www.datos.gov.co/resource/qzze-veut.csv?$limit=150000"
    df = pd.read_csv(url)

    df.columns = ["region", "codigo_dep", "nombre_dep", "codigo_mun", "nombre_mun",
                  "codigo_ORIP", "nombre_ORIP", "PDET", "fecha", "año", "mes",
                  "semestre", "trimestre", "genero", "etnia", "edad",
                  "discapacidad", "orientacion_sexual", "campesino",
                  "cabeza_de_hogar", "victima_de_conflicto_armado",
                  "sujeto_de_formalizacion", "numero_familia"]

    df = df[df['nombre_mun'] == 'SANTIAGO DE CALI']

    df = df.drop(columns=[
        'codigo_dep', 'codigo_mun', 'codigo_ORIP', 'region',
        'nombre_dep', 'nombre_mun', 'PDET',
        'etnia', 'edad', 'orientacion_sexual', 'campesino',
        'victima_de_conflicto_armado'
    ])

    moda_sujeto = df['sujeto_de_formalizacion'].mode()[0]
    df['sujeto_de_formalizacion'] = df['sujeto_de_formalizacion'].replace(
        "SIN INFORMACIÓN", moda_sujeto
    )

    moda_discapacidad = df['discapacidad'].mode()[0]
    df['discapacidad'] = df['discapacidad'].replace(
        "SIN INFORMACIÓN", moda_discapacidad
    )

    df['fecha'] = pd.to_datetime(df['fecha'])

    return df

df = cargar_datos()

#Mapeo de trimestre y semestre
map_trimestre = {
    "I Trim": 1,
    "II Trim": 4,
    "III Trim": 7,
    "IV Trim": 10
}
map_semestre = {
    "I Sem": 1,
    "II Sem": 7
}

st.set_page_config(
    page_title="Dashboard Formalización",
    layout="wide"
)

st.markdown("""
<h1 style="text-align: center;">
Procesos de formalización de propiedad en
</h1>
<h1 style="text-align: center;">
Cali - Colombia
</h1>
""", unsafe_allow_html=True)

st.markdown("""
Este dashboard permite explorar la evolución temporal del número de procesos
según diferentes niveles de agregación.
""")

# Rango mínimo y máximo disponibles
min_date = df["fecha"].min().to_pydatetime()
max_date = df["fecha"].max().to_pydatetime()

# Slider de rango
start_date, end_date = st.slider(
    "Selecciona el rango de fechas",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
    format="YYYY-MM"
)

df_filtrado = df[
    (df["fecha"] >= start_date) &
    (df["fecha"] <= end_date)
]

# Selector de nivel temporal
nivel = st.selectbox(
    "Selecciona temporalidad",
    options=["Día", "Mes", "Trimestre", "Semestre", "Año"]
)

# Selector de categoría
categoria = st.selectbox(
    "Selecciona categoría a analizar",
    options=[
        "Ninguna",
        "Género",
        "Discapacidad",
        "Sujeto de formalización",
        "Número de familia"
    ]
)

# -----------------------------------------------------
# Agregación según selección nivel
@st.cache_data
def agregar_datos(df_filtrado, nivel):
    if nivel == "Día":
        serie = df_filtrado.groupby(df_filtrado['fecha'].dt.floor('D')).size()
        serie = serie.reset_index(name="procesos")

    elif nivel == "Mes":
        serie = df_filtrado.groupby(['año', 'mes']).size().reset_index(name="procesos")
        serie['fecha'] = pd.to_datetime(
            serie['año'].astype(str) + "-" + serie['mes'].astype(str) + "-01"
        )

    elif nivel == "Trimestre":
        serie = df_filtrado.groupby(['año', 'trimestre']).size().reset_index(name="procesos")
        serie['trimestre'] = serie['trimestre'].map(map_trimestre)
        serie['fecha'] = pd.to_datetime(
            serie['año'].astype(str) + "-" + serie['trimestre'].astype(str) + "-01"
        )

    elif nivel == "Semestre":
        serie = df_filtrado.groupby(['año', 'semestre']).size().reset_index(name="procesos")
        serie['semestre'] = serie['semestre'].map(map_semestre)
        serie['fecha'] = pd.to_datetime(
            serie['año'].astype(str) + "-" + serie['semestre'].astype(str) + "-01"
        )

    else:
        serie = df_filtrado.groupby('año').size().reset_index(name="procesos")
        serie['fecha'] = pd.to_datetime(serie['año'].astype(str) + "-01-01")

    return serie

# Agregación según selección categoría
@st.cache_data
def agregar_por_categoria(df_filtrado, categoria_col):
    return (
        df_filtrado
        .groupby(categoria_col)
        .size()
        .reset_index(name="procesos")
        .sort_values("procesos", ascending=False)
    )

# -----------------------------------------------------
# Gráfica temporal
serie = agregar_datos(df_filtrado, nivel)

fig = px.line(
    serie,
    x="fecha",
    y="procesos",
    title=f"Procesos de formalización por {nivel}",
    markers=True,
    color_discrete_sequence=["#1f77b4"]
)

fig.update_layout(
    xaxis_title="Año",
    yaxis_title="Número de procesos",
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)

#Gráfica de categorías
if categoria != "Ninguna":

    mapa_columnas = {
        "Género": "genero",
        "Discapacidad": "discapacidad",
        "Sujeto de formalización": "sujeto_de_formalizacion",
        "Número de familia": "numero_familia"
    }

    columna = mapa_columnas[categoria]

    df_filtrado_cat = agregar_por_categoria(df_filtrado, columna)

    fig_cat = px.bar(
        df_filtrado_cat,
        x=columna,
        y="procesos",
        text="procesos",
        title=f"Distribución de procesos por {categoria.lower()}",
        color_discrete_sequence=["#ffe70e"]
    )

    fig_cat.update_layout(
        xaxis_title=categoria,
        yaxis_title="Número de procesos"
    )

    fig_cat.update_traces(textposition="outside")

    st.plotly_chart(fig_cat, use_container_width=True)
