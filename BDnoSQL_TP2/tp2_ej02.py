import csv
import redis
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

archivo_entrada = BASE_DIR / 'full_export.csv'
nombre_archivo_resultado_ejercicio = BASE_DIR / 'tp2_ej02.txt'

conexion = {
    'redisurl': 'localhost',
    'redispuerto': 6379
}

ids_deportista_cargados = set()

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
        if 0 == count % 100:
            endbloque = time.time()
            tiempo = endbloque - startbloque
            print(str(count) + " en " + str(tiempo) + " segundos")
            startbloque = time.time()
    generar_reporte(db)
    finalizar(db)
    end = time.time()
    print("tiempo total en segundos")
    print(end - start)


def grabar_linea(archivo, linea):
    print(linea)
    archivo.write(str(linea) + '\n')

def inicializar(conn):
    r = redis.Redis(conn["redisurl"], conn["redispuerto"], db=0, decode_responses=True)
    return r

def procesar_fila(db, fila):
    id_deportista = fila["id_deportista"]

    if id_deportista in ids_deportista_cargados:
        return

    nombre_deportista = fila["nombre_deportista"]
    fecha_nacimiento = fila["fecha_nacimiento"]
    nombre_pais_deportista = fila["nombre_pais_deportista"]

    db.hset("deportista:" + id_deportista, mapping = {"nombre_deportista": nombre_deportista,
                                      "fecha_nacimiento": fecha_nacimiento,
                                      "nombre_pais_deportista": nombre_pais_deportista})
    ids_deportista_cargados.add(id_deportista)


def generar_reporte(db):
    archivo = open(
        nombre_archivo_resultado_ejercicio,
        "w",
        encoding="utf-8"
    )

    titulo_reporte = "Datos de los deportistas según el id solicitado"

    encabezado_columnas = (
        "id_deportista,nombre_deportista,"
        "fecha_nacimiento,nombre_pais_deportista"
    )

    grabar_linea(archivo, titulo_reporte)
    grabar_linea(archivo, encabezado_columnas)

    ids_solicitados = ["10", "20", "30"]

    for id_deportista in ids_solicitados:
        ficha_deportista = db.hgetall("deportista:" + id_deportista)

        linea = (
            id_deportista + ","
            + ficha_deportista["nombre_deportista"] + ","
            + ficha_deportista["fecha_nacimiento"] + ","
            + ficha_deportista["nombre_pais_deportista"]
        )

        grabar_linea(archivo, linea)

    archivo.close()


def finalizar(db):
    db.flushdb()

ejecutar(archivo_entrada, conexion)
