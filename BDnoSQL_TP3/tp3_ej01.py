import csv
from cassandra.cluster import Cluster
from cassandra.concurrent import execute_concurrent_with_args

archivo_entrada = 'full_export.csv'
nombre_archivo_resultado_ejercicio = 'tp3_ej01.txt'

conexion = {
    'cassandraurl': 'localhost',
    'cassandrapuerto': 9042
}

keyspace = "sports"
tabla_deportista = "deportista"

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
    # crear db
    create_keyspace_query = f"""
    CREATE KEYSPACE IF NOT EXISTS {keyspace}
    WITH replication = {{
        'class': 'SimpleStrategy',
        'replication_factor': 1
    }}
    """
    session.execute(create_keyspace_query)
    print("Keyspace created successfully!")

    # Use the keyspace
    session.set_keyspace(keyspace)

    # Drop table
    drop_table_query = f"""DROP TABLE IF EXISTS {tabla_deportista}"""
    session.execute(drop_table_query)
    print("Table dropped successfully!")

    #Create table
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {tabla_deportista} (
        id INT PRIMARY KEY,
        nombre TEXT        
    );
    """
    session.execute(create_table_query)
    print("Table created successfully!")

    return session

def procesar_tabla(db, reader):
    rows = ((int(row["id_deportista"]), row["nombre_deportista"]) for row in reader)
    statement = db.prepare(f"INSERT INTO {tabla_deportista} (id, nombre) VALUES (?, ?)")

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
        f"SELECT id, nombre FROM {tabla_deportista} WHERE id IN ?"
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
    cluster = db.cluster
    try:
        db.execute(f"DROP TABLE IF EXISTS {keyspace}.{tabla_deportista}")
    finally:
        db.shutdown()
        cluster.shutdown()

ejecutar(archivo_entrada, conexion)