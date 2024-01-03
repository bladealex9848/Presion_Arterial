import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt

# Configuración inicial de la página de Streamlit.
st.set_page_config(
    page_title="Monitoreo de Presión Arterial",
    page_icon="💓",
    initial_sidebar_state='expanded',
    menu_items={
        'Get Help': 'https://www.isabellaea.com',
        'Report a bug': None,
        'About': "Aplicación de Monitoreo de Presión Arterial"
    }
)

# Título principal y descripción de la aplicación.
st.title('Monitoreo de Presión Arterial')
st.write("""
Esta aplicación permite el seguimiento continuo y detallado de la presión arterial, 
registrando y visualizando datos clave como la presión sistólica y diastólica.
""")

# Conexión con la base de datos SQLite.
conn = sqlite3.connect('presion_arterial.db')
c = conn.cursor()

# Creación de las tablas en la base de datos si no existen.
c.execute('''
CREATE TABLE IF NOT EXISTS pacientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    edad INTEGER,
    historial TEXT
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS mediciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_paciente INTEGER,
    fecha TIMESTAMP,
    sistolica INTEGER,
    diastolica INTEGER,
    FOREIGN KEY(id_paciente) REFERENCES pacientes(id)
)
''')
conn.commit()  # No olvides hacer commit después de crear las tablas.

# Función para agregar pacientes a la base de datos.
def agregar_paciente(nombre, edad, historial):
    c.execute("INSERT INTO pacientes (nombre, edad, historial) VALUES (?, ?, ?)", (nombre, edad, historial))
    conn.commit()

# Función para agregar mediciones a la base de datos.
def agregar_medicion(id_paciente, fecha, sistolica, diastolica):
    c.execute("INSERT INTO mediciones (id_paciente, fecha, sistolica, diastolica) VALUES (?, ?, ?, ?)", (id_paciente, fecha, sistolica, diastolica))
    conn.commit()

# Función para generar diagnósticos y recomendaciones basados en las mediciones de presión arterial.
def generar_diagnostico(sistolica, diastolica):
    if sistolica < 120 and diastolica < 80:
        return ("Normal", "Mantener estilo de vida saludable y monitoreo regular.")
    elif (140 <= sistolica or 90 <= diastolica) and (sistolica < 180 and diastolica < 120):
        return ("Presión arterial alta", "Consultar con el médico para evaluación y posible tratamiento.")
    elif 130 <= sistolica or 80 <= diastolica:
        return ("Presión arterial alta (con factores de riesgo)", "Seguimiento cercano con el médico y considerar cambios en el estilo de vida.")
    elif 180 <= sistolica or 120 <= diastolica:
        return ("Presión arterial peligrosamente alta", "Buscar atención médica inmediata.")
    else:
        return ("Presión arterial elevada", "Monitorizar y consultar con el médico.")

# Sección de la interfaz de usuario para agregar pacientes.
st.sidebar.title("Agregar Paciente")
nombre_paciente = st.sidebar.text_input("Nombre del Paciente", placeholder="Ejemplo: Juan Pérez")
edad_paciente = st.sidebar.number_input("Edad del Paciente", min_value=0, max_value=120, step=1)
historial_paciente = st.sidebar.text_area("Historial Clínico")
if st.sidebar.button("Agregar Paciente"):
    agregar_paciente(nombre_paciente, edad_paciente, historial_paciente)
    st.sidebar.success("Paciente agregado con éxito.")

# Sección de la interfaz de usuario para agregar mediciones.
st.sidebar.title("Agregar Mediciones")
c.execute("SELECT id, nombre FROM pacientes")
pacientes = c.fetchall()
pacientes_dict = {nombre: id for id, nombre in pacientes}
paciente_seleccionado = st.sidebar.selectbox("Seleccionar Paciente", options=pacientes_dict.keys())
fecha_medicion = st.sidebar.date_input("Fecha de Medición")
hora_medicion = st.sidebar.time_input("Hora de Medición")
fecha_hora_medicion = datetime.combine(fecha_medicion, hora_medicion)
sistolica = st.sidebar.number_input("Presión Sistólica (mmHg)", min_value=50, max_value=250)
diastolica = st.sidebar.number_input("Presión Diastólica (mmHg)", min_value=30, max_value=150)
if st.sidebar.button("Registrar Medición"):
    agregar_medicion(pacientes_dict[paciente_seleccionado], fecha_hora_medicion, sistolica, diastolica)
    st.sidebar.success("Medición registrada con éxito.")

# Visualización de Datos y Generación de Diagnósticos
for id_paciente, nombre in pacientes:
    st.header(f"Paciente: {nombre} (ID: {id_paciente})")
    mediciones_df = pd.read_sql_query("SELECT * FROM mediciones WHERE id_paciente = ? ORDER BY fecha", conn, params=(id_paciente,))
    
    if not mediciones_df.empty:
        st.dataframe(mediciones_df)
        ultima_medicion = mediciones_df.iloc[-1]
        diagnostico, recomendacion = generar_diagnostico(ultima_medicion['sistolica'], ultima_medicion['diastolica'])
        st.subheader(f"Último Diagnóstico: {diagnostico}")
        st.write(f"Recomendación: {recomendacion}")

        # Graficación de las mediciones
        fig, ax = plt.subplots()
        ax.plot(mediciones_df['fecha'], mediciones_df['sistolica'], label='Sistólica')
        ax.plot(mediciones_df['fecha'], mediciones_df['diastolica'], label='Diastólica')
        ax.set_title('Presión Arterial a lo Largo del Tiempo')
        ax.set_xlabel('Fecha')
        ax.set_ylabel('Presión Arterial (mmHg)')
        ax.legend()
        st.pyplot(fig)
    else:
        st.write("No hay mediciones disponibles para este paciente.")

# Cerrar conexión con la base de datos
conn.close()

# Sección de footer.
st.sidebar.markdown('---')
st.sidebar.subheader('Creado por:')
st.sidebar.markdown('Alexander Oviedo Fadul')
st.sidebar.markdown("[GitHub](https://github.com/bladealex9848) | [Website](https://alexander.oviedo.isabellaea.com/) | [Instagram](https://www.instagram.com/alexander.oviedo.fadul) | [Twitter](https://twitter.com/alexanderofadul) | [Facebook](https://www.facebook.com/alexanderof/) | [WhatsApp](https://api.whatsapp.com/send?phone=573015930519&text=Hola%20!Quiero%20conversar%20contigo!%20)")