import csv
from cassandra.cluster import Cluster
from cassandra.concurrent import execute_concurrent_with_args

archivo_entrada = 'full_export.csv'
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
    reader = csv.DictReader(open(file, "r", encoding="utf-8"))
    startbloque = time.time()
    procesar_tabla(db, reader)
    endbloque = time.time()
    tiempo = endbloque-startbloque
    print("Completado en " + str(tiempo) + " segundos")
    generar_reporte(db)
    finalizar(db)
    end = time.time()
    print(end - start)


# Funcion que dado un archivo abierto y una linea, imprime por consola y guarda al final de archivo esa linea
def grabar_linea(archivo, linea):
    print(linea)
    archivo.write(str(linea) + '\n')


def inicializar(conn):
    session = Cluster(contact_points=[conn["cassandraurl"]], port=conn["cassandrapuerto"]).connect()
    # crear db
    create_keyspace_query = """
    CREATE KEYSPACE IF NOT EXISTS sports
    WITH replication = {
        'class': 'SimpleStrategy',
        'replication_factor': 1
    }
    """
    session.execute(create_keyspace_query)
    print("Keyspace created successfully!")

    # Use the keyspace
    session.set_keyspace('sports')

    # Drop table
    drop_table_query = """DROP TABLE IF EXISTS deportista"""
    session.execute(drop_table_query)
    print("Table dropped successfully!")

    #Create table
    create_table_query = """
    CREATE TABLE IF NOT EXISTS deportista (
        id INT PRIMARY KEY,
        nombre TEXT        
    );
    """
    session.execute(create_table_query)
    print("Table created successfully!")

    return session


def procesar_tabla(db, reader):
    rows = ((int(row["id_deportista"]), row["nombre_deportista"]) for row in reader)
    statement = db.prepare("INSERT INTO deportista (id, nombre) VALUES (?, ?)")

    results = execute_concurrent_with_args(
        db,
        statement,
        rows,
        concurrency=1000,
        results_generator=True
    )

    for success, result in results:
        if not success:
            raise result


def generar_reporte(db):
    prepared_query = db.prepare(
        "SELECT id, nombre FROM deportista WHERE id IN ?"
    )
    ids = [10, 20, 30]
    rows = db.execute(prepared_query, (ids,))

    with open(nombre_archivo_resultado_ejercicio, "w", encoding="utf-8") as archivo:
        titulo_reporte = "Deportistas con ID 10, 20 y 30"
        encabezado_columnas = "id,nombre"
        grabar_linea(archivo, titulo_reporte)
        grabar_linea(archivo, encabezado_columnas)

        for row in rows:
            grabar_linea(archivo, f"{row.id},{row.nombre}")


def finalizar(db):
    db.shutdown()


ejecutar(archivo_entrada, conexion)


