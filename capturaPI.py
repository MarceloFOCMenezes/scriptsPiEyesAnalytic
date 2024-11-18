import os
import psutil
import time
from mysql.connector import Error, connect
from dotenv import load_dotenv
import requests
import json
import time
from scapy.all import IP, ICMP, sr1
import socket

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

def receberConexoes():
    conex = psutil.net_connections(kind = 'inet')
    conex_atv = [conn for conn in conex if conn.status == 'ESTABLISHED']
    return len(conex_atv)

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

def obter_ip_local():
    try: 
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((os.getenv('DB_HOST'), 8080))

        ip_local = s.getsockname()[0]
        s.close()

        return ip_local
    except Exception as e:
        print(f"Erro ao obter ip: {e}")
        return None

def medir_latencia(host = os.getenv('DB_HOST')):
    pacote = IP(dst=host)/ICMP()

    inicio = time.time()

    resposta = sr1(pacote, timeout=2, verbose=0)

    fim = time.time()

    if resposta:
        latencia = (fim - inicio) * 1000

        print(f"Latencia da Rede: {(latencia):.2f}ms")
        return round(latencia,2)
    else:
        return None


def inserirDados(fkEmpresa, dado, fkMaquina, fkRecurso, bd):

    with bd.cursor() as cursor:
        resultado = cursor.execute(f"SELECT valorMetrica, r.nomeRecurso FROM metrica as m join recurso as r on m.fkRecurso = r.idRecurso WHERE fkEmpresa = {fkEmpresa} AND fkRecurso = {fkRecurso};")
        valorMetrica = cursor.fetchall()
        if len(valorMetrica) > 0 and valorMetrica[0][0]< dado:
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

def inserir_ip(bd, idMaquina):
    with bd.cursor() as cursor:
        ip_local = obter_ip_local()
        informar = ("INSERT INTO log_ip (ip, fkMaquina)"
                                   "VALUES (%s, %s)")
        valores = [ip_local, idMaquina]
        cursor.execute(informar, valores)
        bd.commit()
        

def monitor_system(bd, idMaquina,idEmpresa, interval=10):
    inserir_ip(bd, idMaquina)
    while True:
        bytesRecebidos, bytesEnviados = receberRede()
        latencia = medir_latencia()
        cpu = receberCpu()
        disco = receberDisco()
        ram = receberRam()
        conexoes = receberConexoes()
        inserirDados(idEmpresa,cpu, idMaquina, 1, bd)
        inserirDados(idEmpresa,ram, idMaquina, 2, bd)
        inserirDados(idEmpresa,disco, idMaquina, 3, bd)
        inserirDados(idEmpresa,bytesRecebidos, idMaquina, 4, bd)
        inserirDados(idEmpresa,bytesEnviados, idMaquina, 5, bd)
        inserirDados(idEmpresa, conexoes, idMaquina,8, bd)
        inserirDados(idEmpresa, latencia, idMaquina, 9, bd)
        
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
