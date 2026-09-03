import redis

# ABRIR CLIENTE en powershell
# docker exec -it redis1 redis-cli
# salir de CLI
# exit

#prender apagar contenedor redis1
# docker start redis1
# docker stop redis1

db = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)

db.set("persona:1", "Silvana")
db.set("persona:2", "Ana")

print("Datos cargados")