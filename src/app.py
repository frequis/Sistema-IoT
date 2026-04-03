from flask import Flask, request, jsonify, render_template, abort
from database import (
    init_db,
    inserir_leitura,
    listar_leituras,
    buscar_leitura,
    atualizar_leitura,
    deletar_leitura,
    get_db_connection,
)
from config import FLASK_DEBUG, FLASK_HOST, FLASK_PORT

app = Flask(__name__)

# Garante que as tabelas existam independente de como o servidor é iniciado
# (python app.py  OU  flask run)
with app.app_context():
    init_db()


def _quer_json():
    """Retorna True se o cliente quer JSON (via ?formato=json ou Accept header)."""
    return (
        request.args.get("formato") == "json"
        or request.accept_mimetypes.best == "application/json"
    )


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    leituras = listar_leituras(limite=10)
    if _quer_json():
        return jsonify(leituras)
    return render_template("index.html", leituras=leituras)


# ---------------------------------------------------------------------------
# GET /leituras
# ---------------------------------------------------------------------------
@app.route("/leituras", methods=["GET"])
def listar():
    try:
        limite = int(request.args.get("limite", 20))
        pagina = int(request.args.get("pagina", 1))
    except ValueError:
        abort(400, "Parâmetros de paginação inválidos.")

    limite = max(1, min(limite, 100))
    pagina = max(1, pagina)
    offset = (pagina - 1) * limite

    conn = get_db_connection()
    try:
        total = conn.execute("SELECT COUNT(*) FROM leituras").fetchone()[0]
        rows = conn.execute(
            "SELECT * FROM leituras ORDER BY timestamp DESC LIMIT ? OFFSET ?",
            (limite, offset),
        ).fetchall()
    finally:
        conn.close()

    leituras = [dict(r) for r in rows]
    paginas = (total + limite - 1) // limite

    if _quer_json():
        return jsonify(
            {
                "pagina": pagina,
                "limite": limite,
                "total": total,
                "paginas": paginas,
                "leituras": leituras,
            }
        )
    return render_template(
        "historico.html",
        leituras=leituras,
        pagina=pagina,
        paginas=paginas,
        limite=limite,
        total=total,
    )


# ---------------------------------------------------------------------------
# Mapeamento: distância (cm) → variáveis meteorológicas simuladas
# ---------------------------------------------------------------------------
DIST_MIN, DIST_MAX = 2.0, 200.0

def _mapear(valor, out_min, out_max, inverso=False):
    """Mapeia distância para uma faixa de saída, com clamp nas bordas."""
    t = (max(DIST_MIN, min(DIST_MAX, valor)) - DIST_MIN) / (DIST_MAX - DIST_MIN)
    if inverso:
        t = 1.0 - t
    return round(out_min + t * (out_max - out_min), 1)

def _simular_de_distancia(distancia):
    return {
        "temperatura": _mapear(distancia, 15.0, 40.0),           # perto = mais frio
        "umidade":     _mapear(distancia, 30.0, 95.0, inverso=True),  # perto = mais úmido
        "pressao":     _mapear(distancia, 990.0, 1030.0),        # perto = pressão baixa
    }


# ---------------------------------------------------------------------------
# POST /leituras
# ---------------------------------------------------------------------------
@app.route("/leituras", methods=["POST"])
def criar():
    dados = request.get_json(silent=True)
    if not dados:
        abort(400, "Body JSON obrigatório.")

    try:
        # Modo sensor ultrassônico: recebe só distancia e deriva os demais
        if "distancia" in dados and "temperatura" not in dados:
            distancia = float(dados["distancia"])
            simulado  = _simular_de_distancia(distancia)
            temperatura = simulado["temperatura"]
            umidade     = simulado["umidade"]
            pressao     = simulado["pressao"]
        else:
            # Modo sensor real (DHT11 + BMP): recebe os valores diretamente
            if dados.get("temperatura") is None or dados.get("umidade") is None:
                abort(400, "Campos obrigatórios: temperatura e umidade (ou distancia).")
            temperatura = float(dados["temperatura"])
            umidade     = float(dados["umidade"])
            pressao     = float(dados["pressao"])   if "pressao"   in dados else None
            distancia   = float(dados["distancia"]) if "distancia" in dados else None
    except (ValueError, TypeError):
        abort(400, "Valores numéricos inválidos.")

    novo_id = inserir_leitura(temperatura, umidade, pressao, distancia)
    leitura = buscar_leitura(novo_id)
    return jsonify(leitura), 201


# ---------------------------------------------------------------------------
# GET /leituras/<id>
# ---------------------------------------------------------------------------
@app.route("/leituras/<int:id>", methods=["GET"])
def detalhe(id):
    leitura = buscar_leitura(id)
    if leitura is None:
        abort(404, f"Leitura {id} não encontrada.")

    if _quer_json():
        return jsonify(leitura)
    return render_template("detalhe.html", leitura=leitura)


# ---------------------------------------------------------------------------
# GET /leituras/<id>/editar  (formulário HTML)
# ---------------------------------------------------------------------------
@app.route("/leituras/<int:id>/editar", methods=["GET"])
def editar(id):
    leitura = buscar_leitura(id)
    if leitura is None:
        abort(404, f"Leitura {id} não encontrada.")
    return render_template("editar.html", leitura=leitura)


# ---------------------------------------------------------------------------
# PUT /leituras/<id>
# ---------------------------------------------------------------------------
@app.route("/leituras/<int:id>", methods=["PUT"])
def atualizar(id):
    if buscar_leitura(id) is None:
        abort(404, f"Leitura {id} não encontrada.")

    dados = request.get_json(silent=True)
    if not dados:
        abort(400, "Body JSON obrigatório.")

    try:
        atualizado = atualizar_leitura(id, dados)
    except ValueError as e:
        abort(400, str(e))

    if not atualizado:
        abort(500, "Não foi possível atualizar a leitura.")

    return jsonify(buscar_leitura(id))


# ---------------------------------------------------------------------------
# DELETE /leituras/<id>
# ---------------------------------------------------------------------------
@app.route("/leituras/<int:id>", methods=["DELETE"])
def deletar(id):
    if buscar_leitura(id) is None:
        abort(404, f"Leitura {id} não encontrada.")

    deletar_leitura(id)
    return jsonify({"mensagem": f"Leitura {id} removida com sucesso."}), 200


# ---------------------------------------------------------------------------
# GET /api/estatisticas
# ---------------------------------------------------------------------------
@app.route("/api/estatisticas", methods=["GET"])
def estatisticas():
    desde = request.args.get("desde")   # ex: 2024-01-01
    ate = request.args.get("ate")       # ex: 2024-12-31

    filtros = []
    params = []
    if desde:
        filtros.append("timestamp >= ?")
        params.append(desde)
    if ate:
        filtros.append("timestamp <= ?")
        params.append(ate + " 23:59:59")

    where = ("WHERE " + " AND ".join(filtros)) if filtros else ""

    conn = get_db_connection()
    try:
        row = conn.execute(
            f"""
            SELECT
                COUNT(*)          AS total,
                ROUND(AVG(temperatura), 2) AS temp_media,
                ROUND(MIN(temperatura), 2) AS temp_min,
                ROUND(MAX(temperatura), 2) AS temp_max,
                ROUND(AVG(umidade), 2)     AS umid_media,
                ROUND(MIN(umidade), 2)     AS umid_min,
                ROUND(MAX(umidade), 2)     AS umid_max,
                ROUND(AVG(pressao), 2)     AS pres_media,
                ROUND(MIN(pressao), 2)     AS pres_min,
                ROUND(MAX(pressao), 2)     AS pres_max
            FROM leituras {where}
            """,
            params,
        ).fetchone()
    finally:
        conn.close()

    resultado = dict(row)
    resultado["filtros"] = {"desde": desde, "ate": ate}

    if _quer_json() or True:   # este endpoint sempre devolve JSON
        return jsonify(resultado)


# ---------------------------------------------------------------------------
# Tratamento de erros
# ---------------------------------------------------------------------------
@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(500)
def erro(e):
    if _quer_json() or request.method in ("POST", "PUT", "DELETE"):
        return jsonify({"erro": str(e.description)}), e.code
    return render_template("erro.html", erro=e), e.code


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    init_db()
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
