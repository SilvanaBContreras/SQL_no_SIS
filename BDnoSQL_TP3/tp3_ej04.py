import csv
from cassandra.cluster import Cluster
from cassandra.concurrent import execute_concurrent_with_args

archivo_entrada = 'full_export.csv'
nombre_archivo_resultado_ejercicio = 'tp3_ej04.txt'

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
    drop_table_query = """DROP TABLE IF EXISTS deportista_marcas"""
    session.execute(drop_table_query)
    print("Table dropped successfully!")

    # 4) Imprimir la mejor y peor marca de cada deportista indicando el torneo y el intento en el cuál la logró.
    # Teniendo en cuenta que un deportista puede practicar más de una especialidad.
    # La tabla queda ordenada por marca ascendente. La primera fila de cada particion es la marca minima.
    # La maxima se pide por cada par dando vuelta ese orden.

    # Create table
    create_table_query = """
    CREATE TABLE IF NOT EXISTS deportista_marcas (
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
    print("Table created successfully!")

    return session


def procesar_tabla(db, reader):
    rows = [
        (
            int(row["id_deportista"]),
            int(row["id_especialidad"]),
            row["nombre_deportista"],
            row["nombre_especialidad"],
            row["nombre_tipo_especialidad"],
            int(row["marca"]),
            int(row["id_torneo"]),
            row["nombre_torneo"],
            int(row["intento"]),
        )
        for row in reader
    ]
    statement = db.prepare("""
        INSERT INTO deportista_marcas (
            id_deportista, id_especialidad, nombre_deportista, nombre_especialidad,
            nombre_tipo_especialidad, marca, id_torneo, nombre_torneo, intento
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """)

    results = execute_concurrent_with_args(
        db,
        statement,
        rows,
        concurrency=1000,
        results_generator=False
    )

    for success, result in results:
        if not success:
            raise result


# 4) Imprimir la mejor y peor marca de cada deportista indicando el torneo y el intento en el cuál la logró.
# Teniendo en cuenta que un deportista puede practicar más de una especialidad.

def generar_reporte(db):
    # Con GROUP BY se obtiene el menor valor de marca por deportista y especialidad (la primera fila de cada particion es la marca minima)
    consulta_min = db.prepare("""
        SELECT id_deportista, nombre_deportista, id_especialidad, nombre_especialidad,
               nombre_tipo_especialidad, marca, id_torneo, nombre_torneo, intento
        FROM deportista_marcas
        GROUP BY id_deportista, id_especialidad
    """)
    marcas_min = {}
    for row in db.execute(consulta_min):
        marcas_min[(row.id_deportista, row.id_especialidad)] = row

    # Cassandra solo permite dar vuelta el orden completo de clustering dentro de una particion.
    consulta_max = db.prepare("""
        SELECT id_deportista, nombre_deportista, id_especialidad, nombre_especialidad,
               nombre_tipo_especialidad, marca, id_torneo, nombre_torneo, intento
        FROM deportista_marcas
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
    db.shutdown()


ejecutar(archivo_entrada, conexion)
