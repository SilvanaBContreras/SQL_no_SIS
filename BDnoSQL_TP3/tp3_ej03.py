import csv
from cassandra.cluster import Cluster
from cassandra.concurrent import execute_concurrent_with_args

archivo_entrada = 'full_export.csv'
nombre_archivo_resultado_ejercicio = ['tp3_ej03_parte1.txt', 'tp3_ej03_parte2.txt']

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
    drop_table_query = """DROP TABLE IF EXISTS especialidades"""
    session.execute(drop_table_query)
    print("Table dropped successfully!")

    drop_table_query = """DROP TABLE IF EXISTS especialidades_contador"""
    session.execute(drop_table_query)
    print("Table dropped successfully!")

    # Create table
    create_table_query = """
    CREATE TABLE IF NOT EXISTS especialidades (
        id_tipo_especialidad INT,
        tipo_especialidad TEXT,
        especialidad TEXT,
        PRIMARY KEY(id_tipo_especialidad, especialidad)
    );
    """

    session.execute(create_table_query)

    create_table_query = """
    CREATE TABLE IF NOT EXISTS especialidades_contador (
        tipo_especialidad TEXT PRIMARY KEY,
        cantidad_marcas COUNTER
    );
    """

    session.execute(create_table_query)
    print("Table created successfully!")

    return session


def procesar_tabla(db, reader):
    # No usamos set porque aca me interesa tener todas las filas
    rows = [
        (int(row["id_tipo_especialidad"]), row["nombre_tipo_especialidad"], row["nombre_especialidad"])
        for row in reader
    ]

    stmt_insert = db.prepare("""
                             INSERT INTO especialidades (id_tipo_especialidad, tipo_especialidad, especialidad)
                             VALUES (?, ?, ?)
                             """)

    stmt_counter = db.prepare("""
                              UPDATE especialidades_contador
                              SET cantidad_marcas = cantidad_marcas + 1
                              WHERE tipo_especialidad = ?
                              """)

    results_insert = execute_concurrent_with_args(
        db,
        stmt_insert,
        rows,
        concurrency=100,
        results_generator=False
    )
    for success, result in results_insert:
        if not success:
            raise result

    # Obtiene el id_tipo_especialidad que es el unico input necesario para el contador
    counter_args = [(r[1],) for r in rows]

    results_counter = execute_concurrent_with_args(
        db,
        stmt_counter,
        counter_args,
        concurrency=100,
        results_generator=False
    )
    for success, result in results_counter:
        if not success:
            raise result


# Listar para cada tipo de especialidad los id y nombre de cada uno. Además se debe listar por cada
# tipo los nombres de las especialidades que se encuentran asociadas a cada uno. Al finalizar este
# listado se debe emitir un segundo listado indicando el nombre del tipo de especialidad y la cantidad
# de marcas (es decir, filas del archivo) registradas para ese tipo de especialidad.

def generar_reporte(db):
    prepared_query = db.prepare(
        """
        SELECT id_tipo_especialidad, tipo_especialidad, especialidad
        FROM especialidades 
        """
    )
    rows = db.execute(prepared_query)

    with open(nombre_archivo_resultado_ejercicio[0], "w", encoding="utf-8") as archivo:
        titulo_reporte = "Tipos de especialidad"
        encabezado_columnas = "id_tipo_especialidad, tipo_especialidad, especialidad"
        grabar_linea(archivo, titulo_reporte)
        grabar_linea(archivo, encabezado_columnas)

        for row in rows:
            grabar_linea(archivo, f"{row.id_tipo_especialidad}, {row.tipo_especialidad}, {row.especialidad}")

    prepared_query = db.prepare(
        """
        SELECT tipo_especialidad, cantidad_marcas
        FROM especialidades_contador 
        """
    )
    rows = db.execute(prepared_query)

    with open(nombre_archivo_resultado_ejercicio[1], "w", encoding="utf-8") as archivo:
        titulo_reporte = "Cantidad de marcas por tipo de especialidad"
        encabezado_columnas = "tipo_especialidad, cantidad_marcas"
        grabar_linea(archivo, titulo_reporte)
        grabar_linea(archivo, encabezado_columnas)

        for row in rows:
            grabar_linea(archivo, f"{row.tipo_especialidad}, {row.cantidad_marcas}")


def finalizar(db):
    db.shutdown()


ejecutar(archivo_entrada, conexion)


