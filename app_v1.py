import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3

# Configuramos la aplicación
st.set_page_config(page_title="Monitoreo de presión arterial", page_icon="⚕️")

# Función para obtener la conexión a la base de datos
def get_connection():
    conn = sqlite3.connect("presion_arterial.db", check_same_thread=False)
    return conn

# Creación y manejo de la tabla en la base de datos
def create_table():
    conn = get_connection()
    conn.execute("""CREATE TABLE IF NOT EXISTS mediciones (
        nombre TEXT,
        edad INT,
        altura FLOAT,
        peso FLOAT,
        dia INT,
        mañana INT,
        tarde INT
    )""")
    conn.close()

# Definición de funciones
def ingresar_medicion():
    with st.form("Formulario de Medición"):
        # Solicitamos la información del paciente
        nombre = st.text_input("Nombre:")
        edad = st.number_input("Edad:", min_value=0, max_value=150)
        altura = st.number_input("Altura (en cm):", min_value=0.0, max_value=300.0)
        peso = st.number_input("Peso (en kg):", min_value=0.0, max_value=500.0)

        # Solicitamos las lecturas de presión arterial
        dia = st.number_input("Día:", min_value=1, max_value=31)
        mañana = st.number_input("Presión por la mañana (mmHg):", min_value=0, max_value=300)
        tarde = st.number_input("Presión por la tarde (mmHg):", min_value=0, max_value=300)

        # Botón de envío
        submit_button = st.form_submit_button(label="Ingresar Medición")

    if submit_button:
        conn = get_connection()
        conn.execute("""INSERT INTO mediciones (nombre, edad, altura, peso, dia, mañana, tarde)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (nombre, edad, altura, peso, dia, mañana, tarde))
        conn.commit()
        conn.close()
        st.success("Medición ingresada correctamente.")

def graficar_mediciones():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM mediciones", conn)
    conn.close()

    plt.figure()
    plt.plot(df["dia"], df["mañana"], label="Pasada la mañana")
    plt.plot(df["dia"], df["tarde"], label="Pasada la tarde")
    plt.xlabel("Día")
    plt.ylabel("Presión arterial (mmHg)")
    plt.legend()
    st.pyplot(plt)

def exportar_mediciones():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM mediciones", conn)
    conn.close()

    with pd.ExcelWriter("mediciones.xlsx") as writer:
        df.to_excel(writer)
    with open("mediciones.xlsx", "rb") as file:
        st.download_button(label="Descargar Mediciones", data=file, file_name="mediciones.xlsx")

# Creación de la tabla
create_table()

# Interfaz de usuario
st.title("Monitoreo de Presión Arterial")
ingresar_medicion()

if st.button("Graficar mediciones"):
    graficar_mediciones()

if st.button("Exportar mediciones"):
    exportar_mediciones()