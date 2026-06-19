import streamlit as st
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Optimizador Tecnológico", layout="wide")

st.title("🚀 Optimizador de Producción y Energía")
st.markdown("""
Esta herramienta resuelve un problema de programación lineal para maximizar la utilidad 
de producción de Smartwatches (X) y VR Headsets (Y) basándose en parámetros dinámicos.
""")

# --- SIDEBAR: PARÁMETROS INTERACTIVOS ---
st.sidebar.header("🎛️ Parámetros de Usuario")

# Coeficientes de utilidad (Z = Ax + By)
u_x = st.sidebar.slider("Utilidad Smartwatch ($)", 0, 100, 25)
u_y = st.sidebar.slider("Utilidad VR Headset ($)", 0, 100, 50)

st.sidebar.subheader("Restricciones")
max_capacidad = st.sidebar.number_input("Capacidad Total (x+y)", value=90)
min_energia = st.sidebar.number_input("Consumo Mínimo Energía (4x+6y)", value=390)
max_ensamblaje = st.sidebar.number_input("Tiempo Máximo Ensamblaje (min)", value=2000)

# Opción de variables enteras
es_entero = st.sidebar.checkbox("¿Solo unidades enteras?", value=False)
integrality = [1, 1] if es_entero else [0, 0]

# --- LÓGICA DE OPTIMIZACIÓN ---
# coeficientes de la función objetivo (negativos porque milp minimiza)
c = [-u_x, -u_y]

# coeficientes de las variables en las restricciones
A = [
    [1, 1],     # Capacidad
    [4, 6],     # Energía
    [15, 40]    # Tiempo
]

# cotas superiores e inferiores
bu = [max_capacidad, np.inf, max_ensamblaje]
bl = [-np.inf, min_energia, -np.inf]

constraints = LinearConstraint(A, bl, bu)
bounds = Bounds([0, 0], [np.inf, np.inf])

# Resolución
res = milp(c=c, constraints=constraints, bounds=bounds, integrality=integrality)

# --- MOSTRAR RESULTADOS ---
if res.success:
    col1, col2, col3 = st.columns(3)
    col1.metric("Utilidad Total (Z)", f"${-res.fun:,.2f}")
    col2.metric("Unidades Smartwatch (X)", f"{res.x[0]:.2f}")
    col3.metric("Unidades VR Headset (Y)", f"{res.x[1]:.2f}")
    
    st.success(f"Estado: {res.message}")
    
    # Verificación de consumos
    st.subheader("📊 Uso de Recursos")
    st.write(f"⚡ Energía total: **{4*res.x[0] + 6*res.x[1]:.2f} kWh**")
    st.write(f"⏱️ Tiempo de ensamblaje: **{15*res.x[0] + 40*res.x[1]:.2f} minutos**")
else:
    st.error(f"No se encontró solución: {res.message}")

**Pasos para ejecutar:**
1. Guarda el código anterior en un archivo llamado `app.py`.
2. Asegúrate de tener las librerías instaladas: `pip install streamlit scipy numpy`.
3. En tu terminal, ejecuta: `streamlit run app.py`.

¿Te gustaría que agreguemos algún gráfico del área de factibilidad o alguna otra métrica específica?
