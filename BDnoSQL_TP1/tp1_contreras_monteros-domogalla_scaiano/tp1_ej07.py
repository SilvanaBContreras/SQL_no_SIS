import csv

# Ubicacion del archivo CSV con el contenido provisto por la catedra
archivo_entrada = 'full_export.csv'
#nombre_archivo_resultado_ejercicio = 'tpY_ejXX.txt'

nombre_archivo_resultado_ejercicio = 'tp1_ej07.txt'

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


#como son diferentes especialidades atención a las marcas qué es mejor
def procesar_fila(database, fila):
    marca = int(fila["marca"])
    if fila["nombre_tipo_especialidad"] == "tiempo":
        marca_orden = marca
    else:
        marca_orden = -marca
    resultado = (
    fila["nombre_especialidad"],
    marca_orden,
    fila["nombre_deportista"],
    fila["nombre_torneo"],
    marca)
    database.append(resultado)

# Funcion que realiza el o los queries que resuelven el ejercicio, utilizando la base de datos.
# Debe ser implementada por el alumno
#def generar_reporte(database):

    # archivo = open(nombre_archivo_resultado_ejercicio, 'w')
    # luego para cada linea generada como reporte:
    # grabar_linea(archivo, linea)
#    pass

def generar_reporte(database):
    archivo = open(
        nombre_archivo_resultado_ejercicio, 'w', encoding="utf-8"
    )
    grabar_linea(
        archivo,
        "Podio por especialidad en todo el año:"
    )
    grabar_linea(
        archivo,
        "Torneo,Especialidad,Deportista,Marca"
    )
    grabar_linea(
        archivo,
        "Criterio de desempate: ante igual marca, se ordena alfabéticamente por deportista."
    )
    database.sort()
    especialidad_anterior = ""
    deportistas_podio = []

    for resultado in database:
        especialidad = resultado[0]
        deportista = resultado[2]
        if especialidad != especialidad_anterior:
            especialidad_anterior = especialidad
            deportistas_podio = []
        if deportista not in deportistas_podio and len(deportistas_podio) < 3:
            deportistas_podio.append(deportista)

            linea = (
                 resultado[0] + "," +
                 resultado[3] + "," +
                resultado[2] + "," +
                str(resultado[4]) )
            grabar_linea(archivo, linea)
    archivo.close()


# Funcion para el borrado de estructuras generadas para este ejercicio
# Debe ser implementada por el alumno
def finalizar(database):
    pass
    # Borrar la estructura de la base de datos


# Llamado a la ejecucion del programa
ejecutar(archivo_entrada, conexion)
