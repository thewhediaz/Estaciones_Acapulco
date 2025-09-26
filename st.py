import streamlit as st
import pandas as pd 
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
import datetime


#########################
# importante para poder ocultar el header 
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
# ---------------------------------------------------------------------------
# AUTOREFRESH: 3 minutos después de cada múltiplo de 5
ahora = datetime.datetime.now()

# Buscar el múltiplo de 5 más cercano hacia atrás
multiplo5 = (ahora.minute // 5) * 5
objetivo = ahora.replace(minute=multiplo5, second=0, microsecond=0) + datetime.timedelta(minutes=3)

# Si ya pasó el objetivo, saltamos al siguiente múltiplo de 5 + 3
if ahora >= objetivo:
    objetivo = objetivo + datetime.timedelta(minutes=5)

# Segundos hasta el próximo refresh
delta = objetivo - ahora
milisegundos_hasta_refresh = int(delta.total_seconds() * 1000)

# Ejecutar autorefresh
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
# Crear dos columnas
col1, col2 = st.columns([1, 1])  # proporciones iguales, ajustables

with col1:
    st.image(
        "https://acapulco.gob.mx/proteccioncivil/wp-content/uploads/2025/07/CGPCYB_24.png",
        width=300
    )

with col2:
    st.markdown(
        """
        <div style="text-align: right;">
            <img src="https://i.ibb.co/zTM1fBTg/SIATM.png" width="90">
        </div>
        """,
        unsafe_allow_html=True
    )


# Hora de la última actualización
#st.markdown(
#    """
#    <h2 style='text-align: center; margin-top: 10px; font-size: 20px; line-height: 1.3;'>
#        Monitoreo en tiempo real de estaciones meteorológicas - SIATM Acapulco
#    </h2>
#    """,
#    unsafe_allow_html=True
#)

###############################################################################
# CARGAMOS LOS DATOS DE GOOGLE
urls_estaciones = {
    "Pie de la Cuesta": "https://docs.google.com/spreadsheets/d/1aL5PkK8J-1wI9RZk0nOFT9Cd35jZXPB96FVieh8QeOw/export?format=csv&gid=645419203",
    "Coloso": "https://docs.google.com/spreadsheets/d/1aL5PkK8J-1wI9RZk0nOFT9Cd35jZXPB96FVieh8QeOw/export?format=csv&gid=912283735",
    "Xaltianguis": "https://docs.google.com/spreadsheets/d/1aL5PkK8J-1wI9RZk0nOFT9Cd35jZXPB96FVieh8QeOw/export?format=csv&gid=1707675775"
}

# Sin caché: cada vez que se llama, se leen los datos directamente
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

opciones_tiempo = {
    "Últimas 6 horas": 6,
    "Últimas 12 horas": 12,
    "Últimas 24 horas": 24,
    "Última semana": 7*24
}

seleccion = st.selectbox("Selecciona el intervalo de tiempo a graficar", list(opciones_tiempo.keys()))
horas = opciones_tiempo[seleccion]

hora_actual = pd.Timestamp.now()
hora_limite = hora_actual - pd.Timedelta(hours=horas)
df_filtrado = df_todas[df_todas["Fecha Local"] >= hora_limite]



###############################################################################
# Graficar Temperatura vs Fecha Local con Plotly (líneas + puntos)
# --- crear la figura como antes
fig = px.line(
    df_filtrado,
    x="Fecha Local",
    y="Temperatura (°C)",
    color_discrete_map={
    "Pie de la Cuesta": "#FF1744",
        "Coloso": "#0D47A1",
        "Xaltianguis": "#28A745"
    },
    color="Estación (mostrar/ocultar)",
    labels={"Temperatura (°C)": "Temperatura (°C)", "Fecha Local": "Fecha Local"},
    markers=True
)
fig.update_traces(marker=dict(size=5))  # Cambia 8 por el tamaño que quieras



ultima_hora = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

fig.update_layout(
    title={
        'text': f"""
        <b>Monitoreo de Temperatura - Estaciones SIATM Acapulco</b><br>
        <span style="font-size:14px; color:gray;">Intervalo: {seleccion} | Última actualización: {ultima_hora}</span>
        """,
        'x':0.5,           # centrar horizontalmente
        'xanchor': 'center',
        'yanchor': 'top'
    }
)


# --- FIJAR tamaño y evitar auto-resize
fig.update_layout(
    width=1200,                # ancho fijo en px
    height=700,                # alto fijo en px
    autosize=False,            # IMPORTANT: desactivar autosize
    margin=dict(l=70, r=40, t=80, b=70),  # márgenes fijos para evitar reflow al cambiar leyenda
    transition={'duration': 500, 'easing': 'linear'},
    legend=dict(
        orientation="h",
        y=-0.15,
        x=0.5,
        xanchor="center",
        title=dict(
            text="                                         Estación (mostrar/ocultar)",   # texto de título
            side="top"                          # se coloca arriba
        )
    )
)

# Mantener autorange de ejes (si quieres que min/max se recalculen al ocultar/mostrar series)
fig.update_xaxes(autorange=True)
fig.update_yaxes(
    autorange=True,
    dtick=1,
    gridcolor="rgba(229,236,246,0.15)",  # mismo color, 50% opacidad
    gridwidth=1
)


# leyenda hasta abajo

# Mostrar en Streamlit con config que NO sea responsive y SIN use_container_width
config = {"responsive": False, "displayModeBar": True}
# ... (Código anterior hasta fig.update_layout y fig.update_xaxes/yaxes) ...

# --- INICIO: Nuevo bloque para centrar la gráfica ---
# Ajusta las proporciones: por ejemplo, 1 parte para margen izquierdo, 6 para la gráfica, 1 para margen derecho.
# El '6' debe ser lo suficientemente grande para contener la gráfica de 1200px.
# Puedes ajustar [1, 6, 1] a [1, 4, 1] si el ancho de tu pantalla es menor y necesitas más espacio lateral.
col_vacia_izq, col_central, col_vacia_der = st.columns([1, 10, 1])

with col_central:
    # Mostrar en Streamlit con config que NO sea responsive y SIN use_container_width
    config = {"responsive": False, "displayModeBar": True}
    st.plotly_chart(fig, use_container_width=False, config=config)
# --- FIN: Nuevo bloque para centrar la gráfica ---










