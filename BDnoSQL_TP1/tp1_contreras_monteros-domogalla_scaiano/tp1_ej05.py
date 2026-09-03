import csv

# Ubicacion del archivo CSV con el contenido provisto por la catedra
archivo_entrada = 'full_export.csv'
#nombre_archivo_resultado_ejercicio = 'tpY_ejXX.txt'

nombre_archivo_resultado_ejercicio = 'tp1_ej05.txt'

# Objeto de configuracion para conectarse a la base de datos usada en este ejercicio
conexion = []


# Funcion que dada la configuracion y ubicacion del archivo, carga la base de datos, genera el reporte, y borra la
# base de datos
def ejecutar(file, conn):
    db = inicializar(conn)
    df_filas = csv.DictReader(open(file, "r", encoding="utf-8"))
    for fila in df_filas:
        procesar_fila(db, fila)
    generar_reporte(db)
    finalizar(db)


# Funcion que dado un archivo abierto y una linea, imprime por consola y guarda al final de archivo esa linea
def grabar_linea(archivo, linea):
    print(linea)
    archivo.write(linea+'\n')


# Funcion para poner el codigo que cree las estructuras a usarse en el este ejercicio
# Debe ser implementada por el alumno
def inicializar(conn):
    return []
    # crear db


# Funcion que dada una linea del archivo CSV (en forma de objeto) va a encargarse de insertar el (o los) objetos
# necesarios
# Debe ser implementada por el alumno
#def procesar_fila(database, fila):
#    pass
    # insertar elemento en entidad para el ejercicio actual

def procesar_fila(database, fila):
    if fila["nombre_especialidad"] == "carrera 100 m" and fila["nombre_torneo"] == "Torneo de Argentina":
        resultado = (
            int(fila["marca"]),
            fila["nombre_torneo"],
            fila["nombre_especialidad"],
            fila["nombre_deportista"]
        )
        database.append(resultado)

# Funcion que realiza el o los queries que resuelven el ejercicio, utilizando la base de datos.
# Debe ser implementada por el alumno
#def generar_reporte(database):

    # archivo = open(nombre_archivo_resultado_ejercicio, 'w')
    # luego para cada linea generada como reporte:
    # grabar_linea(archivo, linea)
#    pass

def generar_reporte(database):
    archivo = open(nombre_archivo_resultado_ejercicio, 'w', encoding="utf-8")
    grabar_linea(
        archivo,
        "Podio de carrera 100 m en Torneo de Argentina:"
    )
    grabar_linea(
        archivo,
        "Torneo,Especialidad,Deportista,Marca"
    )
    database.sort()
    for resultado in database[:3]:
        linea = (
            resultado[1] + "," +
            resultado[2] + "," +
            resultado[3] + "," +
            str(resultado[0])
        )
        grabar_linea(archivo, linea)
    archivo.close()


# Funcion para el borrado de estructuras generadas para este ejercicio
# Debe ser implementada por el alumno
def finalizar(database):
    pass
    # Borrar la estructura de la base de datos


# Llamado a la ejecucion del programa
ejecutar(archivo_entrada, conexion)
