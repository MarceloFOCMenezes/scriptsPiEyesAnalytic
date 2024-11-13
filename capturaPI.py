import os
import psutil
import time
from mysql.connector import Error, connect
from dotenv import load_dotenv
import requests
import json

load_dotenv()

url = 'https://hooks.slack.com/services/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'

caminhoEnv = '.env'
idMaquina_key = 'ID_MAQUINA'
idEmpresa_key = 'ID_EMPRESA'
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
    return round(mem.percent,2)

def receberDisco():
    disk = psutil.disk_usage('/')
    print(f"Uso de Disco: {disk.percent}% ({disk.used / (1024 ** 3):.2f} GB)")
    return round(disk.percent,2)

def receberCpu():
    cpu_percent = psutil.cpu_percent()
    print(f"Uso Total da CPU: {cpu_percent}%")
    return round(cpu_percent,2)

def receberRede():
    net = psutil.net_io_counters()
    byrecebidos = net.bytes_recv
    byenviados = net.bytes_sent
    return byrecebidos, byenviados

def inserirDados(fkEmpresa, dado, fkMaquina, fkRecurso, bd):

    with bd.cursor() as cursor:
        resultado = cursor.execute(f"SELECT valorMetrica, r.nomeRecurso FROM metrica as m join recurso as r on m.fkRecurso = r.idRecurso WHERE fkEmpresa = {fkEmpresa} AND fkRecurso = {fkRecurso};")
        valorMetrica = cursor.fetchall()
        if len(valorMetrica)> 0 and valorMetrica[0][0]< dado:
            payload = {
                "text": "Alerta! ⚠️"
                f"\nO recurso: {valorMetrica[0][1]} \nPassou do limite: {valorMetrica[0][0]}\nChegando à {dado}",
                "username": "Bot de Alerta", 
                "icon_emoji": ":robot_face:" }
            
            response = requests.post(url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
            if response.status_code == 200:
                print("Mensagem enviada com sucesso!")
            else:
                print(f"Falha ao enviar mensagem. Status Code: {response.status_code}")
        informar = (
            
            "INSERT INTO dado_capturado (registro, fkMaquina, fkRecurso) "
            "VALUES (%s, %s, %s)"
        )
        valores = [dado, fkMaquina, fkRecurso]
        cursor.execute(informar, valores)
        bd.commit()

def monitor_system(bd, idMaquina,idEmpresa, interval=10):
    while True:
        bytesRecebidos, bytesEnviados = receberRede()
        cpu = receberCpu()
        disco = receberDisco()
        ram = receberRam()
        inserirDados(idEmpresa,cpu, idMaquina, 1, bd)
        inserirDados(idEmpresa,ram, idMaquina, 2, bd)
        inserirDados(idEmpresa,disco, idMaquina, 3, bd)
        inserirDados(idEmpresa,bytesRecebidos, idMaquina, 4, bd)
        inserirDados(idEmpresa,bytesEnviados, idMaquina, 5, bd)
        time.sleep(interval)  # Intervalo em segundos

def main():
    idMaquina = os.getenv(idMaquina_key)
    idEmpresa = os.getenv(idEmpresa_key)
    if idMaquina is not None:
        print(f"Id da Máquina: {idMaquina}")
        bd = configurarBanco()
        
        if bd is None:
            print("Não foi possível conectar ao banco")
            return
        else:
            monitor_system(bd, idMaquina, idEmpresa)
    else:
        print("Máquina não cadastrada!")

if __name__ == "__main__":
    main()
