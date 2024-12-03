from datetime import datetime, timedelta
import random

def generate_sql_inserts():
    # Valores base para conexões ativas
    base_connections = 100  # Base inicial de conexões ativas
    connection_variation = 0.2  # Variação máxima de 20%

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

                # Gera o número de conexões ativas
                active_connections = round(base_connections * (1 + random.uniform(-connection_variation, connection_variation)), 2)
                fkMaquina = 5  # Apenas a máquina 5

                # Calcula CPU e RAM com base nas conexões ativas
                cpu_usage = round(min(active_connections * 0.8 + random.uniform(-5, 5), 100), 2)  # 80% das conexões
                ram_usage = round(min(active_connections * 0.5 + random.uniform(-3, 3), 100), 2)  # 50% das conexões

                # Timestamps
                timestamp = f"{current_date.strftime('%Y-%m-%d')} {hour:02d}:00:00"

                # Cria as inserções
                inserts.append(
                    f"INSERT INTO dado_capturado (registro, dtHora, fkMaquina, fkRecurso) "
                    f"VALUES ({cpu_usage}, '{timestamp}', {fkMaquina}, 1);"  # CPU
                )
                inserts.append(
                    f"INSERT INTO dado_capturado (registro, dtHora, fkMaquina, fkRecurso) "
                    f"VALUES ({ram_usage}, '{timestamp}', {fkMaquina}, 2);"  # RAM
                )
                inserts.append(
                    f"INSERT INTO dado_capturado (registro, dtHora, fkMaquina, fkRecurso) "
                    f"VALUES ({active_connections}, '{timestamp}', {fkMaquina}, 8);"  # Conexões Ativas
                )

                file.write('\n'.join(inserts) + '\n')

            # Avança para o próximo dia
            current_date += timedelta(days=1)

if __name__ == "__main__":
    generate_sql_inserts()
    print("Arquivo 'inserts_eyesAnalytic.sql' gerado com sucesso!")
