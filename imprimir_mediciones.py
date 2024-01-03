import sqlite3

# Establecer conexión con la base de datos.
conn = sqlite3.connect('presion_arterial.db')
c = conn.cursor()

# Consultar las mediciones de la base de datos y mostrarlas.
try:
    c.execute("SELECT fecha, sistolica, diastolica FROM mediciones")
    mediciones = c.fetchall()
    print("Fecha y Hora (UTC) - Sistólica (mmHg) - Diastólica (mmHg)")
    for medicion in mediciones:
        print(f"{medicion[0]} - {medicion[1]} - {medicion[2]}")
except Exception as e:
    print(f"Error al consultar la base de datos: {e}")
finally:
    # Cerrar conexión con la base de datos
    conn.close()