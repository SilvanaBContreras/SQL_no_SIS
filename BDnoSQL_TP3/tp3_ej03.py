import csv
from cassandra.cluster import Cluster
from cassandra.concurrent import execute_concurrent_with_args

archivo_entrada = 'full_export.csv'
nombre_archivo_resultado_ejercicio = ['tp3_ej03_parte1.txt', 'tp3_ej03_parte2.txt']

conexion = {
    'cassandraurl': 'localhost',
    'cassandrapuerto': 9042
}

keyspace = "sports"
tabla_especialidades = "especialidades"
tabla_especialidades_contador = "especialidades_contador"

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

def grabar_linea(archivo, linea):
    print(linea)
    archivo.write(str(linea) + '\n')

def inicializar(conn):
    session = Cluster(contact_points=[conn["cassandraurl"]], port=conn["cassandrapuerto"]).connect()
    create_keyspace_query = f"""
    CREATE KEYSPACE IF NOT EXISTS {keyspace}
    WITH replication = {{
        'class': 'SimpleStrategy',
        'replication_factor': 1
    }}
    """
    session.execute(create_keyspace_query)
    print("Keyspace created successfully!")

    session.set_keyspace(keyspace)

    drop_table_query = f"""DROP TABLE IF EXISTS {tabla_especialidades}"""
    session.execute(drop_table_query)
    print("Table dropped successfully!")

    drop_table_query = f"""DROP TABLE IF EXISTS {tabla_especialidades_contador}"""
    session.execute(drop_table_query)
    print("Table dropped successfully!")

    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {tabla_especialidades} (
        tipo_especialidad TEXT,
        id_tipo_especialidad INT,
        especialidad TEXT,
        cantidad_marcas COUNTER,
        PRIMARY KEY(tipo_especialidad, id_tipo_especialidad, especialidad)
    );
    """

    session.execute(create_table_query)
    print("Table created successfully!")

    return session

def procesar_tabla(db, reader):
    rows = [
        (int(row["id_tipo_especialidad"]), row["nombre_tipo_especialidad"], row["nombre_especialidad"])
        for row in reader
    ]

    stmt_counter = db.prepare(f"""
                              UPDATE {tabla_especialidades}
                              SET cantidad_marcas = cantidad_marcas + 1
                              WHERE tipo_especialidad = ?
                                AND id_tipo_especialidad = ?
                                AND especialidad = ?
                              """)

    counter_args = [(tipo, id_tipo, especialidad) for id_tipo, tipo, especialidad in rows]

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

def generar_reporte(db):
    prepared_query = db.prepare(
        f"""
        SELECT id_tipo_especialidad, tipo_especialidad, especialidad
        FROM {tabla_especialidades}
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
        f"""
        SELECT tipo_especialidad, SUM(cantidad_marcas) AS cantidad_marcas
        FROM {tabla_especialidades}
        GROUP BY tipo_especialidad
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
    cluster = db.cluster
    try:
        db.execute(f"DROP TABLE IF EXISTS {keyspace}.{tabla_especialidades}")
    finally:
        db.shutdown()
        cluster.shutdown()


ejecutar(archivo_entrada, conexion)