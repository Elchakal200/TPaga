import streamlit as st
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

# --- CONFIGURACIÓN DE LA INTERFAZ ---
st.set_page_config(page_title="Optimizador de Programación Lineal", layout="wide")

st.title("📊 Optimizador de Producción y Consumo Energético")
st.markdown("""
Esta aplicación te permite interactuar con un modelo de programación lineal (MILP) y evaluar el impacto 
de múltiples consumos eléctricos del hogar en tiempo real.
""")

# --- INICIALIZACIÓN DEL ESTADO DE LA SESIÓN (MEMORIA DE ELECTRODOMÉSTICOS) ---
if "electrodomesticos" not in st.session_state:
    # Arrancamos con uno por defecto para que la lista no esté vacía
    st.session_state.electrodomesticos = [
        {"nombre": "Heladera", "potencia": 250, "horas": 120}
    ]

# --- BARRA LATERAL: PARÁMETROS DEL USUARIO ---
st.sidebar.header("🎛️ Configuración de Parámetros")

st.sidebar.subheader("💰 Utilidades de la Función Objetivo")
u_x = st.sidebar.slider("Utilidad del Dispositivo 1 (x) [USD]:", min_value=0, max_value=100, value=25)
u_y = st.sidebar.slider("Utilidad del Dispositivo 2 (y) [USD]:", min_value=0, max_value=100, value=50)

st.sidebar.subheader("⚡ Parámetros de Costo Energético")
costo_kwh_d1 = st.sidebar.slider("Costo por kWh del Dispositivo 1 (x) [USD]:", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
costo_kwh_d2 = st.sidebar.slider("Costo por kWh del Dispositivo 2 (y) [USD]:", min_value=0.1, max_value=5.0, value=1.0, step=0.1)

st.sidebar.subheader("📉 Límites de las Restricciones")
limite_capacidad = st.sidebar.number_input("Capacidad máxima combinada (x + y ≤ C):", value=90)
minimo_energia = st.sidebar.number_input("Consumo mínimo requerido de energía (4x + 6y ≥ E):", value=390)
limite_ensamblaje = st.sidebar.number_input("Tiempo máximo de ensamblaje (15x + 40y ≤ T):", value=2000)

st.sidebar.subheader("⚙️ Tipo de Variables")
es_entero = st.sidebar.checkbox("Resolver como números enteros (unidades completas)", value=False)


# --- DISPOISICIÓN EN COLUMNAS (CONTENIDO PRINCIPAL) ---
col_izq, col_der = st.columns(2)

with col_izq:
    # --- SECCIÓN: GESTIÓN DINÁMICA DE ELECTRODOMÉSTICOS ---
    st.subheader("🏠 Consumos Domésticos Adicionales")
    st.markdown("*Agregá o eliminá elementos para evaluar su impacto en el costo mensual global.*")
    
    # Formulario para añadir nuevos elementos
    with st.form("nuevo_electrodomestico", clear_on_submit=True):
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            nuevo_nombre = st.text_input("Nombre:", value="Microondas")
        with col_f2:
            nueva_potencia = st.number_input("Potencia (Watts):", min_value=1, value=800)
        with col_f3:
            nuevas_horas = st.number_input("Horas/mes:", min_value=1, max_value=744, value=30)
            
        boton_agregar = st.form_submit_button("➕ Agregar Electrodoméstico")
        
        if boton_agregar:
            st.session_state.electrodomesticos.append({
                "nombre": nuevo_nombre,
                "potencia": nueva_potencia,
                "horas": nuevas_horas
            })
            st.rerun() # Recarga la app para mostrar el nuevo elemento inmediatamente

    # Mostrar y permitir eliminar elementos de la lista actual
    if st.session_state.electrodomesticos:
        st.markdown("### 📋 Lista de Dispositivos Conectados")
        for indice, item in enumerate(st.session_state.electrodomesticos):
            col_item, col_btn = st.columns([4, 1])
            with col_item:
                consumo_estimado = (item['potencia'] * item['horas']) / 1000
                st.write(f"• **{item['nombre']}** ({item['potencia']}W) — {item['horas']} hs/mes $\\rightarrow$ **{consumo_estimado:.2f} kWh**")
            with col_btn:
                # Botón de eliminación con clave única por índice
                if st.button("🗑️", key=f"btn_{indice}"):
                    st.session_state.electrodomesticos.pop(indice)
                    st.rerun()
    else:
        st.info("No hay electrodomésticos adicionales agregados.")


# --- EJECUCIÓN DEL CÓDIGO ORIGINAL DE OPTIMIZACIÓN ---

c = [-u_x, -u_y]
A = [
    [1, 1],
    [4, 6],
    [15, 40]
]
bu = [limite_capacidad, np.inf, limite_ensamblaje]
bl = [-np.inf, minimo_energia, -np.inf]

constraints = LinearConstraint(A, bl, bu)
bounds = Bounds([0, 0], [np.inf, np.inf])
integrality = [1, 1] if es_entero else [0, 0]

res = milp(c=c, constraints=constraints, bounds=bounds, integrality=integrality)


# --- COLUMNA DERECHA: SECCIÓN DE RESULTADOS ---
with col_der:
    st.subheader("📌 Estado del Modelo Lineal")
    if res.success:
        st.success(f"**Estado:** {res.message}")
        st.metric(label="Función Objetivo (Z - Utilidad Máxima)", value=f"${-res.fun:.2f}")
    else:
        st.error(f"**Estado:** {res.message}")
        st.warning("El modelo actual es infactible con estas restricciones.")

    st.subheader("🚀 Valores Óptimos Encontrados")
    if res.success:
        val_x = res.x[0]
        val_y = res.x[1]
        
        st.metric(label="Unidades de x (Dispositivo 1)", value=f"{val_x:.4f}")
        st.metric(label="Unidades de y (Dispositivo 2)", value=f"{val_y:.4f}")
        
        # Cálculos de la optimización de producción
        energia_x = 4 * val_x
        energia_y = 6 * val_y
        costo_produccion_energia = (energia_x * costo_kwh_d1) + (energia_y * costo_kwh_d2)
        
        # --- CÁLCULO ACUMULADO DE LA LISTA DINÁMICA ---
        total_kwh_hogar = 0.0
        for item in st.session_state.electrodomesticos:
            total_kwh_hogar += (item['potencia'] * item['horas']) / 1000
            
        costo_medio_kwh = (costo_kwh_d1 + costo_kwh_d2) / 2
        costo_hogar_total = total_kwh_hogar * costo_medio_kwh
        costo_total_combinado = costo_produccion_energia + costo_hogar_total
        
        st.markdown("### ⚡ Análisis Económico-Energético Desglosado")
        st.write(f"🔹 **Energía producción (x):** {energia_x:.2f} kWh (Costo: ${energia_x * costo_kwh_d1:.2f})")
        st.write(f"🔹 **Energía producción (y):** {energia_y:.2f} kWh (Costo: ${energia_y * costo_kwh_d2:.2f})")
        st.write(f"🏠 **Consumo total electrodomésticos:** {total_kwh_hogar:.2f} kWh (Costo: ${costo_hogar_total:.2f})")
        
        st.markdown("---")
        st.info(f"💰 **Costo TOTAL de energía eléctrica combinado:** ${costo_total_combinado:.2f}")
