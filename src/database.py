import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "leituras.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def get_db_connection():
    """Retorna uma conexão configurada com row_factory e suporte a escrita concorrente (WAL)."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")  # espera até 5s antes de lançar OperationalError
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Cria as tabelas se não existirem, executando o schema.sql."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = f.read()
    conn = get_db_connection()
    try:
        conn.executescript(schema)
        conn.commit()
    finally:
        conn.close()


def inserir_leitura(temperatura, umidade, pressao=None):
    """Insere uma nova leitura e retorna o id gerado."""
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO leituras (temperatura, umidade, pressao) VALUES (?, ?, ?)",
            (temperatura, umidade, pressao),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def listar_leituras(limite=50):
    """Retorna as leituras mais recentes, limitadas por `limite`."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM leituras ORDER BY timestamp DESC LIMIT ?",
            (limite,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def buscar_leitura(id):
    """Retorna uma leitura pelo id, ou None se não encontrada."""
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM leituras WHERE id = ?", (id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def atualizar_leitura(id, dados):
    """Atualiza campos de uma leitura existente."""
    campos_permitidos = {"temperatura", "umidade", "pressao"}
    campos = {k: v for k, v in dados.items() if k in campos_permitidos}
    if not campos:
        raise ValueError("Nenhum campo válido para atualizar.")

    set_clause = ", ".join(f"{k} = ?" for k in campos)
    valores = list(campos.values()) + [id]

    conn = get_db_connection()
    try:
        cursor = conn.execute(
            f"UPDATE leituras SET {set_clause} WHERE id = ?", valores
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def deletar_leitura(id):
    """Remove uma leitura pelo id. Retorna True se alguma linha foi removida, False caso contrário."""
    conn = get_db_connection()
    try:
        cursor = conn.execute("DELETE FROM leituras WHERE id = ?", (id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
