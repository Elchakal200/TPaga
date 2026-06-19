import streamlit as st
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

# --- CONFIGURACIÓN DE LA INTERFAZ ---
st.set_page_config(page_title="Optimizador de Programación Lineal", layout="wide")

st.title("📊 Optimizador de Producción y Consumo Energético")
st.markdown("""
Esta aplicación te permite interactuar con un modelo de programación lineal (MILP). 
Modificá los parámetros en la barra lateral para ver cómo cambia la solución óptima en tiempo real.
""")

# --- BARRA LATERAL: PARÁMETROS DEL USUARIO ---
st.sidebar.header("🎛️ Configuración de Parámetros")

st.sidebar.subheader("💰 Utilidades de la Función Objetivo")
st.sidebar.markdown("*Determina cuánto aporta cada unidad a la ganancia total (Z = cx + dy)*")
u_x = st.sidebar.slider("Utilidad del Dispositivo 1 (x) [USD]:", min_value=0, max_value=100, value=25)
u_y = st.sidebar.slider("Utilidad del Dispositivo 2 (y) [USD]:", min_value=0, max_value=100, value=50)

st.sidebar.subheader("⚡ Parámetros de Costo Energético")
st.sidebar.markdown("*Configurá el costo por kWh asociado a cada dispositivo*")
costo_kwh_d1 = st.sidebar.slider("Costo por kWh del Dispositivo 1 (x) [USD]:", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
costo_kwh_d2 = st.sidebar.slider("Costo por kWh del Dispositivo 2 (y) [USD]:", min_value=0.1, max_value=5.0, value=1.0, step=0.1)

st.sidebar.subheader("📉 Límites de las Restricciones")
st.sidebar.markdown("*Restricciones operativas del sistema*")
limite_capacidad = st.sidebar.number_input("Capacidad máxima combinada (x + y ≤ C):", value=90)
minimo_energia = st.sidebar.number_input("Consumo mínimo requerido de energía (4x + 6y ≥ E):", value=390)
limite_ensamblaje = st.sidebar.number_input("Tiempo máximo de ensamblaje (15x + 40y ≤ T):", value=2000)

st.sidebar.subheader("⚙️ Tipo de Variables")
es_entero = st.sidebar.checkbox("Resolver como números enteros (unidades completas)", value=False)


# --- CÓDIGO ORIGINAL CON ADAPTACIONES INTERACTIVAS ---

# coeficientes de la función objetivo (negativos porque milp minimiza)
c = [-u_x, -u_y]

# coeficientes de las variables en las restricciones (Se mantiene igual al original)
A = [
    [1, 1],
    [4, 6],
    [15, 40]
]

# cotas superiores e inferiores basadas en lo que ingresa el usuario
bu = [limite_capacidad, np.inf, limite_ensamblaje]
bl = [-np.inf, minimo_energia, -np.inf]

constraints = LinearConstraint(A, bl, bu)
bounds = Bounds([0, 0], [np.inf, np.inf]) # Acá le decimos que las variables son positivas.

# Esto significa que para x,y si es 0 resuelve en continua, si es 1 resuelve en enteros
integrality = [1, 1] if es_entero else [0, 0]

res = milp(
    c=c,
    constraints=constraints,
    bounds=bounds,
    integrality=integrality
)


# --- SECCIÓN DE RESULTADOS ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📌 Estado del Modelo")
    if res.success:
        st.success(f"**Estado:** {res.message}")
        st.metric(label="Función Objetivo (Z - Utilidad Máxima)", value=f"${-res.fun:.2f}")
    else:
        st.error(f"**Estado:** {res.message}")
        st.warning("Revisá los parámetros de las restricciones, el modelo actual es infactible.")

    st.markdown("### 📋 Ecuaciones del problema actual:")
    st.markdown(f"**Maximizar:** $Z = {u_x}x + {u_y}y$")
    st.markdown(f"**Restricción 1 (Capacidad):** $x + y \\le {limite_capacidad}$")
    st.markdown(f"**Restricción 2 (Energía):** $4x + 6y \\ge {minimo_energia}$")
    st.markdown(f"**Restricción 3 (Ensamblaje):** $15x + 40y \\le {limite_ensamblaje}$")

with col2:
    st.subheader("🚀 Valores Óptimos Encontrados")
    if res.success:
        val_x = res.x[0]
        val_y = res.x[1]
        
        # Mostrar valores de x e y
        st.metric(label="Unidades de x (Dispositivo 1)", value=f"{val_x:.4f}")
        st.metric(label="Unidades de y (Dispositivo 2)", value=f"{val_y:.4f}")
        
        # Cálculos de consumo y costos basados en la solución y los deslizadores
        energia_x = 4 * val_x
        energia_y = 6 * val_y
        costo_total_energia = (energia_x * costo_kwh_d1) + (energia_y * costo_kwh_d2)
        
        st.markdown("### ⚡ Análisis Económico-Energético")
        st.write(f"🔹 **Energía consumida por x:** {energia_x:.2f} kWh (Costo: ${energia_x * costo_kwh_d1:.2f})")
        st.write(f"🔹 **Energía consumida por y:** {energia_y:.2f} kWh (Costo: ${energia_y * costo_kwh_d2:.2f})")
        st.info(f"💰 **Costo total de energía eléctrica:** ${costo_total_energia:.2f}")
    else:
        st.write("No se pueden calcular resultados para un modelo sin solución.")
