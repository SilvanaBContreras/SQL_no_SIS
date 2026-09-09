import csv
import redis

# Ubicacion del archivo CSV con el contenido provisto por la catedra
archivo_entrada = 'full_export.csv'
nombre_archivo_resultado_ejercicio = 'tp2_ej04.txt'

# Objeto de configuracion para conectarse a la base de datos usada en este ejercicio
conexion = {
    'redisurl': 'localhost',
    'redispuerto': 6379
}

# Funcion que dada la configuracion y ubicacion del archivo, carga la base de datos, genera el reporte, y borra la
# base de datos
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


# Funcion que dado un archivo abierto y una linea, imprime por consola y guarda al final de archivo esa linea
def grabar_linea(archivo, linea):
    print(linea)
    archivo.write(str(linea) + '\n')


def inicializar(conn):
    r = redis.Redis(conn["redisurl"], conn["redispuerto"], db=0, decode_responses=True)
    return r
    # crear db


# Funcion que dada una linea del archivo CSV (en forma de objeto) va a encargarse de insertar el (o los) objetos
# necesarios
# Debe ser implementada por el alumno

# =========================
# EJ. 4. Listar todos los id y nombre de los tipos de especialidad y la cantidad de especialidades asociadas
# a cada una. Para esto, es requerido la carga de dos estructuras separadas con la totalidad de los
# datos disponibles. En ambas estructuras se debe utilizar el id de tipo de especialidad como key.
# Pero en una se debe almacenar el nombre del tipo de especialidad y en la otra las especialidades
# asociadas.
# =========================

def procesar_fila(db, fila):
    id_especialidad = fila["id_especialidad"] 
    id_tipo_especialidad = fila["id_tipo_especialidad"] #key
    nombre_tipo_especialidad = fila["nombre_tipo_especialidad"]

    # Primera estructura: id del tipo → nombre del tipo
    db.set(
        "tipo_especialidad:" + id_tipo_especialidad,
        nombre_tipo_especialidad
    )

    # Segunda estructura: id del tipo → especialidades asociadas
    db.sadd(
        "especialidades_tipo:" + id_tipo_especialidad,
        id_especialidad
    )


# Funcion que realiza el o los queries que resuelven el ejercicio, utilizando la base de datos.
# Debe ser implementada por el alumno

def generar_reporte(db):
    archivo = open(
        nombre_archivo_resultado_ejercicio,
        "w",
        encoding="utf-8"
    )
    # Título descriptivo y encabezado de columnas al inicio del reporte
    titulo_reporte = "Tipos de especialidad y cantidad de especialidades asociadas"
    encabezado_columnas = "id_tipo_especialidad,nombre_tipo_especialidad,cantidad_especialidades"

    grabar_linea(archivo, titulo_reporte)
    grabar_linea(archivo, encabezado_columnas)

    claves = db.keys("tipo_especialidad:*")

    ids_tipos = []

    for clave in claves:
        id_tipo_especialidad = clave.split(":")[1]
        ids_tipos.append(id_tipo_especialidad)

    ids_tipos.sort(key=int)

    for id_tipo_especialidad in ids_tipos:
        nombre_tipo_especialidad = db.get(
            "tipo_especialidad:" + id_tipo_especialidad
        )

        cantidad_especialidades = db.scard(
            "especialidades_tipo:" + id_tipo_especialidad
        )

        linea = (
            id_tipo_especialidad + ","
            + nombre_tipo_especialidad + ","
            + str(cantidad_especialidades)
        )

        grabar_linea(archivo, linea)

    archivo.close()


# Funcion para el borrado de estructuras generadas para este ejercicio
def finalizar(db):
    db.flushdb()
    # Borrar la estructura de la base de datos


# Llamado a la ejecucion del programa
ejecutar(archivo_entrada, conexion)
