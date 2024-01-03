import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import json

# Conexión con la base de datos SQLite
conn = sqlite3.connect('presion_arterial.db', check_same_thread=False)
c = conn.cursor()

# Definición de la función obtener_responsables después de crear el cursor c
def obtener_responsables():
    c.execute("SELECT id, nombre FROM responsables")
    return c.fetchall()

# Funciones para agregar responsables, pacientes y mediciones.
def agregar_responsable(nombre, rol):
    c.execute("INSERT INTO responsables (nombre, rol) VALUES (?, ?)", (nombre, rol))
    conn.commit()

def agregar_paciente(nombre, edad, historial):
    c.execute("INSERT INTO pacientes (nombre, edad, historial) VALUES (?, ?, ?)", (nombre, edad, historial))
    conn.commit()

def agregar_medicion(id_paciente, id_responsable, fecha, sistolica, diastolica):
    c.execute("INSERT INTO mediciones (id_paciente, id_responsable, fecha, sistolica, diastolica) VALUES (?, ?, ?, ?, ?)", (id_paciente, id_responsable, fecha, sistolica, diastolica))
    conn.commit()

# Cargar administradores desde JSON
def cargar_administradores():
    try:
        with open('administradores.json', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        st.error("El archivo de administradores no se encuentra.")
        return []

# Verificar si el usuario es administrador
def es_admin(usuario, contraseña):
    administradores = cargar_administradores()
    for admin in administradores:
        if admin.get('usuario') == usuario and admin.get('contraseña') == contraseña:
            return True
    return False


# Configuración inicial de la página de Streamlit
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

# Título principal y descripción de la aplicación
st.title('Monitoreo de Presión Arterial')
st.write("""
Esta aplicación permite el seguimiento continuo y detallado de la presión arterial, 
registrando y visualizando datos clave como la presión sistólica y diastólica.
""")

# Inicio de sesión y autenticación de usuario
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
    st.session_state['usuario'] = None
    st.session_state['rol'] = None

with st.sidebar:
    if not st.session_state['autenticado']:
        nombre_usuario = st.text_input("Nombre de Usuario", key="nombre_usuario")
        contraseña_usuario = st.text_input("Contraseña", type="password", key="contraseña_usuario")
        if st.button("Iniciar Sesión", key="boton_iniciar_sesion"):
            if es_admin(nombre_usuario, contraseña_usuario):
                st.session_state['autenticado'] = True
                st.session_state['usuario'] = nombre_usuario
                st.session_state['rol'] = 'Administrador'
                st.success("Inicio de sesión como Administrador.")
            else:
                responsables = obtener_responsables()
                if nombre_usuario in [resp[1] for resp in responsables]:
                    st.session_state['autenticado'] = True
                    st.session_state['usuario'] = nombre_usuario
                    st.session_state['rol'] = 'Responsable'
                    st.success("Inicio de sesión como Responsable.")
                else:
                    st.error("Inicio de sesión fallido. Verifica tus credenciales.")
    else:
        st.write(f"Bienvenido, {st.session_state['usuario']}!")


# Verificar si el usuario está autenticado para mostrar el contenido de la aplicación
if not st.session_state['autenticado']:
    st.warning("Por favor, inicia sesión.")
    st.stop()  # Detiene la ejecución del resto del script si no está autenticado

# Crear tabla de responsables si no existe.
c.execute('''
CREATE TABLE IF NOT EXISTS responsables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    rol TEXT
)
''')

# Crear tabla de pacientes si no existe.
c.execute('''
CREATE TABLE IF NOT EXISTS pacientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    edad INTEGER,
    historial TEXT
)
''')

# Crear tabla de mediciones si no existe.
c.execute('''
CREATE TABLE IF NOT EXISTS mediciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_paciente INTEGER,
    id_responsable INTEGER,
    fecha TIMESTAMP,
    sistolica INTEGER,
    diastolica INTEGER,
    FOREIGN KEY(id_paciente) REFERENCES pacientes(id),
    FOREIGN KEY(id_responsable) REFERENCES responsables(id)
)
''')
conn.commit()

# Función para obtener la lista actualizada de pacientes
def cargar_pacientes():
    c.execute("SELECT id, nombre FROM pacientes")
    return {nombre: id for id, nombre in c.fetchall()}

# Inicialización de la lista de pacientes en el estado de la sesión
if 'pacientes_dict' not in st.session_state:
    st.session_state['pacientes_dict'] = cargar_pacientes()
    
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
 
def mostrar_datos_paciente(mediciones_df):
    mediciones_df['Fecha'] = pd.to_datetime(mediciones_df['fecha']).dt.tz_localize(None)
    mediciones_df.drop(columns=['fecha'], inplace=True)
    
    st.dataframe(mediciones_df)

    fig, ax = plt.subplots()
    ax.plot(mediciones_df['Fecha'], mediciones_df['sistolica'], label='Sistólica', color='blue')
    ax.plot(mediciones_df['Fecha'], mediciones_df['diastolica'], label='Diastólica', color='red')
    ax.set_title('Evolución de la Presión Arterial')
    ax.set_xlabel('Fecha')
    ax.set_ylabel('Presión Arterial (mmHg)')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    ax.xaxis.set_tick_params(rotation=45)
    ax.grid(True)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.legend()
    plt.tight_layout()
    st.pyplot(fig)
    
    ultima_medicion = mediciones_df.iloc[-1]
    diagnostico, recomendacion = generar_diagnostico(ultima_medicion['sistolica'], ultima_medicion['diastolica'])
    st.markdown(f"<div class='diagnostico-recomendacion'><strong>Diagnóstico:</strong> {diagnostico}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='diagnostico-recomendacion'><strong>Recomendación:</strong> {recomendacion}</div>", unsafe_allow_html=True) 
 
def obtener_mediciones_con_nombres(id_paciente):
    consulta = """
    SELECT m.id, p.nombre AS nombre_paciente, r.nombre AS nombre_responsable, m.sistolica, m.diastolica, m.fecha
    FROM mediciones m
    JOIN pacientes p ON m.id_paciente = p.id
    JOIN responsables r ON m.id_responsable = r.id
    WHERE m.id_paciente = ?
    ORDER BY m.fecha DESC
    """
    return pd.read_sql_query(consulta, conn, params=(id_paciente,))
    
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

# Inicio de sesión y autenticación de usuario
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
    st.session_state['usuario'] = None
    st.session_state['rol'] = None

nombre_usuario = st.sidebar.text_input("Nombre de Usuario", key="nombre_usuario_login")
contraseña_usuario = st.sidebar.text_input("Contraseña", type="password", key="contraseña_usuario_login")

if not st.session_state['autenticado']:
    if nombre_usuario and contraseña_usuario and st.sidebar.button("Iniciar Sesión", key="boton_iniciar_sesion"):
        administradores = cargar_administradores()
        if nombre_usuario in [admin['usuario'] for admin in administradores] and any(admin['contraseña'] == contraseña_usuario for admin in administradores):
            st.session_state['autenticado'] = True
            st.session_state['usuario'] = nombre_usuario
            st.session_state['rol'] = 'Administrador'
            st.sidebar.success("Inicio de sesión como Administrador.")
        else:
            responsables = obtener_responsables()
            if nombre_usuario in [resp[1] for resp in responsables]:
                st.session_state['autenticado'] = True
                st.session_state['usuario'] = nombre_usuario
                st.session_state['rol'] = 'Responsable'
                st.sidebar.success("Inicio de sesión como Responsable.")
            else:
                st.sidebar.error("Inicio de sesión fallido. Verifica tus credenciales.")

if not st.session_state['autenticado']:
    st.warning("Por favor, inicia sesión.")
    st.stop()

# Interfaz para administrador para agregar responsables y pacientes
if st.session_state['autenticado'] and st.session_state['rol'] == "Administrador":
    with st.sidebar:
        st.header("Administrar Responsables")
        nombre_responsable = st.text_input("Nombre del Responsable", key="nombre_responsable")
        if st.button("Agregar Responsable", key="agregar_responsable"):
            agregar_responsable(nombre_responsable, "Responsable")
            st.success("Responsable agregado con éxito.")

    # Interfaz para agregar pacientes
    st.sidebar.title("Agregar Paciente")
    nombre_paciente = st.sidebar.text_input("Nombre del Paciente", placeholder="Ejemplo: Juan Pérez")
    edad_paciente = st.sidebar.number_input("Edad del Paciente", min_value=0, max_value=120, step=1)
    historial_paciente = st.sidebar.text_area("Historial Clínico")
    if st.sidebar.button("Agregar Paciente"):
        agregar_paciente(nombre_paciente, edad_paciente, historial_paciente)
        # Actualizar la lista de pacientes en el estado de la sesión
        st.session_state['pacientes_dict'] = cargar_pacientes()
        st.sidebar.success("Paciente agregado con éxito.")
        # Para refrescar la lista de selección de pacientes en la interfaz
        st.experimental_rerun()

# Interfaz para agregar mediciones
if 'rol' in st.session_state:
    # Identificar si el usuario es un administrador o responsable
    id_responsable_actual = None
    if st.session_state['rol'] == 'Responsable':
        responsable_query = pd.read_sql_query("SELECT id FROM responsables WHERE nombre = ?", conn, params=(st.session_state['usuario'],))
        if not responsable_query.empty:
            id_responsable_actual = responsable_query.iloc[0]['id']
    
    # Lista para seleccionar paciente
    pacientes_options = list(st.session_state['pacientes_dict'].keys())
    paciente_seleccionado_key = "paciente_seleccionado"
    paciente_seleccionado = st.sidebar.selectbox("Seleccionar Paciente", options=pacientes_options, key=paciente_seleccionado_key)
    
    # Registrar mediciones
    fecha_medicion = st.sidebar.date_input("Fecha de Medición")
    hora_medicion = st.sidebar.time_input("Hora de Medición")
    fecha_hora_medicion = datetime.combine(fecha_medicion, hora_medicion)
    sistolica = st.sidebar.number_input("Presión Sistólica (mmHg)", min_value=50, max_value=250)
    diastolica = st.sidebar.number_input("Presión Diastólica (mmHg)", min_value=30, max_value=150)
    if st.sidebar.button("Registrar Medición", key="registrar_medicion"):
        if id_responsable_actual is not None:  # Solo los responsables pueden registrar mediciones
            agregar_medicion(st.session_state['pacientes_dict'][paciente_seleccionado], id_responsable_actual, fecha_hora_medicion, sistolica, diastolica)
            st.sidebar.success("Medición registrada con éxito.")

# Visualización de Datos y Generación de Diagnósticos basada en el rol del usuario
if st.session_state['autenticado']:
    if st.session_state['rol'] == 'Administrador':
        # El administrador puede ver todas las mediciones
        st.header("Visualización de Mediciones (Administrador)")
        for id_paciente, nombre in c.execute("SELECT id, nombre FROM pacientes").fetchall():
            with st.container():
                st.markdown(f"<div class='paciente-container'>", unsafe_allow_html=True)
                st.markdown(f"<h2 class='paciente-header'>Paciente: {nombre}</h2>", unsafe_allow_html=True)
                
                mediciones_df = obtener_mediciones_con_nombres(id_paciente)
                
                if not mediciones_df.empty:
                    #st.dataframe(mediciones_df[['nombre_paciente', 'nombre_responsable', 'sistolica', 'diastolica', 'fecha']])
                    mostrar_datos_paciente(mediciones_df)
                else:
                    st.write("No hay mediciones disponibles para este paciente.")
                st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("---")
    elif st.session_state['rol'] == 'Responsable':
        # Los responsables solo pueden ver las mediciones asociadas a ellos
        st.header("Visualización de Mediciones (Responsable)")
        # Realizar consulta para obtener el id del responsable
        responsable_df = pd.read_sql_query("SELECT id FROM responsables WHERE nombre = ?", conn, params=(st.session_state['usuario'],))
        
        # Verificar si el responsable existe en la base de datos antes de continuar
        if not responsable_df.empty:
            id_responsable = responsable_df.iloc[0]['id']
            
            # Mostrar las mediciones para cada paciente asignado a este responsable
            for id_paciente, nombre in c.execute("SELECT id, nombre FROM pacientes").fetchall():
                with st.container():
                    st.markdown(f"<div class='paciente-container'>", unsafe_allow_html=True)
                    st.markdown(f"<h2 class='paciente-header'>Paciente: {nombre}</h2>", unsafe_allow_html=True)
                    
                    # Solo se muestran las mediciones para las que este responsable es responsable
                    mediciones_df = pd.read_sql_query("""
                        SELECT m.id, p.nombre AS nombre_paciente, r.nombre AS nombre_responsable, m.sistolica, m.diastolica, m.fecha
                        FROM mediciones m
                        JOIN pacientes p ON m.id_paciente = p.id
                        JOIN responsables r ON m.id_responsable = r.id
                        WHERE m.id_paciente = ? AND m.id_responsable = ?
                        ORDER BY m.fecha DESC
                        """, conn, params=(id_paciente, id_responsable))
                    
                    if not mediciones_df.empty:
                        #st.dataframe(mediciones_df[['nombre_paciente', 'nombre_responsable', 'sistolica', 'diastolica', 'fecha']])
                        mostrar_datos_paciente(mediciones_df)
                    else:
                        st.write("No hay mediciones disponibles para este paciente.")
                        st.markdown("</div>", unsafe_allow_html=True)
                    st.markdown("---")

# Cerrar conexión con la base de datos
conn.close()

# Sección de footer
st.sidebar.markdown('---')
st.sidebar.subheader('Creado por:')
st.sidebar.markdown('Alexander Oviedo Fadul')
st.sidebar.markdown("[GitHub](https://github.com/bladealex9848) | [Website](https://alexander.oviedo.isabellaea.com/) | [Instagram](https://www.instagram.com/alexander.oviedo.fadul) | [Twitter](https://twitter.com/alexanderofadul) | [Facebook](https://www.facebook.com/alexanderof/) | [WhatsApp](https://api.whatsapp.com/send?phone=573015930519&text=Hola%20!Quiero%20conversar%20contigo!%20)")