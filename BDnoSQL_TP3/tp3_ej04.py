import csv
from cassandra.cluster import Cluster
from cassandra.concurrent import execute_concurrent, execute_concurrent_with_args

archivo_entrada = 'full_export.csv'
nombre_archivo_resultado_ejercicio = 'tp3_ej04.txt'

# Objeto de configuracion para conectarse a la base de datos usada en este ejercicio
conexion = {
    'cassandraurl': 'localhost',
    'cassandrapuerto': 9042
}

keyspace = "sports"
tabla_deportista_marcas = "deportista_marcas"

def ejecutar(file, conn):
    import time

    start = time.time()
    db = inicializar(conn)
    reader = csv.DictReader(open(file, "r", encoding="utf-8"))
    startbloque = time.time()
    print("Iniciando carga de registros a la base...")
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

    session.set_keyspace(keyspace)

    drop_table_query = f"""DROP TABLE IF EXISTS {tabla_deportista_marcas}"""
    session.execute(drop_table_query)

    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {tabla_deportista_marcas} (
        id_deportista int,
        id_especialidad int,
        nombre_deportista text,
        nombre_especialidad text,
        nombre_tipo_especialidad text,
        marca int,
        id_torneo int,
        nombre_torneo text,
        intento int,
        PRIMARY KEY ((id_deportista, id_especialidad), marca, id_torneo, intento)
    ) WITH CLUSTERING ORDER BY (marca ASC, id_torneo ASC, intento ASC);
    """
    session.execute(create_table_query)

    return session

def procesar_fila(fila, insertar):
    valores = (
        int(fila["id_deportista"]),
        int(fila["id_especialidad"]),
        fila["nombre_deportista"],
        fila["nombre_especialidad"],
        fila["nombre_tipo_especialidad"],
        int(fila["marca"]),
        int(fila["id_torneo"]),
        fila["nombre_torneo"],
        int(fila["intento"]),
    )
    return insertar, valores

def procesar_tabla(db, reader):
    import time

    insertar = db.prepare(f"""
        INSERT INTO {tabla_deportista_marcas} (
            id_deportista, id_especialidad, nombre_deportista, nombre_especialidad,
            nombre_tipo_especialidad, marca, id_torneo, nombre_torneo, intento
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """)
    solicitudes = (procesar_fila(fila, insertar) for fila in reader)
    count = 0
    startbloque = time.time()

    results = execute_concurrent(
        db,
        solicitudes,
        concurrency=1000,
        results_generator=True
    )

    for success, result in results:
        count += 1
        if not success:
            raise result
        if count % 10000 == 0:
            endbloque = time.time()
            tiempo = endbloque-startbloque
            print(str(count) + " en " + str(tiempo) + " segundos")
            startbloque = time.time()

def generar_reporte(db):
    consulta_min = db.prepare(f"""
        SELECT id_deportista, nombre_deportista, id_especialidad, nombre_especialidad,
               nombre_tipo_especialidad, marca, id_torneo, nombre_torneo, intento
        FROM {tabla_deportista_marcas}
        GROUP BY id_deportista, id_especialidad
    """)
    marcas_min = {}
    for row in db.execute(consulta_min):
        marcas_min[(row.id_deportista, row.id_especialidad)] = row

    consulta_max = db.prepare(f"""
        SELECT id_deportista, nombre_deportista, id_especialidad, nombre_especialidad,
               nombre_tipo_especialidad, marca, id_torneo, nombre_torneo, intento
        FROM {tabla_deportista_marcas}
        WHERE id_deportista = ? AND id_especialidad = ?
        ORDER BY marca DESC, id_torneo DESC, intento DESC
        LIMIT 1
    """)
    pares = [(row.id_deportista, row.id_especialidad) for row in marcas_min.values()]
    results_max = execute_concurrent_with_args(
        db,
        consulta_max,
        pares,
        concurrency=1000,
        results_generator=False
    )

    marcas_max = {}
    for (id_deportista, id_especialidad), (success, result) in zip(pares, results_max):
        if not success:
            raise result
        marcas_max[(id_deportista, id_especialidad)] = result.one()

    with open(nombre_archivo_resultado_ejercicio, "w", encoding="utf-8") as archivo:
        titulo_reporte = "Mejor y peor marca por deportista y especialidad"
        encabezado_columnas = "id_deportista, nombre_deportista, id_especialidad, nombre_especialidad, tipo_especialidad, marca_mejor, id_torneo_mejor, torneo_mejor, intento_mejor, marca_peor, id_torneo_peor, torneo_peor, intento_peor"
        grabar_linea(archivo, titulo_reporte)
        grabar_linea(archivo, encabezado_columnas)

        for clave in sorted(marcas_min):
            menor = marcas_min[clave]
            mayor = marcas_max[clave]
            if menor.nombre_tipo_especialidad == "tiempo":
                mejor, peor = menor, mayor
            else:
                mejor, peor = mayor, menor
            grabar_linea(
                archivo,
                f"{menor.id_deportista}, {menor.nombre_deportista}, {menor.id_especialidad}, {menor.nombre_especialidad}, {menor.nombre_tipo_especialidad}, {mejor.marca}, {mejor.id_torneo}, {mejor.nombre_torneo}, {mejor.intento}, {peor.marca}, {peor.id_torneo}, {peor.nombre_torneo}, {peor.intento}"
            )

def finalizar(db):
    cluster = db.cluster
    try:
        db.execute(f"DROP TABLE IF EXISTS {keyspace}.{tabla_deportista_marcas}")
    finally:
        db.shutdown()
        cluster.shutdown()

ejecutar(archivo_entrada, conexion)
