import csv
import redis

archivo_entrada = 'full_export.csv'
nombre_archivo_resultado_ejercicio = 'tp2_ej07.txt'

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
    # crear db

def procesar_fila(db, fila):
    id_deportista = fila["id_deportista"]
    nombre_deportista = fila["nombre_deportista"]
    id_especialidad = fila["id_especialidad"]
    nombre_especialidad = fila["nombre_especialidad"]
    nombre_tipo_especialidad = fila["nombre_tipo_especialidad"]
    id_torneo = fila["id_torneo"]
    nombre_torneo = fila["nombre_torneo"]
    intento = fila["intento"]
    marca = fila["marca"]

    clave = f"id_especialidad_id_torneo:{id_especialidad}:{id_torneo}"
    miembro = f"intento_id_deportista:{intento}:{id_deportista}"

    db.zadd(
        clave, {miembro:marca}
    )

    db.hset("nombre_deportista", id_deportista, nombre_deportista)
    db.hset("nombre_especialidad", id_especialidad, nombre_especialidad)
    db.hset("nombre_tipo_especialidad", id_especialidad, nombre_tipo_especialidad)
    db.hset("nombre_torneo", id_torneo, nombre_torneo)

def generar_reporte(db):
    archivo = open(
        nombre_archivo_resultado_ejercicio,
        "w",
        encoding="utf-8"
    )

    titulo_reporte = "Top 3 anual por especialidad"
    encabezado_columnas = "nombre_torneo,nombre_especialidad,nombre_deportista,intento,marca,posicion_podio,"

    grabar_linea(archivo, titulo_reporte)
    grabar_linea(archivo, encabezado_columnas)

    claves = db.keys("id_especialidad_id_torneo:*")

    especialidades_torneo = []
    for clave in claves:
        _, id_especialidad, id_torneo = clave.split(":")
        nombre_especialidad = db.hget("nombre_especialidad", id_especialidad)
        nombre_torneo = db.hget("nombre_torneo",id_torneo)
        especialidades_torneo.append((nombre_especialidad, id_especialidad, nombre_torneo, id_torneo, clave))

    especialidades_torneo.sort(key=lambda x: (x[2], x[0]))  # orden alfabético por nombre_especialidad

    for nombre_especialidad, id_especialidad, nombre_torneo, id_torneo, clave in especialidades_torneo:
        nombre_tipo_especialidad = db.hget("nombre_tipo_especialidad", id_especialidad)

        if nombre_tipo_especialidad == 'tiempo':
            mejor = db.zrange(clave, 0, 2, withscores=True)
        else:
            mejor = db.zrevrange(clave, 0, 2, withscores=True)

        for i in range(0, 3):
            intento_id_deportista, marca = mejor[i]
            _, intento, id_deportista = intento_id_deportista.split(":")
            nombre_deportista = db.hget("nombre_deportista", id_deportista)

            linea = (
                nombre_torneo + ","
                + nombre_especialidad + ","
                + nombre_deportista + ","
                + str(intento) + ","
                + str(marca) + ","
                + str(i + 1)
            )
            grabar_linea(archivo, linea)

    archivo.close()

def finalizar(db):
    db.flushdb()

ejecutar(archivo_entrada, conexion)
