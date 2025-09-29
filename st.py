import streamlit as st
import pandas as pd 
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
import datetime
import pytz


alerta = True

if alerta:
    # Agregamos emojis de sirena al inicio y final del texto
    texto = "🚨 ¡ALERTA! Todos los usuarios deben prestar atención a los datos de monitoreo 🚨"
    tiempo_animacion = max(10, len(texto) * 0.5)

    st.markdown(
        f"""
        <div style="width:100%;height:150px;background:red;overflow:hidden;position:relative;animation: blink 1s infinite;
                    display:flex; align-items:center;">
            <div style="display:inline-block; white-space:nowrap; animation: scrollText {tiempo_animacion}s linear infinite; font-size:40px; color:white;">
                {texto}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  <!-- Espacio extra para separación -->
            </div>
        </div>

        <style>
        @keyframes blink {{
            0%, 50%, 100% {{opacity: 1;}}
            25%, 75% {{opacity: 0;}}
        }}

        @keyframes scrollText {{
            0% {{ transform: translateX(100%); }}
            100% {{ transform: translateX(-100%); }}
        }}
        </style>
        """,
        unsafe_allow_html=True
    )




else:
    # Crear cabecera con logos
    col1, col2 = st.columns([1, 1])
    with col1:
        st.image("https://acapulco.gob.mx/proteccioncivil/wp-content/uploads/2025/07/CGPCYB_24.png", width=300)
    with col2:
        st.markdown(
            """
            <div style="text-align: right;">
                <img src="https://i.ibb.co/zTM1fBTg/SIATM.png" width="90">
            </div>
            """,
            unsafe_allow_html=True
        )

    


###############################################################################
# ocultar header y footer de streamlit
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 0rem !important;
        margin-top: 0rem !important;
        padding-bottom: 0rem !important;
        margin-bottom: 0rem !important;
    }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------------------------------------------------------------
# AUTOREFRESH: 3 minutos después de cada múltiplo de 5
ahora = datetime.datetime.now()
multiplo5 = (ahora.minute // 5) * 5
objetivo = ahora.replace(minute=multiplo5, second=0, microsecond=0) + datetime.timedelta(minutes=3)
if ahora >= objetivo:
    objetivo = objetivo + datetime.timedelta(minutes=5)
delta = objetivo - ahora
milisegundos_hasta_refresh = int(delta.total_seconds() * 1000)
count = st_autorefresh(interval=milisegundos_hasta_refresh, key="datarefresh")

# Configuración de la página
st.set_page_config(
    page_title="Protección Civil - Acapulco",
    layout="wide"
)

# Ajuste de márgenes mediante CSS
st.markdown(
    """
    <style>
    .block-container {
        padding-left: 3rem;
        padding-right: 3rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

###############################################################################

###############################################################################
# CARGAMOS LOS DATOS DE GOOGLE
urls_estaciones = {
    "Pie de la Cuesta": "https://docs.google.com/spreadsheets/d/1aL5PkK8J-1wI9RZk0nOFT9Cd35jZXPB96FVieh8QeOw/export?format=csv&gid=645419203",
    "Coloso": "https://docs.google.com/spreadsheets/d/1aL5PkK8J-1wI9RZk0nOFT9Cd35jZXPB96FVieh8QeOw/export?format=csv&gid=912283735",
    "Xaltianguis": "https://docs.google.com/spreadsheets/d/1aL5PkK8J-1wI9RZk0nOFT9Cd35jZXPB96FVieh8QeOw/export?format=csv&gid=1707675775"
}

def obtener_datos(url):
    df = pd.read_csv(url)
    df["Fecha Local"] = pd.to_datetime(df["Fecha Local"])
    return df

dfs = []
for est, url in urls_estaciones.items():
    df = obtener_datos(url)
    df["Estación (mostrar/ocultar)"] = est
    dfs.append(df)

df_todas = pd.concat(dfs)

###############################################################################
# Crear selectores
col1, col2 = st.columns([1, 1])  
with col1:
    opciones_tiempo = {
        "Últimas 6 horas": 6,
        "Últimas 12 horas": 12,
        "Últimas 24 horas": 24,
        "Última semana": 7*24
    }
    seleccion = st.selectbox("Selecciona el intervalo de tiempo a graficar", list(opciones_tiempo.keys()))
    horas = opciones_tiempo[seleccion]

with col2:
    opciones_variable = {
        "Temperatura": {"col":"Temperatura (°C)", "unidad":"°C"},
        "Precipitación diaria": {"col":"Precipitación diaria (mm)", "unidad":"mm"},
        "Viento sostenido": {"col":"Viento promedio (km/h)", "unidad":"km/h"},
        "Racha máxima de viento en ultimos 10 minutos": {"col":"Ráfaga máxima (km/h)", "unidad":"km/h"},
        "Índice Ultravioleta": {"col":"Índice UV", "unidad":""},
        "Sensación térmica": {"col":"Sensación térmica calor (°C)", "unidad":"°C"},
        "Humedad relativa": {"col":"Humedad (%)", "unidad":"%"},
        "Presión (FALTA AJUSTAR A NIVEL DEL MAR)": {"col":"Presión (hPa)", "unidad":"hPa"}
    }
    seleccion2 = st.selectbox("Selecciona la variable a graficar", list(opciones_variable.keys()))
    variable_col = opciones_variable[seleccion2]["col"]
    variable_unidad = opciones_variable[seleccion2]["unidad"]

# Variable para configurar grid del eje Y según la variable
if seleccion2 == "Temperatura":
    dtick_y = 1
else:
    dtick_y = None  # deja automático para viento

###########################################################################################################################
# Zona horaria y filtrado
zona = pytz.timezone('America/Mexico_City')
hora_actual = pd.Timestamp.now(tz=zona)
df_todas["Fecha Local"] = pd.to_datetime(df_todas["Fecha Local"]).dt.tz_localize(zona, ambiguous='NaT', nonexistent='NaT')
hora_limite = hora_actual - pd.Timedelta(hours=horas)
df_filtrado = df_todas[df_todas["Fecha Local"] >= hora_limite]
if seleccion2 == "Precipitación diaria":
    df_filtrado = df_filtrado[df_filtrado["Estación (mostrar/ocultar)"] != "Xaltianguis"]

###############################################################################
# CREAR FIGURA
fig = px.line(
    df_filtrado,
    x="Fecha Local",
    y=variable_col,
    color_discrete_map={
        "Pie de la Cuesta": "#FF1744",
        "Coloso": "#0D47A1",
        "Xaltianguis": "#28A745"
    },
    color="Estación (mostrar/ocultar)",
    labels={variable_col: f"{variable_col}", "Fecha Local": "Fecha Local"},
    markers=False
)
#fig.update_traces(marker=dict(size=5))

ultima_hora = hora_actual.strftime("%Y-%m-%d %H:%M:%S")

# Actualizar layout: título, ejes, leyenda (sin tocar colores)
fig.update_layout(
    title={
        'text': f"""
        <b>Monitoreo de {seleccion2} - Estaciones SIATM Acapulco</b><br>
        <span style="font-size:14px; color:gray;">Intervalo: {seleccion} | Última actualización: {ultima_hora}</span>
        """,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'
    },
    width=1400,
    height=700,
    autosize=False,
    margin=dict(l=70, r=200, t=80, b=70),
    transition={'duration': 500, 'easing': 'linear'},
    legend=dict(
        orientation="v",
        x=1.05,
        y=1,
        xanchor="left",
        yanchor="top",
        title=dict(text="Estación (mostrar/ocultar)")
    )
)

# Configurar ejes
fig.update_xaxes(title="Fecha Local")
fig.update_yaxes(title=f"{variable_col}", dtick=dtick_y, gridcolor="rgba(229,236,246,0.15)", gridwidth=1)

###############################################################################
# Centrar gráfica en la página
col_vacia_izq, col_central, col_vacia_der = st.columns([1, 10, 1])
with col_central:
    st.plotly_chart(fig, use_container_width=False, config={"responsive": False, "displayModeBar": True})





















