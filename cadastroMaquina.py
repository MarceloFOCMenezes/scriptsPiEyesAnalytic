import os
from mysql.connector import connect, Error
from dotenv import load_dotenv, set_key
import cpuinfo
import psutil
import subprocess

load_dotenv()


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
        resultado = cursor.execute(f"SELECT idEmpresa FROM empresa WHERE codSeg = {codigoSeguranca}")
        empresaId = cursor.fetchall()
        if(len(empresaId) > 0):
            resultadoEmpresaId = empresaId[0]
            set_key(caminhoEnv,idEmpresa_key,str(resultadoEmpresaId[0]))
            return resultadoEmpresaId[0]
        else:
            print("O codigo de seguranca invalido")
            return None


def cadastrarMaquina(db, EmpresaId):
    with db.cursor() as cursor:
        resultado = cursor.execute(f"SELECT idMaquina FROM maquina ORDER BY idMaquina DESC LIMIT 1")
        qtdMaquinaRaw = cursor.fetchall()
        idMaquina = (qtdMaquinaRaw[0])[0]
        query= ("INSERT INTO maquina (idMaquina, situacao, fkEmpresa, fkPrioridade) VALUES" +
                "(%s, 'ativa', %s, 3)")
        valor = [idMaquina+1, EmpresaId]

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

def obterInformacaoRam():
    comando = "sudo dmidecode --type memory"
    fabricantes = []
    tamanhos = []
    velocidades = []
    
    try:
        resultado = subprocess.check_output(comando, shell=True, text=True)

        fabricante_atual = None
        tamanho_atual = None
        velocidade_atual = None

        for linha in resultado.splitlines():
            if "Manufacturer" in linha:
                fabricante_atual = linha.split(":")[1].strip()
                fabricantes.append(fabricante_atual)
            elif "Size" in linha and "MB" in linha:
                tamanho_atual = linha.split(":")[1].strip()
                tamanhos.append(tamanho_atual)
            elif "Speed" in linha:
                velocidade_atual = linha.split(":")[1].strip()
                velocidades.append(velocidade_atual)

        return fabricantes, tamanhos, velocidades

    except subprocess.CalledProcessError as e:
        print("Erro ao obter informações da RAM:", e)
        return None, None, None

def obterInformacaoDisco():                                                     
    comando = "lsblk -o NAME,SIZE,MODEL,TYPE"
    try:
        resultado = subprocess.check_output(comando, shell=True, text=True)
        discos = []
        for linha in resultado.splitlines()[1:]:
            colunas = linha.split()
            if len(colunas) >= 3:
                nome = colunas[0]
                tamanho = colunas[1][:-1]
                modelo = ' '.join(colunas[2:-1])
                discos.append({
                    'nome': nome,
                    'tamanho': tamanho,
                    'modelo': modelo,
                })
                return discos
    except subprocess.CalledProcessError as e:
        print("Erro ao obter informações do disco:", e)
        return None

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
    
    fabricantes, capacidade, velocidade = obterInformacaoRam()

    for fabricante, capacidade, velocidade in zip(fabricantes,capacidade,velocidade):
        idVinculado =  vincular(db, MaquinaId, 2)
        informar( db, fabricante, idVinculado, 1)
        informar( db, velocidade, idVinculado, 3)
        informar( db, capacidade, idVinculado, 6)

def cadastrarDisco(db, MaquinaId):
    disco = obterInformacaoDisco()
    for d in disco:
        fabricante = d['nome']
        modelo = d['modelo']
        capacidade  = d['tamanho']
        idVinculado =  vincular(db, MaquinaId, 3)
        informar( db, fabricante, idVinculado, 1)
        informar( db, modelo, idVinculado, 2)
        informar( db, capacidade, idVinculado, 6)

def cadastrarRecursoRede(db, idMaquina):
    vincular(db, idMaquina, 4)
    vincular(db, idMaquina, 5)
    vincular(db, idMaquina, 6)
    vincular(db, idMaquina, 7)
    vincular(db, idMaquina, 8)

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
                idMaquina = cadastrarMaquina(db, idEmpresa)
                cadastrarRecursoRede(db,idMaquina)
                cadastrarCpu(db, idMaquina)
                cadastrarRam(db, idMaquina)              
                cadastrarDisco(db, idMaquina)
                cadastrarRecursoRede(db, idMaquina)
        db.close()           
    else:
        print("Maquina ja cadastrada.")
                
    

if __name__ == '__main__':
    main()
