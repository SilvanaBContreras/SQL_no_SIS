import csv
import sys

from cassandra.concurrent import execute_concurrent
from cassandra.cluster import Cluster

archivo_entrada = "full_export.csv"
nombre_archivo_resultado_ejercicio = "tp3_ej06.txt"

conexion = {
    "cassandraurl": "localhost",
    "cassandrapuerto": 9042,
}

keyspace = "tp3_ej06"
tabla_podio = "podio_anual"

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
    archivo.write(str(linea) + "\n")

def inicializar(conn):
    cluster = Cluster(
        contact_points=[conn["cassandraurl"]],
        port=conn["cassandrapuerto"],
    )

    try:
        session = cluster.connect()

        session.execute(
            f"""
            CREATE KEYSPACE IF NOT EXISTS {keyspace}
            WITH replication = {{
                'class': 'SimpleStrategy',
                'replication_factor': 1
            }}
            """
        )

        session.set_keyspace(keyspace)

        session.execute(f"DROP TABLE IF EXISTS {tabla_podio}")

        session.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {tabla_podio} (
                id_torneo int,
                id_especialidad int,
                marca int,
                marca_orden int,
                id_deportista int,
                intento int,
                nombre_torneo text,
                nombre_especialidad text,
                nombre_deportista text,

                PRIMARY KEY (
                    (id_torneo, id_especialidad),
                    marca_orden,
                    id_deportista,
                    intento
                )
            ) WITH CLUSTERING ORDER BY (
                marca_orden ASC,
                id_deportista ASC,
                intento ASC
            )
            """
        )

        return session

    except Exception:
        cluster.shutdown()
        raise

def procesar_fila(fila, insertar):
    # Cada fila representa un intento y mantiene sus identificadores para que
    # distintos intentos, incluso del mismo deportista, ocupen filas propias.
    valores = (
        int(fila["id_torneo"]),
        int(fila["id_especialidad"]),
        int(fila["marca"]),
        int(fila["marca"]) if fila["nombre_tipo_especialidad"] == "tiempo" else -int(fila["marca"]),
        int(fila["id_deportista"]),
        int(fila["intento"]),
        fila["nombre_torneo"],
        fila["nombre_especialidad"],
        fila["nombre_deportista"],
    )

    return insertar, valores

def procesar_tabla(db, reader):
    import time

    # Se preparan los INSERT una sola vez, sin variables globales.
    columnas = (
        "id_torneo, id_especialidad, marca, marca_orden, id_deportista, intento, "
        "nombre_torneo, nombre_especialidad, nombre_deportista"
    )
    valores = "?, ?, ?, ?, ?, ?, ?, ?, ?"
    insertar_marca = db.prepare(
        f"INSERT INTO {tabla_podio} ({columnas}) VALUES ({valores})"
    )
    # El generador evita guardar todo el CSV en memoria.
    solicitudes = (
        procesar_fila(fila, insertar_marca)
        for fila in reader
    )
    count = 0
    startbloque = time.time()
    error = None
    # Hasta 100 inserciones en curso para no esperar una por una.
    for success, detalle in execute_concurrent(
        db,
        solicitudes,
        concurrency=100,
        raise_on_first_error=False,
        results_generator=True,
    ):
        count += 1
        if not success and error is None:
            error = detalle
        if count % 10000 == 0:
            endbloque = time.time()
            tiempo = endbloque-startbloque
            print(str(count) + " en " + str(tiempo) + " segundos")
            startbloque = time.time()
    # Se revisan todas las respuestas antes de generar el reporte.
    if error is not None:
        raise error

def generar_reporte(db):
    with open(nombre_archivo_resultado_ejercicio, "w", encoding="utf-8") as archivo:
        grabar_linea(
            archivo,
            "id_torneo, nombre_torneo, id_especialidad, nombre_especialidad, "
            "posicion, id_deportista, nombre_deportista, intento, marca",
        )

        pares = db.execute(
            f"""
            SELECT DISTINCT id_torneo, id_especialidad
            FROM {tabla_podio}
            """
        )

        mejores_por_par = db.prepare(
            f"""
            SELECT id_torneo, id_especialidad, marca, id_deportista, intento,
                   nombre_torneo, nombre_especialidad, nombre_deportista
            FROM {tabla_podio}
            WHERE id_torneo = ? AND id_especialidad = ?
            LIMIT 3
            """
        )

        for par in pares:
            filas = db.execute(
                mejores_por_par,
                (par.id_torneo, par.id_especialidad),
            )

            posicion = 0

            for fila in filas:
                posicion += 1

                grabar_linea(
                    archivo,
                    f"{fila.id_torneo}, {fila.nombre_torneo}, "
                    f"{fila.id_especialidad}, {fila.nombre_especialidad}, "
                    f"{posicion}, {fila.id_deportista}, "
                    f"{fila.nombre_deportista}, {fila.intento}, {fila.marca}",
                )

def finalizar(db):
    cluster = db.cluster
    try:
        db.execute(f"DROP TABLE IF EXISTS {keyspace}.{tabla_podio}")
    finally:
        db.shutdown()
        cluster.shutdown()

if __name__ == "__main__":
    ejecutar(archivo_entrada, conexion)