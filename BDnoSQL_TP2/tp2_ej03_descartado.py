import csv
import redis

# Ubicacion del archivo CSV con el contenido provisto por la catedra
archivo_entrada = 'full_export.csv'
nombre_archivo_resultado_ejercicio = 'tp2_ej03.txt'

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

# ========================
# Listar los siguientes datos del deportista: id, nombre, fecha de nacimiento, y nombre del país de
# nacimiento para los deportistas con id 10, 20, 30 y 229. Además listar la cantidad de especialidades
# que cada deportista practica Es requerido que en la base de datos se encuentren los registros para
# todos los deportistas en primer lugar. Utilizar el tipo de dato HASH para almacenar la información
# del deportista y SET para las especialidades practicadas por cada uno.
# ========================

def procesar_fila(db, fila):
    id_deportista = fila["id_deportista"]
    nombre_deportista = fila["nombre_deportista"]
    fecha_nacimiento = fila["fecha_nacimiento"]
    nombre_pais_deportista = fila["nombre_pais_deportista"]
    nombre_especialidad = fila["nombre_especialidad"]
    db.hset("ficha:" + id_deportista, mapping = {"nombre_deportista": nombre_deportista, 
                                      "fecha_nacimiento": fecha_nacimiento,
                                      "nombre_pais_deportista": nombre_pais_deportista
                                      })

    db.sadd("especialidades:" + id_deportista,
        nombre_especialidad
    )

# Funcion que realiza el o los queries que resuelven el ejercicio, utilizando la base de datos.
# Debe ser implementada por el alumno

def generar_reporte(db):
    archivo = open(nombre_archivo_resultado_ejercicio, "w", encoding="utf-8")

    claves = db.keys("ficha:*")

    #claves.sort(key=int) #para que devuelva ordenados

    for clave in claves:
        id_deportista = clave.split(":")[1]
        
        if id_deportista in ["10", "20", "30", "229"]:

            ficha_deportista = db.hgetall(clave)
            especialidades = db.smembers (f"especialidades:{id_deportista}")

            linea = id_deportista + "," + ficha_deportista["nombre_deportista"] + "," + ficha_deportista["fecha_nacimiento"] + "," + ficha_deportista["nombre_pais_deportista"] + "," + str(len(especialidades))

            grabar_linea(archivo, linea)

    archivo.close()


# Funcion para el borrado de estructuras generadas para este ejercicio
def finalizar(db):
    db.flushdb()
    # Borrar la estructura de la base de datos


# Llamado a la ejecucion del programa
ejecutar(archivo_entrada, conexion)
