from datetime import datetime, timedelta
import random

def generate_sql_inserts():
    # Valores base apenas para os recursos necessários
    base_values = {
        'CPU': 70,
        'RAM': 60,
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
                    
                    # Limitar valores de CPU e RAM para no máximo 100%
                    if resource in ['CPU', 'RAM']:
                        variation = min(variation, 100)

                    timestamp = f"{current_date.strftime('%Y-%m-%d')} {hour:02d}:00:00"
                    fkMaquina = 5  # Substituímos pela máquina 5
                    fkRecurso = {'CPU': 1, 'RAM': 2, 'Conexões Ativas': 8}[resource]  # IDs fixos para os recursos

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
