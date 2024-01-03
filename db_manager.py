import streamlit as st
from PIL import Image
import os
import sqlite3
import pandas as pd

# Configuración inicial de la página de Streamlit
st.set_page_config(
    page_title="Gestor de Base de Datos SQLite",
    page_icon="🗃️",
    initial_sidebar_state='expanded',
    menu_items={
        'Get Help': 'https://www.isabellaea.com',
        'Report a bug': None,
        'About': """Esta es una herramienta de gestión de base de datos SQLite. 
                    Permite realizar operaciones CRUD (Crear, Leer, Actualizar, Eliminar) 
                    en cualquier base de datos SQLite. Desarrollada para ser flexible y 
                    adaptable a diferentes proyectos."""
    }
)

# Funciones auxiliares
def listar_bases_datos(ruta_directorio):
    return [archivo for archivo in os.listdir(ruta_directorio) if archivo.endswith('.db')]

def conectar_bd(ruta_bd):
    try:
        return sqlite3.connect(ruta_bd)
    except sqlite3.DatabaseError as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        return None

def obtener_esquema_bd(conn):
    return pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)

def obtener_datos_tabla(conn, tabla):
    return pd.read_sql_query(f"SELECT * FROM {tabla};", conn)

def obtener_columnas_tabla(conn, tabla):
    columnas = pd.read_sql_query(f"PRAGMA table_info({tabla});", conn)
    return columnas['name'].tolist()

def actualizar_registro(conn, tabla, id_registro, valores_nuevos):
    columnas = ', '.join([f"{k} = ?" for k in valores_nuevos.keys()])
    valores = list(valores_nuevos.values()) + [id_registro]
    query = f"UPDATE {tabla} SET {columnas} WHERE id = ?"
    conn.execute(query, valores)
    conn.commit()

# Carga y muestra el logo de la aplicación.
logo = Image.open('img/logo_bd.png')
st.image(logo, width=250)

# Título principal y descripción de la aplicación.
st.title('🗃️ Gestor de Base de Datos SQLite')
st.write("""
🛠️ Esta herramienta proporciona una interfaz intuitiva para gestionar bases de datos SQLite. 
Permite realizar operaciones CRUD (Crear, Leer, Actualizar, Eliminar) en tablas de bases de datos, 
facilitando la manipulación 🔄 y visualización 👁️‍🗨️ de datos. Diseñada para ser flexible y adaptable, 
es una solución ideal para proyectos que requieren una gestión eficiente de bases de datos SQLite.
""")

# Sidebar para operaciones
with st.sidebar:
    archivos_db = listar_bases_datos('.')
    base_datos_seleccionada = st.selectbox('Selecciona una base de datos', archivos_db)

    if base_datos_seleccionada:
        conn = conectar_bd(base_datos_seleccionada)
        if conn:
            c = conn.cursor()
            esquema = obtener_esquema_bd(conn)
            tabla_seleccionada = st.selectbox('Selecciona una tabla', esquema['name'])

            # Inserción de registros
            st.subheader(f"Añadir registro a {tabla_seleccionada}")
            if tabla_seleccionada:
                columnas_tabla = obtener_columnas_tabla(conn, tabla_seleccionada)
                valores_nuevos = {col: st.text_input(f"Valor para {col}", key=col) for col in columnas_tabla}
                if st.button(f"Añadir registro a {tabla_seleccionada}"):
                    columnas = ', '.join(valores_nuevos.keys())
                    placeholders = ', '.join(['?'] * len(valores_nuevos))
                    query = f"INSERT INTO {tabla_seleccionada} ({columnas}) VALUES ({placeholders})"
                    try:
                        c.execute(query, list(valores_nuevos.values()))
                        conn.commit()
                        st.success("Registro añadido exitosamente.")
                    except sqlite3.DatabaseError as e:
                        st.error(f"Error al añadir registro: {e}")

            # Actualización de registros
            st.subheader(f"Actualizar registro en {tabla_seleccionada}")
            if tabla_seleccionada:
                id_actualizar = st.text_input("ID del registro a actualizar", key="update")
                if id_actualizar:
                    try:
                        registro_actual = pd.read_sql_query(f"SELECT * FROM {tabla_seleccionada} WHERE id = {id_actualizar};", conn)
                        if not registro_actual.empty:
                            st.write("Registro Actual:", registro_actual)
                            valores_actualizados = {col: st.text_input(f"Nuevo valor para {col}", value=str(registro_actual.iloc[0][col]), key=col + "_update") for col in columnas_tabla}
                            if st.button(f"Actualizar registro en {tabla_seleccionada}"):
                                actualizar_registro(conn, tabla_seleccionada, id_actualizar, valores_actualizados)
                                st.success("Registro actualizado exitosamente.")
                    except sqlite3.DatabaseError as e:
                        st.error(f"Error al actualizar registro: {e}")

            # Eliminación de registros
            st.subheader(f"Eliminar registro de {tabla_seleccionada}")
            if tabla_seleccionada:
                registro_id = st.text_input("ID del registro a eliminar", key="delete")
                if st.button(f"Eliminar registro de {tabla_seleccionada}"):
                    try:
                        c.execute(f"DELETE FROM {tabla_seleccionada} WHERE id = ?", (registro_id,))
                        conn.commit()
                        st.success("Registro eliminado exitosamente.")
                    except sqlite3.DatabaseError as e:
                        st.error(f"Error al eliminar registro: {e}")

# Área principal para la visualización de la base de datos
if base_datos_seleccionada and tabla_seleccionada:
    st.header(f"Datos de la tabla {tabla_seleccionada}")
    try:
        datos_tabla = obtener_datos_tabla(conn, tabla_seleccionada)
        st.write(datos_tabla)
    except sqlite3.DatabaseError as e:
        st.error(f"Error al cargar datos de la tabla {tabla_seleccionada}: {e}")

    if conn:
        conn.close()
        
# Sección de footer.
st.sidebar.markdown('---')
st.sidebar.subheader('Creado por:')
st.sidebar.markdown('Alexander Oviedo Fadul')
st.sidebar.markdown("[GitHub](https://github.com/bladealex9848) | [Website](https://alexander.oviedo.isabellaea.com/) | [Instagram](https://www.instagram.com/alexander.oviedo.fadul) | [Twitter](https://twitter.com/alexanderofadul) | [Facebook](https://www.facebook.com/alexanderof/) | [WhatsApp](https://api.whatsapp.com/send?phone=573015930519&text=Hola%20!Quiero%20conversar%20contigo!%20)")