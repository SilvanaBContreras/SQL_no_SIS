import csv
import redis

archivo_entrada = 'full_export.csv'
nombre_archivo_resultado_ejercicio = 'tp2_ej05.txt'

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
    id_deportista = fila["id_deportista"] #key
    id_especialidad = fila["id_especialidad"] #key
    nombre_tipo_especialidad = fila["nombre_tipo_especialidad"]
    id_torneo = fila["id_torneo"]
    nombre_torneo = fila["nombre_torneo"]
    intento = fila["intento"]
    marca = fila["marca"]

    clave = f"clave_deportista_especialidad:{id_deportista}:{id_especialidad}"
    miembro = f"intento_idtorneo:{intento}:{id_torneo}"

    db.zadd(
        clave, {miembro:marca}
    )

    db.hset("nombre_torneo", id_torneo, nombre_torneo)
    db.hset("nombres_tipo_especialidad", id_especialidad, nombre_tipo_especialidad)

def generar_reporte(db):
    archivo = open(
        nombre_archivo_resultado_ejercicio,
        "w",
        encoding="utf-8"
    )
    titulo_reporte = "Mejor y peor marca de cada deportista"
    encabezado_columnas = "id_deportista,id_especialidad,nombre_torneo,intento,marca,tipo_marca"

    grabar_linea(archivo, titulo_reporte)
    grabar_linea(archivo, encabezado_columnas)

    claves = db.keys("clave_deportista_especialidad:*")

    claves.sort(key=lambda c: (int(c.split(":")[1]), int(c.split(":")[2])))

    for clave in claves:
        _, id_deportista, id_especialidad = clave.split(":")

        nombre_tipo_especialidad = db.hget("nombres_tipo_especialidad", id_especialidad)

        if nombre_tipo_especialidad == 'tiempo':
            mejor = db.zrange(clave, 0, 0, withscores=True)
            peor = db.zrevrange(clave, 0, 0, withscores=True)
        else:
            mejor = db.zrevrange(clave, 0, 0, withscores=True)
            peor = db.zrange(clave, 0, 0, withscores=True)

        clave_intento_torneo, marca = mejor[0]
        _, intento, id_torneo = clave_intento_torneo.split(":")
        nombre_torneo = db.hget("nombre_torneo", id_torneo)

        linea = (
            id_deportista + ","
            + id_especialidad + ","
            + nombre_torneo + ","
            + intento + ","
            + str(marca) + ","
            + "mejor"
        )
        grabar_linea(archivo, linea)

        clave_intento_torneo, marca = peor[0]
        _, intento, id_torneo = clave_intento_torneo.split(":")
        nombre_torneo = db.hget("nombre_torneo", id_torneo)

        linea = (
            id_deportista + ","
            + id_especialidad + ","
            + nombre_torneo + ","
            + intento + ","
            + str(marca) + ","
            + "peor"
        )
        grabar_linea(archivo, linea)

    archivo.close()

def finalizar(db):
    db.flushdb()

ejecutar(archivo_entrada, conexion)