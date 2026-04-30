import reimport mathimport unicodedatafrom decimal import Decimal, InvalidOperation

import psycopg2import psycopg2.extras

DEFAULT_STOPWORDS = {"para", "de", "da", "do", "das", "dos","com", "sem", "e", "ou", "a", "o", "as", "os","um", "uma", "uns", "umas", "no", "na", "nos", "nas"}

DEFAULT_SINONIMOS = {"alto falante": "falante","speaker phone": "falante","speaker": "falante","auricular": "falante","campainha": "falante","buzzer": "falante",

"dock de carga": "conector carga",
"dock carga": "conector carga",
"dock": "conector carga",
"charging port": "conector carga",
"conector de carga": "conector carga",
"conector carga": "conector carga",
"placa conector": "conector carga",
"placa de carga": "conector carga",
"flat carga": "conector carga",
"flex carga": "conector carga",
"flex de carga": "conector carga",
"flex conector de carga": "conector carga",

"frontal": "display",
"lcd": "display",
"tela": "display",
"touch": "display",

}

DEFAULT_TIPOS = {"display": {"display"},"bateria": {"bateria", "battery"},"conector_carga": {"conector", "carga", "dock"},"tampa": {"tampa", "traseira", "carcaca", "carcaça"},"capinha": {"capinha", "capa"},"pelicula": {"pelicula", "película", "vidro", "hidrogel", "privacidade"},"aro": {"aro"},"botao": {"botao", "botão", "power", "volume", "biometria"},"camera": {"camera", "câmera", "lente"},"falante": {"falante", "speaker", "auricular", "campainha", "buzzer"},}

ESTOQUE_SQL = "CAST(COALESCE(NULLIF(estoque, ''), '0') AS NUMERIC) > 0"

def remover_acentos(txt: str) -> str:txt = unicodedata.normalize("NFKD", txt or "")return "".join(c for c in txt if not unicodedata.combining(c))

def decimal_from_any(valor):if valor is None:return Decimal("0")

txt = str(valor).strip()
if not txt:
    return Decimal("0")

txt = remover_acentos(txt.lower())
txt = txt.replace("reais", "")
txt = txt.replace("r$", "")
txt = txt.replace("(", "").replace(")", "")
txt = txt.strip()

if "," in txt and "." in txt:
    txt = txt.replace(".", "").replace(",", ".")
elif "," in txt:
    txt = txt.replace(",", ".")

txt = re.sub(r"[^0-9.\-]", "", txt)

if not txt:
    return Decimal("0")

try:
    return Decimal(txt)
except (InvalidOperation, ValueError):
    return Decimal("0")

def estoque_maior_que_zero(valor) -> bool:return decimal_from_any(valor) > 0

def normalizar_basico(txt: str) -> str:txt = remover_acentos((txt or "").lower())txt = txt.replace("-", " ")txt = txt.replace("/", " ")txt = re.sub(r"[^\w\s]+", " ", txt)txt = re.sub(r"\s+", " ", txt).strip()return txt

def ensure_filtros_tables(db_conn):conn = db_conn()cur = conn.cursor()try:cur.execute("""CREATE TABLE IF NOT EXISTS catalogo_filtros_config (id BIGSERIAL PRIMARY KEY,tipo TEXT NOT NULL,chave TEXT NOT NULL,valor TEXT,ativo BOOLEAN NOT NULL DEFAULT TRUE,criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW())""")

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_catalogo_filtros_tipo
        ON catalogo_filtros_config (tipo)
    """)

    cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_catalogo_filtros_unico
        ON catalogo_filtros_config (tipo, chave, COALESCE(valor, ''))
    """)

    conn.commit()
finally:
    cur.close()
    conn.close()

seed_default_filters(db_conn)

def seed_default_filters(db_conn):conn = db_conn()cur = conn.cursor()try:for palavra in sorted(DEFAULT_STOPWORDS):cur.execute("""INSERT INTO catalogo_filtros_config (tipo, chave, valor, ativo)VALUES (%s, %s, %s, TRUE)ON CONFLICT DO NOTHING""", ("stopword", normalizar_basico(palavra), ""))

    for origem, destino in DEFAULT_SINONIMOS.items():
        cur.execute("""
            INSERT INTO catalogo_filtros_config (tipo, chave, valor, ativo)
            VALUES (%s, %s, %s, TRUE)
            ON CONFLICT DO NOTHING
        """, ("sinonimo", normalizar_basico(origem), normalizar_basico(destino)))

    for tipo, keywords in DEFAULT_TIPOS.items():
        for keyword in sorted(keywords):
            cur.execute("""
                INSERT INTO catalogo_filtros_config (tipo, chave, valor, ativo)
                VALUES (%s, %s, %s, TRUE)
                ON CONFLICT DO NOTHING
            """, ("tipo_keyword", normalizar_basico(tipo), normalizar_basico(keyword)))

    conn.commit()
finally:
    cur.close()
    conn.close()

def listar_filtros(db_conn):conn = db_conn()cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)try:cur.execute("""SELECT id, tipo, chave, valor, ativo, criado_emFROM catalogo_filtros_configORDER BY tipo, chave, valor, id""")rows = cur.fetchall()

    saida = {
        "stopwords": [],
        "sinonimos": [],
        "tipos": {}
    }

    for row in rows:
        if row["tipo"] == "stopword":
            saida["stopwords"].append(row)
        elif row["tipo"] == "sinonimo":
            saida["sinonimos"].append(row)
        elif row["tipo"] == "tipo_keyword":
            grupo = row["chave"] or "geral"
            if grupo not in saida["tipos"]:
                saida["tipos"][grupo] = []
            saida["tipos"][grupo].append(row)

    return saida
finally:
    cur.close()
    conn.close()

def adicionar_filtro(db_conn, tipo, chave, valor=""):tipo = (tipo or "").strip().lower()chave = normalizar_basico(chave)valor = normalizar_basico(valor)

if tipo not in {"stopword", "sinonimo", "tipo_keyword"}:
    raise ValueError("Tipo de filtro inválido.")

if not chave:
    raise ValueError("Chave do filtro não informada.")

if tipo == "sinonimo" and not valor:
    raise ValueError("Informe o destino do sinônimo.")

conn = db_conn()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
try:
    cur.execute("""
        INSERT INTO catalogo_filtros_config (tipo, chave, valor, ativo)
        VALUES (%s, %s, %s, TRUE)
        RETURNING id, tipo, chave, valor, ativo, criado_em
    """, (tipo, chave, valor))
    row = cur.fetchone()
    conn.commit()
    return row
finally:
    cur.close()
    conn.close()

def excluir_filtro(db_conn, filtro_id):conn = db_conn()cur = conn.cursor()try:cur.execute("DELETE FROM catalogo_filtros_config WHERE id = %s", (filtro_id,))removidos = cur.rowcountconn.commit()return removidos > 0finally:cur.close()conn.close()

def carregar_config_filtros(db_conn):conn = db_conn()cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)try:cur.execute("""SELECT id, tipo, chave, valorFROM catalogo_filtros_configWHERE ativo = TRUEORDER BY tipo, chave, valor, id""")rows = cur.fetchall()finally:cur.close()conn.close()

stopwords = set()
sinonimos = {}
tipos = {}

for row in rows:
    if row["tipo"] == "stopword":
        if row["chave"]:
            stopwords.add(row["chave"])
    elif row["tipo"] == "sinonimo":
        if row["chave"] and row["valor"]:
            sinonimos[row["chave"]] = row["valor"]
    elif row["tipo"] == "tipo_keyword":
        grupo = row["chave"]
        keyword = row["valor"]
        if grupo and keyword:
            tipos.setdefault(grupo, set()).add(keyword)

if not stopwords:
    stopwords = {normalizar_basico(x) for x in DEFAULT_STOPWORDS}

if not sinonimos:
    sinonimos = {normalizar_basico(k): normalizar_basico(v) for k, v in DEFAULT_SINONIMOS.items()}

if not tipos:
    tipos = {
        normalizar_basico(tipo): {normalizar_basico(k) for k in keywords}
        for tipo, keywords in DEFAULT_TIPOS.items()
    }

termos_tipo = set()
for keywords in tipos.values():
    termos_tipo.update(keywords)

return {
    "stopwords": stopwords,
    "sinonimos": sinonimos,
    "tipos": tipos,
    "termos_tipo": termos_tipo,
}

def aplicar_sinonimos(txt: str, sinonimos: dict) -> str:txt = normalizar_basico(txt)

for origem, destino in sorted(sinonimos.items(), key=lambda x: len(x[0]), reverse=True):
    txt = re.sub(rf"\b{re.escape(origem)}\b", destino, txt)

txt = re.sub(r"\s+", " ", txt).strip()
return txt

def normalizar_texto(txt: str, cfg: dict) -> str:txt = aplicar_sinonimos(txt, cfg["sinonimos"])termos = [t for t in txt.split() if t and t not in cfg["stopwords"]]return " ".join(termos)

def detectar_tipo_peca(texto: str, cfg: dict):texto = normalizar_texto(texto, cfg)termos = set(texto.split())

for tipo, keywords in cfg["tipos"].items():
    if termos.intersection(keywords):
        return tipo

return None

def expandir_consultas_busca(termo_original: str, cfg: dict):bruto = (termo_original or "").strip()normalizado = normalizar_texto(bruto, cfg)consultas = []

def add(q):
    qn = normalizar_texto(q, cfg)
    if qn and qn not in consultas:
        consultas.append(qn)

add(bruto)
add(normalizado)

if re.fullmatch(r"\d{1,2}", bruto.strip()):
    add(f"iphone {bruto.strip()}")
    add(f"i {bruto.strip()}")

if re.fullmatch(r"[a-zA-Z]\s*\d{1,2}", bruto.strip()):
    numero = re.sub(r"\D", "", bruto)
    if numero:
        add(f"iphone {numero}")

return consultas

def separar_tokens_busca(termo: str, cfg: dict):consulta = normalizar_texto(termo, cfg)tokens = [t for t in consulta.split() if t]

tipo_tokens = []
modelo_tokens = []

for token in tokens:
    if token in cfg["termos_tipo"]:
        tipo_tokens.append(token)
    else:
        modelo_tokens.append(token)

tipo_detectado = detectar_tipo_peca(termo, cfg)

return {
    "consulta_normalizada": consulta,
    "tokens": tokens,
    "tipo_tokens": tipo_tokens,
    "modelo_tokens": modelo_tokens,
    "tipo_detectado": tipo_detectado,
}

def gerar_frases_modelo(modelo_tokens):frases = []

if not modelo_tokens:
    return frases

frase_completa = " ".join(modelo_tokens).strip()
if frase_completa:
    frases.append(frase_completa)

if len(modelo_tokens) > 1 and modelo_tokens[0] in {"iphone", "samsung", "motorola", "xiaomi", "redmi", "poco", "realme"}:
    resto = " ".join(modelo_tokens[1:]).strip()
    if resto:
        frases.append(resto)

unicas = []
for f in frases:
    if f and f not in unicas:
        unicas.append(f)

return unicas

def montar_exclusoes_tipo(tipo_detectado, cfg: dict):if not tipo_detectado or tipo_detectado not in cfg["tipos"]:return "", []

negativos = []
params = []

for outro_tipo, keywords in cfg["tipos"].items():
    if outro_tipo == tipo_detectado:
        continue

    for kw in sorted(keywords):
        negativos.append("""
            COALESCE(nome, '') NOT ILIKE %s
            AND COALESCE(tags, '') NOT ILIKE %s
        """)
        params.extend([f"%{kw}%", f"%{kw}%"])

if not negativos:
    return "", []

return " AND " + " AND ".join(f"({x.strip()})" for x in negativos), params

def montar_busca_exata_sql(info_busca, cfg: dict):tipo_tokens = info_busca["tipo_tokens"]modelo_tokens = info_busca["modelo_tokens"]consulta_normalizada = info_busca["consulta_normalizada"]tipo_detectado = info_busca["tipo_detectado"]

where_clauses = []
where_params = []

for token in modelo_tokens:
    where_clauses.append("palavras_busca ILIKE %s")
    where_params.append(f"%{token}%")

frases_modelo = gerar_frases_modelo(modelo_tokens)
if frases_modelo:
    sub = []
    for frase in frases_modelo:
        sub.append("(COALESCE(nome, '') ILIKE %s OR COALESCE(tags, '') ILIKE %s OR COALESCE(palavras_busca, '') ILIKE %s)")
        where_params.extend([f"%{frase}%", f"%{frase}%", f"%{frase}%"])
    where_clauses.append("(" + " OR ".join(sub) + ")")

if tipo_tokens:
    sub = []
    for token in tipo_tokens:
        sub.append("(COALESCE(nome, '') ILIKE %s OR COALESCE(tags, '') ILIKE %s OR COALESCE(palavras_busca, '') ILIKE %s)")
        where_params.extend([f"%{token}%", f"%{token}%", f"%{token}%"])
    where_clauses.append("(" + " OR ".join(sub) + ")")

exclusao_sql, exclusao_params = montar_exclusoes_tipo(tipo_detectado, cfg)

score_parts = []
score_params = []

score_parts.append("CASE WHEN COALESCE(palavras_busca, '') ILIKE %s THEN 800 ELSE 0 END")
score_params.append(f"%{consulta_normalizada}%")

score_parts.append("CASE WHEN COALESCE(nome, '') ILIKE %s THEN 500 ELSE 0 END")
score_params.append(f"%{consulta_normalizada}%")

for frase in frases_modelo:
    score_parts.append("CASE WHEN COALESCE(nome, '') ILIKE %s THEN 350 ELSE 0 END")
    score_params.append(f"%{frase}%")
    score_parts.append("CASE WHEN COALESCE(tags, '') ILIKE %s THEN 220 ELSE 0 END")
    score_params.append(f"%{frase}%")
    score_parts.append("CASE WHEN COALESCE(palavras_busca, '') ILIKE %s THEN 180 ELSE 0 END")
    score_params.append(f"%{frase}%")

for token in modelo_tokens:
    score_parts.append("CASE WHEN COALESCE(nome, '') ILIKE %s THEN 90 ELSE 0 END")
    score_params.append(f"%{token}%")
    score_parts.append("CASE WHEN COALESCE(tags, '') ILIKE %s THEN 50 ELSE 0 END")
    score_params.append(f"%{token}%")
    score_parts.append("CASE WHEN COALESCE(palavras_busca, '') ILIKE %s THEN 35 ELSE 0 END")
    score_params.append(f"%{token}%")

for token in tipo_tokens:
    score_parts.append("CASE WHEN COALESCE(nome, '') ILIKE %s THEN 160 ELSE 0 END")
    score_params.append(f"%{token}%")
    score_parts.append("CASE WHEN COALESCE(tags, '') ILIKE %s THEN 110 ELSE 0 END")
    score_params.append(f"%{token}%")
    score_parts.append("CASE WHEN COALESCE(palavras_busca, '') ILIKE %s THEN 70 ELSE 0 END")
    score_params.append(f"%{token}%")

where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
if exclusao_sql:
    where_sql += exclusao_sql
    where_params.extend(exclusao_params)

score_sql = " + ".join(score_parts) if score_parts else "0"

return where_sql, where_params, score_sql, score_params

def montar_busca_fallback_sql(info_busca):tipo_tokens = info_busca["tipo_tokens"]modelo_tokens = info_busca["modelo_tokens"]consulta_normalizada = info_busca["consulta_normalizada"]

where_clauses = []
where_params = []

for token in modelo_tokens:
    where_clauses.append("palavras_busca ILIKE %s")
    where_params.append(f"%{token}%")

frases_modelo = gerar_frases_modelo(modelo_tokens)
if frases_modelo:
    sub = []
    for frase in frases_modelo:
        sub.append("COALESCE(palavras_busca, '') ILIKE %s")
        where_params.append(f"%{frase}%")
    where_clauses.append("(" + " OR ".join(sub) + ")")

if tipo_tokens:
    sub = []
    for token in tipo_tokens:
        sub.append("COALESCE(palavras_busca, '') ILIKE %s")
        where_params.append(f"%{token}%")
    where_clauses.append("(" + " OR ".join(sub) + ")")

score_parts = []
score_params = []

score_parts.append("CASE WHEN COALESCE(palavras_busca, '') ILIKE %s THEN 450 ELSE 0 END")
score_params.append(f"%{consulta_normalizada}%")

for frase in frases_modelo:
    score_parts.append("CASE WHEN COALESCE(nome, '') ILIKE %s THEN 250 ELSE 0 END")
    score_params.append(f"%{frase}%")
    score_parts.append("CASE WHEN COALESCE(tags, '') ILIKE %s THEN 150 ELSE 0 END")
    score_params.append(f"%{frase}%")
    score_parts.append("CASE WHEN COALESCE(palavras_busca, '') ILIKE %s THEN 120 ELSE 0 END")
    score_params.append(f"%{frase}%")

for token in modelo_tokens:
    score_parts.append("CASE WHEN COALESCE(nome, '') ILIKE %s THEN 60 ELSE 0 END")
    score_params.append(f"%{token}%")
    score_parts.append("CASE WHEN COALESCE(tags, '') ILIKE %s THEN 30 ELSE 0 END")
    score_params.append(f"%{token}%")
    score_parts.append("CASE WHEN COALESCE(palavras_busca, '') ILIKE %s THEN 20 ELSE 0 END")
    score_params.append(f"%{token}%")

for token in tipo_tokens:
    score_parts.append("CASE WHEN COALESCE(nome, '') ILIKE %s THEN 90 ELSE 0 END")
    score_params.append(f"%{token}%")
    score_parts.append("CASE WHEN COALESCE(tags, '') ILIKE %s THEN 60 ELSE 0 END")
    score_params.append(f"%{token}%")
    score_parts.append("CASE WHEN COALESCE(palavras_busca, '') ILIKE %s THEN 40 ELSE 0 END")
    score_params.append(f"%{token}%")

where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
score_sql = " + ".join(score_parts) if score_parts else "0"

return where_sql, where_params, score_sql, score_params

def buscar_catalogo_filtrado(db_conn, termo="", page=1, limit=50, cursor_factory=None):termo = (termo or "").strip()offset = (page - 1) * limit

cfg = carregar_config_filtros(db_conn)
consultas = expandir_consultas_busca(termo, cfg)

melhor_rows = []
melhor_total = 0
melhor_consulta = ""

for consulta in consultas:
    info_busca = separar_tokens_busca(consulta, cfg)

    conn = db_conn()
    cur = conn.cursor(cursor_factory=cursor_factory) if cursor_factory else conn.cursor()
    try:
        where_sql, where_params, score_sql, score_params = montar_busca_exata_sql(info_busca, cfg)

        cur.execute(f"""
            SELECT COUNT(*) AS total
            FROM catalogo_grades
            WHERE {where_sql}
              AND {ESTOQUE_SQL}
        """, where_params)
        row_total = cur.fetchone()
        total = row_total["total"] if cursor_factory else row_total[0]

        cur.execute(f"""
            SELECT *,
                   ({score_sql}) AS score
            FROM catalogo_grades
            WHERE {where_sql}
              AND {ESTOQUE_SQL}
            ORDER BY score DESC, LENGTH(nome) ASC, nome ASC
            LIMIT %s OFFSET %s
        """, score_params + where_params + [limit, offset])
        rows = cur.fetchall()

        if rows:
            return rows, total, max(1, math.ceil(total / limit)) if limit else 1, consulta

        where_sql_fb, where_params_fb, score_sql_fb, score_params_fb = montar_busca_fallback_sql(info_busca)

        cur.execute(f"""
            SELECT COUNT(*) AS total
            FROM catalogo_grades
            WHERE {where_sql_fb}
              AND {ESTOQUE_SQL}
        """, where_params_fb)
        row_total_fb = cur.fetchone()
        total_fb = row_total_fb["total"] if cursor_factory else row_total_fb[0]

        cur.execute(f"""
            SELECT *,
                   ({score_sql_fb}) AS score
            FROM catalogo_grades
            WHERE {where_sql_fb}
              AND {ESTOQUE_SQL}
            ORDER BY score DESC, LENGTH(nome) ASC, nome ASC
            LIMIT %s OFFSET %s
        """, score_params_fb + where_params_fb + [limit, offset])
        rows_fb = cur.fetchall()

        if rows_fb:
            return rows_fb, total_fb, max(1, math.ceil(total_fb / limit)) if limit else 1, consulta

        if total_fb > melhor_total:
            melhor_total = total_fb
            melhor_consulta = consulta

    finally:
        cur.close()
        conn.close()

return melhor_rows, melhor_total, max(1, math.ceil(melhor_total / limit)) if limit else 1, melhor_consulta
