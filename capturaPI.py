import os
import psutil
import time
from mysql.connector import Error, connect
from dotenv import load_dotenv

load_dotenv()

caminhoEnv = '.env'
idMaquina_key = 'ID_MAQUINA'
config = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME')
}

def configurarBanco():
    try:
        db = connect(**config)
        if db.is_connected():
            db_info = db.get_server_info()
            print("Connected to MySQL server version -", db_info)
            return db
    except Error as e:
        print("Error to connect with MySQL -", e)
        return None

def receberRam():
    mem = psutil.virtual_memory()
    print(f"Uso de RAM: {mem.percent}% ({mem.used / (1024 ** 3):.2f} GB)")
    return mem.percent

def receberDisco():
    disk = psutil.disk_usage('/')
    print(f"Uso de Disco: {disk.percent}% ({disk.used / (1024 ** 3):.2f} GB)")
    return disk.percent

def receberCpu():
    cpu_percent = psutil.cpu_percent()
    print(f"Uso Total da CPU: {cpu_percent}%")
    return cpu_percent

def receberRede():
    net = psutil.net_io_counters()
    byrecebidos = net.bytes_recv
    byenviados = net.bytes_sent
    return byrecebidos, byenviados

def inserirDados(dado, fkMaquina, fkRecurso, bd):
    with bd.cursor() as cursor:
        informar = (
            "INSERT INTO dado_capturado (registro, fkMaquina, fkRecurso) "
            "VALUES (%s, %s, %s)"
        )
        valores = [dado, fkMaquina, fkRecurso]
        cursor.execute(informar, valores)
        bd.commit()

def monitor_system(bd, idMaquina, interval=10):
    while True:
        bytesRecebidos, bytesEnviados = receberRede()
        cpu = receberCpu()
        disco = receberDisco()
        ram = receberRam()
        inserirDados(cpu, idMaquina, 1, bd)
        inserirDados(ram, idMaquina, 2, bd)
        inserirDados(disco, idMaquina, 3, bd)
        inserirDados(bytesRecebidos, idMaquina, 4, bd)
        inserirDados(bytesEnviados, idMaquina, 5, bd)
        time.sleep(interval)  # Intervalo em segundos

def main():
    idMaquina = os.getenv(idMaquina_key)
    if idMaquina is not None:
        print(f"Id da Máquina: {idMaquina}")
        bd = configurarBanco()
        
        if bd is None:
            print("Não foi possível conectar ao banco")
            return
        else:
            monitor_system(bd, idMaquina)
    else:
        print("Máquina não cadastrada!")

if __name__ == "__main__":
    main()
