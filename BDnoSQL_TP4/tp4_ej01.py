import csv
import os
import time
from datetime import datetime
from pymongo import MongoClient

# Ubicacion del archivo CSV con el contenido provisto por la catedra
# Ruta relativa a la carpeta del script, para ejecutarlo desde cualquier ubicacion
archivo_entrada = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'full_export.csv')
nombre_archivo_resultado_ejercicio = 'tp4_ej01_resultado.txt'

# Objeto de configuracion para conectarse a la base de datos usada en este ejercicio
conexion = {
    'mongourl': 'localhost',
    'mongopuerto': 27017
}

nombre_base_datos = 'iaaf'
nombre_coleccion_deportistas = 'deportistas'


# Carga de la coleccion. El reporte se genera desde un cliente de Mongo y la coleccion se conserva
# para los ejercicios siguientes. Tiempo de carga: aprox. 0,7 s (714 deportistas)
def ejecutar(file, conn):
    inicio_total = time.time()
    client = inicializar(conn)
    with open(file, "r", encoding="utf-8") as archivo_csv:
        lector_filas_csv = csv.DictReader(archivo_csv)
        print("Iniciando carga de registros a la base...")
        procesar_coleccion(client, lector_filas_csv)
    generar_reporte(client)
    finalizar(client)
    print("tiempo total en segundos")
    print(time.time() - inicio_total)


# Funcion que dado un archivo abierto y una linea, imprime por consola y guarda al final de archivo esa linea
def grabar_linea(archivo, linea):
    print(linea)
    archivo.write(str(linea) + '\n')


def inicializar(conn):
    cliente_mongo = MongoClient(conn["mongourl"], conn["mongopuerto"])
    # Borrado previo de la coleccion para que la carga sea repetible
    cliente_mongo[nombre_base_datos].drop_collection(nombre_coleccion_deportistas)
    return cliente_mongo


# Un documento por deportista, con el id de deportista como _id y el pais como subdocumento
def procesar_fila(fila):
    return {
        "_id": int(fila["id_deportista"]),
        "nombre": fila["nombre_deportista"],
        "fecha_nacimiento": datetime.strptime(fila["fecha_nacimiento"], "%Y-%m-%d"),
        "pais": {
            "id": int(fila["id_pais_deportista"]),
            "nombre": fila["nombre_pais_deportista"]
        }
    }


# Diccionario id > documento: el .csv repite al deportista en cada marca, 
# pero en el dicc se guarda una sola vez y crea su documento. Si el ID ya está en el dicc la fila se saltea.
# Luego, insercion de los deportistas con un unico insert_many
# Descartados: update_one con upsert por fila e insert_one (demasiadas operaciones), 
#  y un generador con set e islice, porque el código era menos legible.

def procesar_coleccion(client, lector_filas_csv):
    coleccion_deportistas = client[nombre_base_datos][nombre_coleccion_deportistas]
    deportistas_por_id = {}
    for fila in lector_filas_csv:
        id_deportista = int(fila["id_deportista"])
        if id_deportista not in deportistas_por_id:
            deportistas_por_id[id_deportista] = procesar_fila(fila)

    coleccion_deportistas.insert_many(list(deportistas_por_id.values()))
    print(str(len(deportistas_por_id)) + " deportistas insertados")


# Funcion que realiza el o los queries que resuelven el ejercicio, utilizando la base de datos.
def generar_reporte(client):
    # No se genera el reporte acá: la query se ejecuta desde un cliente de Mongo (ver tp4_ej01_query.txt)
    pass


# Funcion para el borrado de estructuras generadas para este ejercicio
def finalizar(client):
    # No se elimina la coleccion porque se utiliza en los ejercicios 2, 3 y 4
    client.close()


# Llamado a la ejecucion del programa
ejecutar(archivo_entrada, conexion)
