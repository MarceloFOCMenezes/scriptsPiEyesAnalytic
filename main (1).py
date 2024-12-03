from datetime import datetime, timedelta
import random

def generate_sql_inserts():
    # Base values for resources
    base_values = {
        'usoCPU': 70.0,
        'usoRAM': 60.0,
        'usoTotal': 65.0,
        'velocidadeDownload': 90.0,
        'velocidadeUpload': 80.0,
        'erroPacotesEntrada': 2.0,
        'erroPacotesSaida': 1.0,
        'descartePacotesEntrada': 1.0,
        'descartePacotesSaida': 1.0,
        'megabytesRecebidos': 300.0,
        'megabytesEnviados': 200.0,
        'pacotesEnviados': 500.0,
        'pacotesRecebidos': 600.0
    }

    # Generate dates for both weeks
    start_date = datetime(2024, 10, 20)
    dates = [(start_date + timedelta(days=x)).strftime('%Y-%m-%d') for x in range(14)]

    for date in dates:
        print(f"-- Dia {date}")
        print("INSERT INTO ServGuard.Captura (fkMaquinaRecurso, registro, dthCriacao, isAlerta) VALUES")

        inserts = []
        for resource, base_value in base_values.items():
            # Add small random variation (-5% to +5%)
            variation = base_value * (1 + random.uniform(-0.05, 0.05))

            insert = f"""    ((SELECT idMaquinaRecurso FROM ServGuard.MaquinaRecurso 
        WHERE fkMaquina = 1 AND fkRecurso = (SELECT idRecurso FROM ServGuard.Recurso WHERE nome = '{resource}')), 
        {variation:.0f}, '{date} 10:00:00', 0)"""
            inserts.append(insert)

        print(',\n'.join(inserts) + ';\n')

print("-- Inserindo dados para as duas semanas")
generate_sql_inserts()