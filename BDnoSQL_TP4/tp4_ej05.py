import csv
import os
import time
from datetime import datetime
from pymongo import MongoClient

# Ubicacion del archivo CSV con el contenido provisto por la catedra
# Ruta relativa a la carpeta del script, para ejecutarlo desde cualquier ubicacion
archivo_entrada = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'full_export.csv')
nombre_archivo_resultado_ejercicio = 'tp4_ej05_resultado.txt'

# Objeto de configuracion para conectarse a la base de datos usada en este ejercicio
conexion = {
    'mongourl': 'localhost',
    'mongopuerto': 27017
}

nombre_base_datos = 'iaaf'
nombre_coleccion_participaciones = 'participaciones'


# Carga de la coleccion. El reporte se genera desde un cliente de Mongo. Tiempo de carga: aprox. 5 s.
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
    cliente_mongo[nombre_base_datos].drop_collection(nombre_coleccion_participaciones)
    return cliente_mongo


# Un documento por fila del CSV (participacion completa), desnormalizado en subdocumentos
def procesar_fila(fila):
    return {
        "deportista": {
            "id": int(fila["id_deportista"]),
            "nombre": fila["nombre_deportista"],
            "fecha_nacimiento": datetime.strptime(fila["fecha_nacimiento"], "%Y-%m-%d"),
            "pais": {
                "id": int(fila["id_pais_deportista"]),
                "nombre": fila["nombre_pais_deportista"]
            }
        },
        "especialidad": {
            "id": int(fila["id_especialidad"]),
            "nombre": fila["nombre_especialidad"],
            "tipo": {
                "id": int(fila["id_tipo_especialidad"]),
                "nombre": fila["nombre_tipo_especialidad"]
            }
        },
        "torneo": {
            "id": int(fila["id_torneo"]),
            "nombre": fila["nombre_torneo"],
            "ciudad": {
                "id": int(fila["id_ciudad_torneo"]),
                "nombre": fila["nombre_ciudad_torneo"]
            },
            "pais": {
                "id": int(fila["id_pais_torneo"]),
                "nombre": fila["nombre_pais_torneo"]
            }
        },
        "intento": int(fila["intento"]),
        "marca": int(fila["marca"])
    }


# Insercion masiva: insert_many recibe todas las filas y pymongo las envia en lotes
# Tiempo de carga: aprox. 5 s (161.403 participaciones)
def procesar_coleccion(client, lector_filas_csv):
    coleccion_participaciones = client[nombre_base_datos][nombre_coleccion_participaciones]
    resultado = coleccion_participaciones.insert_many(procesar_fila(fila) for fila in lector_filas_csv)
    print(str(len(resultado.inserted_ids)) + " documentos insertados")


# Funcion que realiza el o los queries que resuelven el ejercicio, utilizando la base de datos.
def generar_reporte(client):
    # No se genera el reporte acá: la query se ejecuta desde un cliente de Mongo (ver tp4_ej05_query.txt)
    pass


# Funcion para el borrado de estructuras generadas para este ejercicio
def finalizar(client):
    # No se elimina la coleccion porque se utiliza en los ejercicios 6 a 9
    client.close()


# Llamado a la ejecucion del programa
ejecutar(archivo_entrada, conexion)
