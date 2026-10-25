import csv
from cassandra.cluster import Cluster
from cassandra.concurrent import execute_concurrent_with_args

archivo_entrada = 'full_export.csv'
nombre_archivo_resultado_ejercicio = 'tp3_ej02.txt'

# Objeto de configuracion para conectarse a la base de datos usada en este ejercicio
conexion = {
    'cassandraurl': 'localhost',
    'cassandrapuerto': 9042
}

keyspace = "sports"
tabla_deportista_especialidad = "deportista_especialidad"

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

    session.set_keyspace(keyspace)

    drop_table_query = f"""DROP TABLE IF EXISTS {tabla_deportista_especialidad}"""
    session.execute(drop_table_query)
    print("Table dropped successfully!")

    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {tabla_deportista_especialidad} (
        id_deportista INT PRIMARY KEY,
        nombre_deportista TEXT,
        fecha_nacimiento DATE,
        id_pais_nacimiento INT,
        nombre_pais_nacimiento TEXT,
        especialidades SET<TEXT>
    );
    """
    session.execute(create_table_query)
    print("Table created successfully!")

    return session

def procesar_tabla(db, reader):
    rows = ((row["nombre_deportista"], row["fecha_nacimiento"], int(row["id_pais_deportista"]), row["nombre_pais_deportista"], {row["nombre_especialidad"]}, int(row["id_deportista"])) for row in reader)
    statement = db.prepare(f"""
        UPDATE {tabla_deportista_especialidad}
        SET nombre_deportista= ?,
            fecha_nacimiento = ?,
            id_pais_nacimiento = ?,
            nombre_pais_nacimiento = ?,
            especialidades = especialidades + ?
        WHERE id_deportista = ?
        """)

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
        f"""
        SELECT id_deportista, nombre_deportista, fecha_nacimiento, id_pais_nacimiento, nombre_pais_nacimiento, especialidades
        FROM {tabla_deportista_especialidad}
        WHERE id_deportista IN ?
        """
    )
    ids = [10, 20, 30]
    rows = db.execute(prepared_query, (ids,))

    with open(nombre_archivo_resultado_ejercicio, "w", encoding="utf-8") as archivo:
        titulo_reporte = "Deportistas con ID 10, 20 y 30"
        encabezado_columnas = "id_deportista, nombre_deportista, fecha_nacimiento, id_pais_nacimiento, nombre_pais_nacimiento, especialidades"
        grabar_linea(archivo, titulo_reporte)
        grabar_linea(archivo, encabezado_columnas)

        for row in rows:
            for especialidad in sorted(row.especialidades):
                grabar_linea(archivo, f"{row.id_deportista}, {row.nombre_deportista}, {row.fecha_nacimiento}, {row.id_pais_nacimiento}, {row.nombre_pais_nacimiento}, {especialidad}")

def finalizar(db):
    cluster = db.cluster
    try:
        db.execute(f"DROP TABLE IF EXISTS {keyspace}.{tabla_deportista_especialidad}")
    finally:
        db.shutdown()
        cluster.shutdown()

ejecutar(archivo_entrada, conexion)