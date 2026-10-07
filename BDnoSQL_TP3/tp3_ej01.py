import csv
from cassandra.cluster import Cluster

# Ubicacion del archivo CSV con el contenido provisto por la catedra
#archivo_entrada = 'full_export.csv'
archivo_entrada = 'full_export_version_corta.csv'
nombre_archivo_resultado_ejercicio = 'tp3_ej01.txt'

# Objeto de configuracion para conectarse a la base de datos usada en este ejercicio
conexion = {
    'cassandraurl': 'localhost',
    'cassandrapuerto': 9042
}


# Funcion que dada la configuracion y ubicacion del archivo, carga la base de datos, genera el reporte, y borra la
# base de datos
def ejecutar(file, conn):
    import time

    start = time.time()
    db = inicializar(conn)
    df_filas = csv.DictReader(open(file, "r", encoding="utf-8"))
    count = 0
    startbloque = time.time()
    for fila in df_filas:
        procesar_fila(db, fila)
        count += 1
        if 0 == count%100:
            endbloque = time.time()
            tiempo = endbloque-startbloque
            print(str(count) + " en " + str(tiempo) + " segundos")
            startbloque = time.time()
    generar_reporte(db)
    finalizar(db)
    end = time.time()
    print("tiempo total en segundos")
    print(end - start)


# Funcion que dado un archivo abierto y una linea, imprime por consola y guarda al final de archivo esa linea
def grabar_linea(archivo, linea):
    print(linea)
    archivo.write(str(linea) + '\n')


def inicializar(conn):
    cassandra_session = Cluster(contact_points=[conn["cassandraurl"]], port=conn["cassandrapuerto"]).connect()
    # crear db
    create_keyspace_query = """
    CREATE KEYSPACE IF NOT EXISTS equipo1
    WITH replication = {
        'class': 'SimpleStrategy',
        'replication_factor': 1
    }
    """
    cassandra_session.execute(create_keyspace_query)
    print("Keyspace created successfully!")

    # Use the keyspace
    cassandra_session.set_keyspace('equipo1')

    #Create table
    create_table_query = """
    CREATE TABLE IF NOT EXISTS deportista (
        id int PRIMARY KEY,
        nombre TEXT        
    )
    """
    cassandra_session.execute(create_table_query)
    print("Table created successfully!")

    return cassandra_session



# Funcion que dada una linea del archivo CSV (en forma de objeto) va a encargarse de insertar el (o los) objetos
# necesarios
# Debe ser implementada por el alumno
def procesar_fila(db, fila):
    id_deportista = int(fila["id_deportista"])
    db.execute(
        "INSERT INTO deportista (id, nombre) VALUES (%s, %s)",
        (id_deportista, fila["nombre_deportista"])
        )


# Funcion que realiza el o los queries que resuelven el ejercicio, utilizando la base de datos.
# Debe ser implementada por el alumno

def generar_reporte(db):
    prepared_query = db.prepare(
        "SELECT id, nombre FROM deportista WHERE id IN ?"
    )
    rows = db.execute(prepared_query, ([10, 20, 30],))

    with open(nombre_archivo_resultado_ejercicio, "w", encoding="utf-8") as archivo:
        titulo_reporte = "Deportistas con ID 10, 20 y 30"
        encabezado_columnas = "id,nombre"
        grabar_linea(archivo, titulo_reporte)
        grabar_linea(archivo, encabezado_columnas)

        for row in rows:
            grabar_linea(archivo, f"{row.id},{row.nombre}")


# Funcion para el borrado de estructuras generadas para este ejercicio
def finalizar(db):
    db.shutdown()
    # Borrar la estructura de la base de datos


# Llamado a la ejecucion del programa
ejecutar(archivo_entrada, conexion)


