import csv
import redis

archivo_entrada = 'BDnoSQL_TP2/full_export.csv'
nombre_archivo_resultado_ejercicio = 'BDnoSQL_TP2/tp2_ej03.txt'

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


ids_deportista_cargados = set()

def procesar_fila(db, fila):
    id_deportista = fila["id_deportista"]
    id_especialidad = fila["id_especialidad"]

    if id_deportista not in ids_deportista_cargados:
        nombre_deportista = fila["nombre_deportista"]
        fecha_nacimiento = fila["fecha_nacimiento"]
        nombre_pais_deportista = fila["nombre_pais_deportista"]

        db.hset(
            id_deportista,
            mapping={
                "id_deportista": id_deportista,
                "nombre_deportista": nombre_deportista,
                "fecha_nacimiento": fecha_nacimiento,
                "nombre_pais_deportista": nombre_pais_deportista
            }
        )
        ids_deportista_cargados.add(id_deportista)

    db.sadd(
        "especialidades:" + id_deportista,
        id_especialidad
    )

def generar_reporte(db):
    archivo = open(
        nombre_archivo_resultado_ejercicio,
        "w",
        encoding="utf-8"
    )

    titulo_reporte = "Datos y cantidad de especialidades de los deportistas según el id solicitado"
    encabezado_columnas = "id_deportista,nombre_deportista,fecha_nacimiento,nombre_pais_deportista,cantidad_especialidades"
    grabar_linea(archivo, titulo_reporte)
    grabar_linea(archivo, encabezado_columnas)


    ids_solicitados = ["10", "20", "30", "229"]

    for id_deportista in ids_solicitados:
        ficha_deportista = db.hgetall(id_deportista)

        cantidad_especialidades = db.scard(
            "especialidades:" + id_deportista
        )

        linea = (
            ficha_deportista["id_deportista"] + ","
            + ficha_deportista["nombre_deportista"] + ","
            + ficha_deportista["fecha_nacimiento"] + ","
            + ficha_deportista["nombre_pais_deportista"] + ","
            + str(cantidad_especialidades)
        )

        grabar_linea(archivo, linea)

    archivo.close()

def finalizar(db):
    db.flushdb()

ejecutar(archivo_entrada, conexion)
