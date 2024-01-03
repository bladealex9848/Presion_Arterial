import streamlit as st
from PIL import Image
import pandas as pd
import sqlite3
import pytz
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Define la zona horaria de Colombia
colombia_zone = pytz.timezone('America/Bogota')

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

# Carga y muestra el logo de la aplicación.
logo = Image.open('img/logo.png')
st.image(logo, width=250)

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

# Estilo CSS personalizado
st.markdown(
    """
    <style>
    .paciente-container {
        border-radius: 10px;
        box-shadow: 5px 5px 20px rgba(0,0,0,0.1);
        padding: 20px;
        margin-bottom: 20px;
        transition: box-shadow 0.3s ease-in-out;
        background-color: #f8f9fa;
    }
    .paciente-container:hover {
        box-shadow: 5px 5px 30px rgba(0,0,0,0.2);
    }
    .paciente-header {
        color: #4f8bf9;
        margin-bottom: 20px;
        font-weight: 500;
    }
    .grafica {
        margin-top: 20px;
        margin-bottom: 20px;
    }
    .grafica-title {
        text-align: center;
        margin-top: 10px;
        font-weight: bold;
        color: #333;
    }
    .diagnostico-recomendacion {
        margin-top: 20px;
        padding: 10px;
        background-color: #e9ecef;
        border-left: 5px solid #4f8bf9;
        font-weight: 500;
    }
    </style>
    """,
    unsafe_allow_html=True
)

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
    with st.container():
        st.markdown(f"<div class='paciente-container'>", unsafe_allow_html=True)
        st.markdown(f"<h2 class='paciente-header'>Paciente: {nombre} (ID: {id_paciente})</h2>", unsafe_allow_html=True)
        
        try:
            mediciones_df = pd.read_sql_query("SELECT * FROM mediciones WHERE id_paciente = ? ORDER BY fecha", conn, params=(id_paciente,))
        except Exception as e:
            st.error(f"Error al cargar las mediciones: {e}")
            continue

        if not mediciones_df.empty:
            try:
                mediciones_df['fecha'] = pd.to_datetime(mediciones_df['fecha'])
                mediciones_df['Fecha'] = mediciones_df['fecha'].dt.strftime('%d/%m/%Y')
                mediciones_df['Hora'] = mediciones_df['fecha'].dt.strftime('%I:%M %p')
                mediciones_df.rename(columns={'sistolica': 'Presión Sistólica (mmHg)', 'diastolica': 'Presión Diastólica (mmHg)'}, inplace=True)
                
                # Aquí asignamos el nombre del paciente a todas las filas en lugar del id_paciente.
                mediciones_df['Paciente'] = nombre  # Usamos la variable nombre del bucle for.
                
                # Preparar la tabla para mostrar.
                tabla_para_mostrar = mediciones_df[['Paciente', 'Presión Sistólica (mmHg)', 'Presión Diastólica (mmHg)', 'Fecha', 'Hora']].copy()
                
                st.dataframe(tabla_para_mostrar)

            except Exception as e:
                st.error(f"Error al procesar las mediciones: {e}")
                continue

            try:
                # Asegúrate de que las fechas para el gráfico sean reconocidas en el formato adecuado
                fig, ax = plt.subplots()
                ax.plot(mediciones_df['fecha'], mediciones_df['Presión Sistólica (mmHg)'], label='Sistólica', color='blue')
                ax.plot(mediciones_df['fecha'], mediciones_df['Presión Diastólica (mmHg)'], label='Diastólica', color='red')
                ax.set_title('Evolución de la Presión Arterial')
                ax.set_xlabel('Fecha y Hora')
                ax.set_ylabel('Presión Arterial (mmHg)')

                # Formatear el eje x para mostrar fecha y hora
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y %I:%M %p'))
                ax.xaxis.set_major_locator(mdates.AutoDateLocator())
                ax.xaxis.set_tick_params(rotation=45)
                ax.grid(True)
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.legend()
                plt.tight_layout()
                st.pyplot(fig)

            except Exception as e:
                st.error(f"Error al generar el gráfico: {e}")

            # Usar .iloc[-1].copy() para obtener una copia independiente de la última fila
            ultima_medicion = mediciones_df.iloc[-1].copy()
            diagnostico, recomendacion = generar_diagnostico(ultima_medicion['Presión Sistólica (mmHg)'], ultima_medicion['Presión Diastólica (mmHg)'])
            st.markdown(f"<div class='diagnostico-recomendacion'><strong>Diagnóstico:</strong> {diagnostico}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='diagnostico-recomendacion'><strong>Recomendación:</strong> {recomendacion}</div>", unsafe_allow_html=True)
        else:
            st.write("No hay mediciones disponibles para este paciente.")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("---")


# Cerrar conexión con la base de datos
conn.close()

# Sección de footer.
st.sidebar.markdown('---')
st.sidebar.subheader('Creado por:')
st.sidebar.markdown('Alexander Oviedo Fadul')
st.sidebar.markdown("[GitHub](https://github.com/bladealex9848) | [Website](https://alexander.oviedo.isabellaea.com/) | [Instagram](https://www.instagram.com/alexander.oviedo.fadul) | [Twitter](https://twitter.com/alexanderofadul) | [Facebook](https://www.facebook.com/alexanderof/) | [WhatsApp](https://api.whatsapp.com/send?phone=573015930519&text=Hola%20!Quiero%20conversar%20contigo!%20)")