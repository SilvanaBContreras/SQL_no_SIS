import csv
import redis
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

archivo_entrada = BASE_DIR / 'full_export.csv'
nombre_archivo_resultado_ejercicio = BASE_DIR / 'tp2_ej04.txt'

conexion = {
    'redisurl': 'localhost',
    'redispuerto': 6379
}

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
    id_especialidad = fila["id_especialidad"] 
    id_tipo_especialidad = fila["id_tipo_especialidad"] #key
    nombre_tipo_especialidad = fila["nombre_tipo_especialidad"]

    db.set(
        "nombre_tipo_especialidad:" + id_tipo_especialidad,
        nombre_tipo_especialidad
    )

    db.sadd(
        "id_especialidad:" + id_tipo_especialidad,
        id_especialidad
    )

def generar_reporte(db):
    archivo = open(
        nombre_archivo_resultado_ejercicio,
        "w",
        encoding="utf-8"
    )

    titulo_reporte = (
        "Tipos de especialidad y cantidad de especialidades asociadas"
    )

    encabezado_columnas = (
        "id_tipo_especialidad,nombre_tipo_especialidad,"
        "cantidad_especialidades"
    )

    grabar_linea(archivo, titulo_reporte)
    grabar_linea(archivo, encabezado_columnas)

    claves = db.keys("nombre_tipo_especialidad:*")

    ids_tipos = []

    for clave in claves:
        id_tipo_especialidad = clave.split(":")[1]
        ids_tipos.append(id_tipo_especialidad)

    ids_tipos.sort(key=int)

    for id_tipo_especialidad in ids_tipos:
        nombre_tipo_especialidad = db.get(
            "nombre_tipo_especialidad:" + id_tipo_especialidad
        )

        cantidad_especialidades = db.scard(
            "id_especialidad:" + id_tipo_especialidad
        )

        linea = (
            id_tipo_especialidad + ","
            + nombre_tipo_especialidad + ","
            + str(cantidad_especialidades)
        )

        grabar_linea(archivo, linea)

    archivo.close()

def finalizar(db):
    db.flushdb()

ejecutar(archivo_entrada, conexion)
