import csv
import redis

archivo_entrada = 'full_export.csv'
nombre_archivo_resultado_ejercicio = 'tp2_ej01.txt'

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
    id_deportista = fila["id_deportista"]
    nombre_deportista = fila["nombre_deportista"]
    db.set(id_deportista, nombre_deportista)

def generar_reporte(db):
    archivo = open(nombre_archivo_resultado_ejercicio, "w", encoding="utf-8")

    titulo_reporte = "Nombre de deportistas segun Ids solicitados"
    encabezado_columnas = "id_deportista,nombre_deportista"
    grabar_linea(archivo, titulo_reporte)
    grabar_linea(archivo, encabezado_columnas)

    claves = db.keys("*")
    ids_solicitados = ["10", "20", "30"]

    for id_deportista in ids_solicitados:
        if id_deportista in claves:
            nombre_deportista = db.get(id_deportista)
            linea = id_deportista + "," + nombre_deportista
            grabar_linea(archivo, linea)
    archivo.close()

def finalizar(db):
    db.flushdb()

ejecutar(archivo_entrada, conexion)
