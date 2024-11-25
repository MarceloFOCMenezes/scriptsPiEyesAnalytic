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

# Arquivo para salvar estado
STATE_FILE = "network_state.json"


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
    print(f"Conexoes Ativas: {len(conex_atv)}")
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
    bytesRecebidos = net.bytes_recv / 1e+6  # Convertendo para MB
    bytesEnviados = net.bytes_sent / 1e+6 # Convertendo para MB
    pacotesRecebidos = net.packets_recv
    pacotesEnviados = net.packets_sent
    return bytesRecebidos, bytesEnviados, pacotesRecebidos, pacotesEnviados

def carregarEstado():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as file:
            return json.load(file)
    return None


def salvarEstado(bytesRecebidos, bytesEnviados, pacotesRecebidos, pacotesEnviados):
    estado = {
        "bytesRecebidos": bytesRecebidos,
        "bytesEnviados": bytesEnviados,
        "pacotesRecebidos": pacotesRecebidos,
        "pacotesEnviados": pacotesEnviados
    }
    with open(STATE_FILE, "w") as file:
        json.dump(estado, file)

def calcularDiferencas(atual, anterior):
    return max(atual - anterior, 0)  # Garantir que a diferença não seja negativa

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
    estado = carregarEstado()
    inserir_ip(bd, idMaquina)

    if estado:
        prev_bytesRecebidos = estado["bytesRecebidos"]
        prev_bytesEnviados = estado["bytesEnviados"]
        prev_pacotesRecebidos = estado["pacotesRecebidos"]
        prev_pacotesEnviados = estado["pacotesEnviados"]
    else:
        # Primeira execução: inicializa estado com os valores capturados
        prev_bytesRecebidos, prev_bytesEnviados, prev_pacotesRecebidos, prev_pacotesEnviados = receberRede()
        salvarEstado(prev_bytesRecebidos, prev_bytesEnviados, prev_pacotesRecebidos, prev_pacotesEnviados)
        
    while True:
        bytesRecebidos, bytesEnviados, pacotesRecebidos, pacotesEnviados = receberRede()

        # Calcula diferenças
        diff_bytesRecebidos = calcularDiferencas(bytesRecebidos, prev_bytesRecebidos)
        diff_bytesEnviados = calcularDiferencas(bytesEnviados, prev_bytesEnviados)
        diff_pacotesRecebidos = calcularDiferencas(pacotesRecebidos, prev_pacotesRecebidos)
        diff_pacotesEnviados = calcularDiferencas(pacotesEnviados, prev_pacotesEnviados)

        # Calcula pacotes perdidos
        if diff_pacotesEnviados > 0:
            pacotesPerdidos = max((diff_pacotesEnviados - diff_pacotesRecebidos) / diff_pacotesEnviados * 100, 0)
        else:
            pacotesPerdidos = 0

        # Atualiza os valores anteriores
        prev_bytesRecebidos = bytesRecebidos
        prev_bytesEnviados = bytesEnviados
        prev_pacotesRecebidos = pacotesRecebidos
        prev_pacotesEnviados = pacotesEnviados

        # Salva o estado atual
        salvarEstado(prev_bytesRecebidos, prev_bytesEnviados, prev_pacotesRecebidos, prev_pacotesEnviados)
        
        latencia = medir_latencia()
        cpu = receberCpu()
        disco = receberDisco()
        ram = receberRam()
        conexoes = receberConexoes()
        inserirDados(idEmpresa,cpu, idMaquina, 1, bd)
        inserirDados(idEmpresa,ram, idMaquina, 2, bd)
        inserirDados(idEmpresa,disco, idMaquina, 3, bd)
        inserirDados(idEmpresa, diff_bytesRecebidos, idMaquina, 4, bd)
        inserirDados(idEmpresa, diff_bytesEnviados, idMaquina, 5, bd)
        inserirDados(idEmpresa, diff_pacotesEnviados, idMaquina, 6, bd)
        inserirDados(idEmpresa, diff_pacotesRecebidos, idMaquina, 7, bd)
        inserirDados(idEmpresa, conexoes, idMaquina,8, bd)
        inserirDados(idEmpresa, latencia, idMaquina, 9, bd)
        inserirDados(idEmpresa, pacotesPerdidos, idMaquina, 10, bd)
        
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
