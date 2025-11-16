import sys
import pyodbc
import os

dsn_name = ''

conn_str = f'DRIVER=; Host=; port=; db=; uid=; pwd=;'

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

if __name__ == '__main__':

    if len(sys.argv) > 1:
        offset = int(sys.argv[1])
    else:
        print("Os parâmetros não foram passados")
        sys.exit()

    # Lê o arquivo se existir, senão usa string vazia
    if os.path.exists("initial_data.log"):
        with open("initial_data.log", "r") as f:
            start_date = f.read().strip()
    else:
        start_date = ""

    # Monta a query
    date_filter = f"AND p_nr.dt_inicio > '{start_date}'" if start_date else ""
    query = f"""
    """

    # Executa a query
    cursor.execute(query)
    rows = cursor.fetchall()

    # Atualiza o arquivo com a maior data
    if rows:
        max_dt_inicio = max(row[2] for row in rows if row[2] is not None)
        if hasattr(max_dt_inicio, "strftime"):
            max_dt_inicio_str = max_dt_inicio.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        else:
            max_dt_inicio_str = str(max_dt_inicio)
        with open("initial_data.log", "w") as f:
            f.write(max_dt_inicio_str)

    # Itera e imprime os resultados
    for row in rows:
        processo = str(row[0]).replace("-", "").replace(".", "")
        numero = str(row[1])
        nr_processo = str(row[2])
        print(f"{processo}, {numero}, {nr_processo}")

