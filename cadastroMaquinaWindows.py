import os
from mysql.connector import connect, Error
from dotenv import load_dotenv, set_key
import cpuinfo
import psutil
import socket
import wmi as w 
import requests
import json





wmi = w.WMI()


load_dotenv()

url = os.getenv('URL')

caminhoEnv = '.env'
idEmpresa_key = 'ID_EMPRESA'
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
            print ("Connected to MySQL server version -", db_info)
            return db                                                                                                   
    except Error as e:
        print("Error to conect with MySQL -", e)
        return None
    
def selectIdEmpresa(db, codigoSeguranca):
    with db.cursor() as cursor:
        resultado = cursor.execute(f"SELECT idEmpresa,razaoSocial FROM empresa WHERE codSeg = {codigoSeguranca}")
        empresaId = cursor.fetchall()
        if(len(empresaId) > 0):
            print(f"Empresa: {empresaId[0][1]}")
            resultadoEmpresaId = empresaId[0]
            set_key(caminhoEnv,idEmpresa_key,str(resultadoEmpresaId[0]))
            return resultadoEmpresaId[0]
        else:
            print("O codigo de seguranca invalido")
            return None


def cadastrarMaquina(db,nomeMaquina, EmpresaId):
    with db.cursor() as cursor:
        resultado = cursor.execute(f"SELECT idMaquina FROM maquina ORDER BY idMaquina DESC LIMIT 1")
        qtdMaquinaRaw = cursor.fetchall()
        idMaquina = (qtdMaquinaRaw[0])[0]
        query= ("INSERT INTO maquina (idMaquina, nomeMaquina, situacao, fkEmpresa, fkPrioridade) VALUES" +
                "(%s, %s, 'Ativo', %s, 3)")
        valor = [idMaquina+1, nomeMaquina ,EmpresaId]

        cursor.execute(query, valor)
        db.commit()
        print("Maquina Cadastrada com sucesso!")
        set_key(caminhoEnv,idMaquina_key, str(idMaquina+1))
        cursor.close()
        return idMaquina+1

def vincular(db, MaquinaId, IdRecurso):
    with db.cursor() as cursor:
        vincular = ("INSERT INTO maquina_recurso (fkMaquina, fkRecurso) VALUES"+
                 "(%s, %s)")
        valor = [MaquinaId, IdRecurso]
        cursor.execute(vincular, valor)
        db.commit()
        resultado = cursor.execute("SELECT LAST_INSERT_ID()")
        idVinculadoRaw = cursor.fetchall()
        idVinculado = (idVinculadoRaw[0])[0]
        cursor.close()
        return idVinculado

def informar(db, valorAtributo, idVinculado, idAtributo):
    with db.cursor() as cursor:
        informar = ("INSERT INTO atributo_maquina_recurso (valor, fkAtributo, fkMaquinaRecurso) VALUES" +
                    "(%s, %s, %s)")
        valores = [valorAtributo, idAtributo, idVinculado]
        cursor.execute(informar,valores)
        db.commit()
        cursor.close()


def cadastrarCpu(db, MaquinaId):
    processador = cpuinfo.get_cpu_info()
    nucleoFisico = psutil.cpu_count(logical=False)
    modelo = processador.get('brand_raw', 'Desconhecido')
    fabricante = processador.get('vendor_id_raw', 'Desconhecido')
    velocidade = processador.get('hz_advertised_friendly')
    nucleos = processador.get('count')
    threads = nucleoFisico
    idVinculado =  vincular(db, MaquinaId, 1)
    print(idVinculado)
    informar( db, modelo, idVinculado, 1)
    informar( db, fabricante, idVinculado, 2)
    informar( db, velocidade, idVinculado, 3)
    informar( db, nucleos, idVinculado, 5)
    informar( db, threads, idVinculado, 4)

def cadastrarRam(db, MaquinaId):
        ram = wmi.Win32_PhysicalMemory()
        for r in ram:
            capacidade = int(r.Capacity)/(1024**3)
            velocidade = r.speed
            fabricante = r.Manufacturer if hasattr(r, 'Manufacturer') else "Desconhecido"
    
        idVinculado =  vincular(db, MaquinaId, 2)
        informar( db, fabricante, idVinculado, 1)
        informar( db, velocidade, idVinculado, 3)
        informar( db, capacidade, idVinculado, 6)

def cadastrarDisco(db, MaquinaId):
    disco =  wmi.Win32_LogicalDisk()
    for d in disco:
        fabricante = d.Manufacturer if hasattr(d, 'Manufacturer') else "Desconhecido"
        modelo = getattr(d, 'Model', 'Modelo Desconhecido')
        capacidade  =  int(d.Size) / (1024**3)
        idVinculado =  vincular(db, MaquinaId, 3)
        informar( db, fabricante, idVinculado, 1)
        informar( db, modelo, idVinculado, 2)
        informar( db, round(capacidade,2), idVinculado, 6)

def cadastrarRecursoRede(db, idMaquina):
    vincular(db, idMaquina, 4)
    vincular(db, idMaquina, 5)
    vincular(db, idMaquina, 6)
    vincular(db, idMaquina, 7)
    vincular(db, idMaquina, 8)
    vincular(db, idMaquina, 9)

def main():
    EmpresaId = os.getenv(idEmpresa_key)
    MaquinaId = os.getenv(idMaquina_key)
    if EmpresaId is None and MaquinaId is None:
        codigoSeguranca = input("Insira o codigo de seguranca:")
        db = configurarBanco()
        if db is None:
            print("Nao foi possivel conectar ao banco")
            return
        else:
            idEmpresa = selectIdEmpresa(db, codigoSeguranca)
            if idEmpresa != None:
                nomeMaquina = socket.gethostname()
                idMaquina = cadastrarMaquina(db, nomeMaquina, idEmpresa)
                cadastrarRecursoRede(db,idMaquina)
                cadastrarCpu(db, idMaquina)
                cadastrarRam(db, idMaquina)              
                cadastrarDisco(db, idMaquina)
                cadastrarRecursoRede(db, idMaquina)
                payload = {
    "text": "Nova máquina adicionada! 🖥️",
    "username": "Bot de Alerta",  # Nome que aparecerá como remetente da mensagem
    "icon_emoji": ":robot_face:",  # Emoji do bot
}
                response = requests.post(url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
# Verificar se a requisição foi bem-sucedida
                if response.status_code == 200:
                    print("Mensagem enviada com sucesso!")
                else:
                    print(f"Falha ao enviar mensagem. Status Code: {response.status_code}")

        db.close()           
    else:
        print("Maquina ja cadastrada.")
                
    

if __name__ == '__main__':
    main()
