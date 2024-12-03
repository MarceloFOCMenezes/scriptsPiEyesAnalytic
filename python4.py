from datetime import datetime, timedelta
import random

def generate_sql_inserts():
    # Valores base para os recursos monitorados
    base_values = {
        'CPU': 70,
        'RAM': 60,
        'Latência': 20,
        'Bytes Recebidos': 300,
        'Bytes Enviados': 200,
        'Pacotes Recebidos': 600,
        'Pacotes Enviados': 500,
        'Perda de Pacotes': 1,
        'Conexões Ativas': 100
    }

    # Define o período de um ano
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2024, 12, 3)

    with open('inserts_eyesAnalytic.sql', 'w', encoding='utf-8') as file:
        file.write("-- Inserindo dados simulados para `dado_capturado` no período anual\n")
        file.write(f"-- Período: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}\n")

        current_date = start_date
        while current_date <= end_date:
            file.write(f"\n-- Dia {current_date.strftime('%Y-%m-%d')}\n")

            for hour in range(24):
                file.write(f"\n-- Hora {hour:02d}:00\n")
                inserts = []

                for resource, base_value in base_values.items():
                    variation = round(base_value * (1 + random.uniform(-0.2, 0.2)), 2)
                    timestamp = f"{current_date.strftime('%Y-%m-%d')} {hour:02d}:00:00"
                    fkMaquina = random.randint(1, 3)  # Assume 3 máquinas cadastradas
                    fkRecurso = random.randint(1, 9)  # Assume 9 recursos cadastrados (inclui Conexões Ativas)

                    insert = (
                        f"INSERT INTO dado_capturado (registro, dtHora, fkMaquina, fkRecurso) "
                        f"VALUES ({variation}, '{timestamp}', {fkMaquina}, {fkRecurso});"
                    )
                    inserts.append(insert)

                file.write('\n'.join(inserts) + '\n')

            # Avança para o próximo dia
            current_date += timedelta(days=1)

if __name__ == "__main__":
    generate_sql_inserts()
    print("Arquivo 'inserts_eyesAnalytic.sql' gerado com sucesso!")
