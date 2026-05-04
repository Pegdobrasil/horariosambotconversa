from flask import Flask, jsonify, Response, request
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import calendar
import json
import os
import requests

app = Flask(__name__)

TIMEZONE_BRASILIA = ZoneInfo("America/Sao_Paulo")

LOGO_PEG_URL = "https://magazord-public.s3.sa-east-1.amazonaws.com/pegdobrasil/img/2025/03/banner/138072/medium/logo-vazia.png"

BOTCONVERSA_WEBHOOK_URL = os.getenv(
    "BOTCONVERSA_WEBHOOK_URL",
    "https://h.integrations-hub.com/wh/38/1lfflc2/2iC6BeqklPyOx_e4aiG6k8OIKBXCdc-V9nb60pBbJTk/"
).strip()

DIAS_SEMANA = {
    0: "segunda-feira",
    1: "terça-feira",
    2: "quarta-feira",
    3: "quinta-feira",
    4: "sexta-feira",
    5: "sábado",
    6: "domingo"
}

DIAS_ENDPOINT = {
    "segunda": 0,
    "segunda-feira": 0,
    "terca": 1,
    "terça": 1,
    "terça-feira": 1,
    "quarta": 2,
    "quarta-feira": 2,
    "quinta": 3,
    "quinta-feira": 3,
    "sexta": 4,
    "sexta-feira": 4,
    "sabado": 5,
    "sábado": 5,
    "domingo": 6
}

MESES = {
    1: "janeiro",
    2: "fevereiro",
    3: "março",
    4: "abril",
    5: "maio",
    6: "junho",
    7: "julho",
    8: "agosto",
    9: "setembro",
    10: "outubro",
    11: "novembro",
    12: "dezembro"
}


def calcular_pascoa(ano):
    a = ano % 19
    b = ano // 100
    c = ano % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1
    return date(ano, mes, dia)


def obter_datas_fechadas(ano):
    pascoa = calcular_pascoa(ano)
    sexta_feira_santa = pascoa - timedelta(days=2)
    corpus_christi = pascoa + timedelta(days=60)

    return {
        date(ano, 1, 1): {"nome": "Confraternização Universal", "tipo": "feriado_nacional"},
        sexta_feira_santa: {"nome": "Sexta-feira Santa", "tipo": "feriado_nacional"},
        date(ano, 4, 21): {"nome": "Tiradentes", "tipo": "feriado_nacional"},
        date(ano, 5, 1): {"nome": "Dia do Trabalho", "tipo": "feriado_nacional"},
        corpus_christi: {"nome": "Corpus Christi", "tipo": "data_especial"},
        date(ano, 9, 7): {"nome": "Independência do Brasil", "tipo": "feriado_nacional"},
        date(ano, 11, 2): {"nome": "Finados", "tipo": "feriado_nacional"},
        date(ano, 11, 15): {"nome": "Proclamação da República", "tipo": "feriado_nacional"},
        date(ano, 12, 25): {"nome": "Natal", "tipo": "feriado_nacional"}
    }


def obter_feriados_com_loja_aberta(ano):
    return {
        date(ano, 9, 8): {
            "nome": "Nossa Senhora da Luz dos Pinhais, padroeira de Curitiba",
            "tipo": "feriado_municipal_loja_aberta"
        },
        date(ano, 10, 12): {
            "nome": "Nossa Senhora Aparecida",
            "tipo": "feriado_nacional_loja_aberta"
        },
        date(ano, 11, 20): {
            "nome": "Dia Nacional de Zumbi e da Consciência Negra",
            "tipo": "feriado_nacional_loja_aberta"
        }
    }


def verificar_data_fechada(data_consulta):
    datas_fechadas = obter_datas_fechadas(data_consulta.year)

    if data_consulta in datas_fechadas:
        item = datas_fechadas[data_consulta]
        return {
            "eh_feriado_nacional": item["tipo"] == "feriado_nacional",
            "eh_feriado_municipal": item["tipo"] == "feriado_municipal",
            "eh_data_especial": item["tipo"] == "data_especial",
            "nome_feriado": item["nome"],
            "tipo_fechamento": item["tipo"],
            "motivo_fechamento": item["nome"]
        }

    return {
        "eh_feriado_nacional": False,
        "eh_feriado_municipal": False,
        "eh_data_especial": False,
        "nome_feriado": None,
        "tipo_fechamento": None,
        "motivo_fechamento": None
    }


def verificar_feriado_com_loja_aberta(data_consulta):
    feriados_abertos = obter_feriados_com_loja_aberta(data_consulta.year)

    if data_consulta in feriados_abertos:
        item = feriados_abertos[data_consulta]
        return {
            "eh_feriado_com_loja_aberta": True,
            "nome_feriado_aberto": item["nome"],
            "tipo_feriado_aberto": item["tipo"],
            "observacao_feriado_aberto": "A loja não fecha nesta data."
        }

    return {
        "eh_feriado_com_loja_aberta": False,
        "nome_feriado_aberto": None,
        "tipo_feriado_aberto": None,
        "observacao_feriado_aberto": None
    }


def gerar_dados_data(ano, mes, dia):
    try:
        data_consulta = date(ano, mes, dia)

        dia_semana_numero = data_consulta.weekday()
        dia_semana = DIAS_SEMANA[dia_semana_numero]
        data_extenso = f"{dia_semana}, {dia:02d} de {MESES[mes]} de {ano}"

        eh_sabado = dia_semana_numero == 5
        eh_domingo = dia_semana_numero == 6
        eh_dia_util = dia_semana_numero in [0, 1, 2, 3, 4]
        eh_final_de_semana = eh_sabado or eh_domingo

        fechamento = verificar_data_fechada(data_consulta)
        feriado_aberto = verificar_feriado_com_loja_aberta(data_consulta)

        if fechamento["eh_feriado_nacional"] or fechamento["eh_feriado_municipal"] or fechamento["eh_data_especial"]:
            loja_abre = False
            funcionamento_previsto = "Fechado"
            motivo_fechamento = fechamento["motivo_fechamento"]
        elif eh_domingo:
            loja_abre = False
            funcionamento_previsto = "Fechado"
            motivo_fechamento = "Domingo"
        elif eh_sabado:
            loja_abre = True
            funcionamento_previsto = "09:00 às 13:00"
            motivo_fechamento = None
        elif eh_dia_util:
            loja_abre = True
            funcionamento_previsto = "09:00 às 18:00"
            motivo_fechamento = None
        else:
            loja_abre = False
            funcionamento_previsto = "Fechado"
            motivo_fechamento = "Data sem expediente cadastrado"

        if loja_abre:
            if feriado_aberto["eh_feriado_com_loja_aberta"]:
                mensagem_resposta = (
                    f"Nessa data teremos atendimento das {funcionamento_previsto}. "
                    f"Feriado cadastrado com loja aberta: {feriado_aberto['nome_feriado_aberto']}. "
                    "A loja não fecha nesta data."
                )
            else:
                mensagem_resposta = f"Nessa data teremos atendimento das {funcionamento_previsto}."
        else:
            if fechamento["nome_feriado"]:
                mensagem_resposta = f"Nessa data não teremos atendimento devido ao feriado: {fechamento['nome_feriado']}."
            else:
                mensagem_resposta = f"Nessa data não teremos atendimento. Motivo: {motivo_fechamento}."

        return {
            "data": data_consulta.strftime("%Y-%m-%d"),
            "data_br": data_consulta.strftime("%d/%m/%Y"),
            "data_extenso": data_extenso,
            "ano": ano,
            "mes": mes,
            "mes_nome": MESES[mes],
            "dia": dia,
            "dia_semana": dia_semana,
            "dia_semana_numero": dia_semana_numero,
            "eh_dia_util": eh_dia_util,
            "eh_sabado": eh_sabado,
            "eh_domingo": eh_domingo,
            "eh_final_de_semana": eh_final_de_semana,
            "eh_feriado_nacional": fechamento["eh_feriado_nacional"],
            "eh_feriado_municipal": fechamento["eh_feriado_municipal"],
            "eh_data_especial": fechamento["eh_data_especial"],
            "nome_feriado": fechamento["nome_feriado"],
            "tipo_fechamento": fechamento["tipo_fechamento"],
            "eh_feriado_com_loja_aberta": feriado_aberto["eh_feriado_com_loja_aberta"],
            "nome_feriado_aberto": feriado_aberto["nome_feriado_aberto"],
            "tipo_feriado_aberto": feriado_aberto["tipo_feriado_aberto"],
            "observacao_feriado_aberto": feriado_aberto["observacao_feriado_aberto"],
            "loja_abre": loja_abre,
            "funcionamento_previsto": funcionamento_previsto,
            "motivo_fechamento": motivo_fechamento,
            "mensagem_resposta": mensagem_resposta
        }

    except ValueError:
        return None


def verificar_atendimento_agora():
    agora = datetime.now(TIMEZONE_BRASILIA)
    dados_data = gerar_dados_data(agora.year, agora.month, agora.day)

    minutos_atuais = agora.hour * 60 + agora.minute
    inicio_atendimento = 9 * 60
    fim_segunda_sexta = 18 * 60
    fim_sabado = 13 * 60

    atendimento_aberto = False

    if dados_data["loja_abre"]:
        if dados_data["eh_dia_util"] and inicio_atendimento <= minutos_atuais < fim_segunda_sexta:
            atendimento_aberto = True
        elif dados_data["eh_sabado"] and inicio_atendimento <= minutos_atuais < fim_sabado:
            atendimento_aberto = True

    if atendimento_aberto:
        status_atendimento = "aberto"

        if dados_data["eh_feriado_com_loja_aberta"]:
            mensagem_atendimento = (
                f"Estamos em horário de atendimento. "
                f"Hoje é {dados_data['nome_feriado_aberto']}, mas a loja não fecha nesta data."
            )
        else:
            mensagem_atendimento = "Estamos em horário de atendimento."
    else:
        status_atendimento = "fechado"

        if dados_data["nome_feriado"]:
            mensagem_atendimento = f"Estamos fechados devido ao feriado: {dados_data['nome_feriado']}."
        elif dados_data["eh_domingo"]:
            mensagem_atendimento = "Estamos fechados. Aos domingos não temos atendimento."
        else:
            mensagem_atendimento = "Estamos fora do horário de atendimento."

    return {
        "atendimento_aberto": atendimento_aberto,
        "status_atendimento": status_atendimento,
        "mensagem_atendimento": mensagem_atendimento
    }


def obter_dados_horario():
    agora = datetime.now(TIMEZONE_BRASILIA)
    dados_data = gerar_dados_data(agora.year, agora.month, agora.day)
    atendimento = verificar_atendimento_agora()

    return {
        "empresa": "PEG do Brasil",
        "timezone": "America/Sao_Paulo",
        "data_atual": dados_data["data"],
        "data_br": dados_data["data_br"],
        "data_extenso": dados_data["data_extenso"],
        "dia_semana": dados_data["dia_semana"],
        "dia_semana_numero": dados_data["dia_semana_numero"],
        "hora_atual": agora.strftime("%H:%M:%S"),
        "ano_atual": agora.year,
        "mes_atual": agora.month,
        "mes_nome": MESES[agora.month],
        "dia_mes": agora.day,
        "hora_numero": agora.hour,
        "minuto_numero": agora.minute,
        "segundo_numero": agora.second,
        "atendimento_aberto": atendimento["atendimento_aberto"],
        "status_atendimento": atendimento["status_atendimento"],
        "mensagem_atendimento": atendimento["mensagem_atendimento"],
        "loja_abre_hoje": dados_data["loja_abre"],
        "funcionamento_previsto_hoje": dados_data["funcionamento_previsto"],
        "eh_feriado_nacional": dados_data["eh_feriado_nacional"],
        "eh_feriado_municipal": dados_data["eh_feriado_municipal"],
        "eh_data_especial": dados_data["eh_data_especial"],
        "nome_feriado": dados_data["nome_feriado"],
        "eh_feriado_com_loja_aberta": dados_data["eh_feriado_com_loja_aberta"],
        "nome_feriado_aberto": dados_data["nome_feriado_aberto"],
        "observacao_feriado_aberto": dados_data["observacao_feriado_aberto"],
        "motivo_fechamento": dados_data["motivo_fechamento"],
        "horario_funcionamento": {
            "segunda_a_sexta": "09:00 às 18:00",
            "sabado": "09:00 às 13:00",
            "domingo": "Fechado",
            "feriados_fechados": "Fechado",
            "feriados_com_loja_aberta": "A loja não fecha nessas datas cadastradas"
        }
    }


def gerar_calendario_mes(ano, mes):
    try:
        primeiro_dia, total_dias = calendar.monthrange(ano, mes)

        dias = []
        for dia in range(1, total_dias + 1):
            dias.append(gerar_dados_data(ano, mes, dia))

        semanas = []
        semana_atual = []

        for _ in range(primeiro_dia):
            semana_atual.append(None)

        for dados_dia in dias:
            semana_atual.append(dados_dia)

            if len(semana_atual) == 7:
                semanas.append(semana_atual)
                semana_atual = []

        if semana_atual:
            while len(semana_atual) < 7:
                semana_atual.append(None)
            semanas.append(semana_atual)

        return {
            "ano": ano,
            "mes": mes,
            "mes_nome": MESES[mes],
            "total_dias": total_dias,
            "primeiro_dia_semana_numero": primeiro_dia,
            "primeiro_dia_semana": DIAS_SEMANA[primeiro_dia],
            "dias": dias,
            "semanas": semanas
        }

    except Exception:
        return None


def gerar_calendario_ano(ano):
    meses = []

    for mes in range(1, 13):
        meses.append(gerar_calendario_mes(ano, mes))

    return {
        "ano": ano,
        "total_meses": 12,
        "meses": meses
    }


def listar_feriados_ano(ano):
    feriados = []

    for data_fechada, item in sorted(obter_datas_fechadas(ano).items()):
        dados = gerar_dados_data(data_fechada.year, data_fechada.month, data_fechada.day)

        feriados.append({
            "data": dados["data"],
            "data_br": dados["data_br"],
            "data_extenso": dados["data_extenso"],
            "dia_semana": dados["dia_semana"],
            "nome_feriado": item["nome"],
            "tipo": item["tipo"],
            "loja_abre": False,
            "funcionamento_previsto": "Fechado",
            "motivo_fechamento": item["nome"],
            "eh_feriado_com_loja_aberta": False
        })

    for data_aberta, item in sorted(obter_feriados_com_loja_aberta(ano).items()):
        dados = gerar_dados_data(data_aberta.year, data_aberta.month, data_aberta.day)

        feriados.append({
            "data": dados["data"],
            "data_br": dados["data_br"],
            "data_extenso": dados["data_extenso"],
            "dia_semana": dados["dia_semana"],
            "nome_feriado": item["nome"],
            "tipo": item["tipo"],
            "loja_abre": dados["loja_abre"],
            "funcionamento_previsto": dados["funcionamento_previsto"],
            "motivo_fechamento": None,
            "eh_feriado_com_loja_aberta": True,
            "observacao": "A loja não fecha nesta data."
        })

    feriados = sorted(feriados, key=lambda item: item["data"])

    return {
        "ano": ano,
        "tipo_consulta": "feriados_e_datas_cadastradas",
        "total_feriados": len(feriados),
        "feriados": feriados
    }


def proxima_data_por_dia_semana(dia_alvo):
    hoje = datetime.now(TIMEZONE_BRASILIA).date()
    delta = (dia_alvo - hoje.weekday()) % 7

    if delta == 0:
        delta = 7

    data_alvo = hoje + timedelta(days=delta)
    return gerar_dados_data(data_alvo.year, data_alvo.month, data_alvo.day)


def proximo_feriado():
    hoje = datetime.now(TIMEZONE_BRASILIA).date()

    eventos = []

    for ano in range(hoje.year, hoje.year + 3):
        for data_fechada, item in sorted(obter_datas_fechadas(ano).items()):
            eventos.append((data_fechada, item["nome"], "fechado"))

        for data_aberta, item in sorted(obter_feriados_com_loja_aberta(ano).items()):
            eventos.append((data_aberta, item["nome"], "loja_aberta"))

    eventos = sorted(eventos, key=lambda item: item[0])

    for data_evento, nome, tipo in eventos:
        if data_evento >= hoje:
            dados = gerar_dados_data(data_evento.year, data_evento.month, data_evento.day)
            dados["tipo_consulta"] = "proximo_feriado"
            dados["tipo_evento"] = tipo
            dados["nome_evento"] = nome
            return dados

    return None


def quer_visual():
    return request.args.get("visual") in ["1", "true", "sim", "html"]


def montar_item_inicio_botconversa():
    dados = obter_dados_horario()

    item = {
        "empresa": dados.get("empresa"),
        "timezone": dados.get("timezone"),

        "data_atual": dados.get("data_atual"),
        "data_br": dados.get("data_br"),
        "data_extenso": dados.get("data_extenso"),

        "dia_semana": dados.get("dia_semana"),
        "dia_semana_numero": dados.get("dia_semana_numero"),

        "hora_atual": dados.get("hora_atual"),
        "ano_atual": dados.get("ano_atual"),
        "mes_atual": dados.get("mes_atual"),
        "mes_nome": dados.get("mes_nome"),
        "dia_mes": dados.get("dia_mes"),

        "atendimento_aberto": dados.get("atendimento_aberto"),
        "status_atendimento": dados.get("status_atendimento"),
        "mensagem_atendimento": dados.get("mensagem_atendimento"),

        "loja_abre_hoje": dados.get("loja_abre_hoje"),
        "funcionamento_previsto_hoje": dados.get("funcionamento_previsto_hoje"),

        "eh_feriado_nacional": dados.get("eh_feriado_nacional"),
        "eh_feriado_municipal": dados.get("eh_feriado_municipal"),
        "eh_data_especial": dados.get("eh_data_especial"),
        "nome_feriado": dados.get("nome_feriado"),

        "eh_feriado_com_loja_aberta": dados.get("eh_feriado_com_loja_aberta"),
        "nome_feriado_aberto": dados.get("nome_feriado_aberto"),
        "observacao_feriado_aberto": dados.get("observacao_feriado_aberto"),

        "motivo_fechamento": dados.get("motivo_fechamento"),

        "segunda_a_sexta": dados.get("horario_funcionamento", {}).get("segunda_a_sexta"),
        "sabado": dados.get("horario_funcionamento", {}).get("sabado"),
        "domingo": dados.get("horario_funcionamento", {}).get("domingo"),
        "feriados_fechados": dados.get("horario_funcionamento", {}).get("feriados_fechados"),
        "feriados_com_loja_aberta": dados.get("horario_funcionamento", {}).get("feriados_com_loja_aberta")
    }

    return item


def montar_payload_inicio_botconversa(tipo_consulta="inicio"):
    item = montar_item_inicio_botconversa()

    message = (
        f"{item['data_extenso']} - {item['hora_atual']} - "
        f"{item['mensagem_atendimento']}"
    )

    resposta = {
        "ok": True,
        "tipo_consulta": tipo_consulta,
        "total_encontrado": 1,
        "total_retornado": 1,
        "message": message,
        "items": [item]
    }

    resposta.update(item)

    return resposta


def responder(dados, titulo, subtitulo, status_texto=None, calendario=None, tempo_real=False):
    if quer_visual():
        return render_visual(titulo, subtitulo, dados, status_texto, calendario, tempo_real)
    return jsonify(dados)


CSS_PEG = """
<style>
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  min-height: 100vh;
  padding: 24px;
  font-family: Arial, Helvetica, sans-serif;
  color: #e5f4ff;
  background:
    radial-gradient(circle at top left, rgba(0, 200, 255, 0.20), transparent 34%),
    radial-gradient(circle at top right, rgba(0, 92, 255, 0.22), transparent 32%),
    linear-gradient(135deg, #020617 0%, #071527 45%, #020617 100%);
}

.page {
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
}

.hero {
  border: 1px solid rgba(0, 200, 255, 0.22);
  border-radius: 26px;
  padding: 28px;
  background:
    linear-gradient(145deg, rgba(15, 23, 42, 0.94), rgba(2, 6, 23, 0.72)),
    radial-gradient(circle at 30% 20%, rgba(0, 200, 255, 0.16), transparent 35%);
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.35);
}

.topbar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.logo {
  width: 74px;
  height: 74px;
  border-radius: 20px;
  object-fit: contain;
  padding: 10px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(0, 200, 255, 0.24);
}

h1 {
  margin: 0;
  font-size: 26px;
  color: #ffffff;
}

.subtitle {
  margin: 6px 0 0;
  color: #94a3b8;
  font-size: 14px;
}

.grid {
  display: grid;
  grid-template-columns: 1.3fr 0.7fr;
  gap: 20px;
}

.card {
  border-radius: 22px;
  padding: 26px;
  background: rgba(2, 6, 23, 0.62);
  border: 1px solid rgba(148, 163, 184, 0.16);
}

.label {
  color: #00c8ff;
  text-transform: uppercase;
  letter-spacing: 1.4px;
  font-weight: 900;
  font-size: 12px;
  margin-bottom: 12px;
}

.date {
  font-size: 30px;
  font-weight: 900;
  color: #ffffff;
  margin-bottom: 16px;
  text-transform: capitalize;
}

.clock {
  font-size: 92px;
  line-height: 1;
  font-weight: 900;
  color: #ffffff;
  text-shadow:
    0 0 22px rgba(0, 200, 255, 0.22),
    0 0 52px rgba(0, 92, 255, 0.18);
}

.status {
  padding: 16px;
  border-radius: 18px;
  font-weight: 900;
  line-height: 1.45;
  background: rgba(0, 200, 255, 0.08);
  border: 1px solid rgba(0, 200, 255, 0.28);
}

.status.closed {
  background: rgba(239, 68, 68, 0.10);
  border-color: rgba(239, 68, 68, 0.35);
  color: #fee2e2;
}

.status.open {
  background: rgba(34, 197, 94, 0.12);
  border-color: rgba(34, 197, 94, 0.35);
  color: #dcfce7;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-top: 18px;
}

.info {
  padding: 14px;
  border-radius: 16px;
  background: rgba(15, 23, 42, 0.48);
  border: 1px solid rgba(0, 200, 255, 0.13);
}

.info span {
  display: block;
  color: #94a3b8;
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
  margin-bottom: 6px;
}

.info strong {
  color: #ffffff;
  font-size: 15px;
}

.endpoints {
  display: grid;
  gap: 10px;
  margin-top: 20px;
}

.endpoint {
  display: block;
  color: #e0f2fe;
  text-decoration: none;
  background: linear-gradient(135deg, rgba(0, 92, 255, 0.16), rgba(0, 200, 255, 0.06));
  border: 1px solid rgba(0, 200, 255, 0.16);
  border-radius: 14px;
  padding: 12px 14px;
  font-size: 14px;
  font-weight: 800;
  word-break: break-word;
}

.json {
  margin-top: 20px;
  padding: 18px;
  border-radius: 18px;
  background: rgba(2, 6, 23, 0.86);
  color: #dbeafe;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  overflow: auto;
  max-height: 520px;
}

@media (max-width: 900px) {
  .grid {
    grid-template-columns: 1fr;
  }

  .clock {
    font-size: 64px;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }
}
</style>
"""


def render_visual(titulo, subtitulo, dados, status_texto=None, calendario=None, tempo_real=False):
    json_formatado = json.dumps(dados, ensure_ascii=False, indent=2)

    data_extenso = dados.get("data_extenso") or dados.get("hoje", {}).get("data_extenso") or "Consulta PEG"
    hora_atual = dados.get("hora_atual") or dados.get("hoje", {}).get("hora_atual") or "--:--:--"

    atendimento_aberto = dados.get("atendimento_aberto")
    loja_abre = dados.get("loja_abre")
    nome_feriado = dados.get("nome_feriado")

    if atendimento_aberto is True:
        status_classe = "open"
    elif loja_abre is True and not nome_feriado:
        status_classe = "open"
    else:
        status_classe = "closed"

    status_final = (
        status_texto
        or dados.get("mensagem_atendimento")
        or dados.get("mensagem_resposta")
        or "Consulta disponível"
    )

    script_tempo_real = ""

    if tempo_real:
        script_tempo_real = """
<script>
async function atualizarHorarioPeg() {
  try {
    const resposta = await fetch("/api/horario", { cache: "no-store" });
    const dados = await resposta.json();

    const dataEl = document.getElementById("dataAtualPeg");
    const horaEl = document.getElementById("horaAtualPeg");
    const statusEl = document.getElementById("statusAtualPeg");
    const jsonEl = document.getElementById("jsonAtualPeg");

    if (dataEl) dataEl.textContent = dados.data_extenso;
    if (horaEl) horaEl.textContent = dados.hora_atual;
    if (statusEl) {
      statusEl.textContent = dados.mensagem_atendimento;
      statusEl.classList.remove("open", "closed");
      statusEl.classList.add(dados.atendimento_aberto ? "open" : "closed");
    }
    if (jsonEl) jsonEl.textContent = JSON.stringify(dados, null, 2);
  } catch (erro) {
    console.log("Erro ao atualizar horário PEG", erro);
  }
}

atualizarHorarioPeg();
setInterval(atualizarHorarioPeg, 1000);
</script>
"""

    html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{titulo} - PEG do Brasil</title>
  {CSS_PEG}
</head>
<body>
  <div class="page">
    <section class="hero">
      <div class="topbar">
        <a href="/">
          <img class="logo" src="{LOGO_PEG_URL}" alt="PEG do Brasil">
        </a>
        <div>
          <h1>{titulo}</h1>
          <p class="subtitle">{subtitulo}</p>
        </div>
      </div>

      <div class="grid">
        <div class="card">
          <div class="label">Data e hora de Brasília</div>
          <div id="dataAtualPeg" class="date">{data_extenso}</div>
          <div id="horaAtualPeg" class="clock">{hora_atual}</div>
        </div>

        <div class="card">
          <div class="label">Status operacional</div>
          <div id="statusAtualPeg" class="status {status_classe}">{status_final}</div>

          <div class="info-grid">
            <div class="info">
              <span>Data</span>
              <strong>{dados.get("data_br", "-")}</strong>
            </div>
            <div class="info">
              <span>Dia</span>
              <strong>{dados.get("dia_semana", "-")}</strong>
            </div>
            <div class="info">
              <span>Horário</span>
              <strong>{dados.get("funcionamento_previsto_hoje", dados.get("funcionamento_previsto", "-"))}</strong>
            </div>
            <div class="info">
              <span>Situação</span>
              <strong>{dados.get("status_atendimento", "-")}</strong>
            </div>
          </div>
        </div>
      </div>

      <div class="card" style="margin-top:20px;">
        <div class="label">Endpoints</div>
        <div class="endpoints">
          <a class="endpoint" href="/api/inicio?visual=1">/api/inicio?visual=1</a>
          <a class="endpoint" href="/api/horario?visual=1">/api/horario?visual=1</a>
          <a class="endpoint" href="/api/amanha?visual=1">/api/amanha?visual=1</a>
          <a class="endpoint" href="/api/depois-de-amanha?visual=1">/api/depois-de-amanha?visual=1</a>
          <a class="endpoint" href="/api/proximo-dia/sexta?visual=1">/api/proximo-dia/sexta?visual=1</a>
          <a class="endpoint" href="/api/proximo-feriado?visual=1">/api/proximo-feriado?visual=1</a>
          <a class="endpoint" href="/api/feriados/2026?visual=1">/api/feriados/2026?visual=1</a>
          <a class="endpoint" href="/api/calendario?visual=1">/api/calendario?visual=1</a>
          <a class="endpoint" href="/api/botconversa/enviar-inicio">/api/botconversa/enviar-inicio</a>
        </div>
      </div>

      <pre id="jsonAtualPeg" class="json">{json_formatado}</pre>
    </section>
  </div>

  {script_tempo_real}
</body>
</html>
"""

    return Response(html, mimetype="text/html")


@app.route("/")
def index():
    dados = obter_dados_horario()
    agora = datetime.now(TIMEZONE_BRASILIA)
    calendario_mes = gerar_calendario_mes(agora.year, agora.month)

    return render_visual(
        "Horário e Calendário PEG",
        "Base de consulta para a Sam - BotConversa",
        dados,
        dados.get("mensagem_atendimento"),
        calendario_mes,
        tempo_real=True
    )


@app.route("/api/inicio", methods=["GET", "POST"])
def api_inicio():
    corpo_recebido = request.get_json(silent=True) or {}
    consulta = str(corpo_recebido.get("consulta") or request.args.get("consulta") or "inicio").strip()

    return jsonify(montar_payload_inicio_botconversa(consulta))


@app.route("/api/botconversa/enviar-inicio", methods=["GET", "POST"])
def enviar_inicio_para_botconversa():
    webhook_url = BOTCONVERSA_WEBHOOK_URL

    if not webhook_url:
        return jsonify({
            "ok": False,
            "message": "BOTCONVERSA_WEBHOOK_URL não configurada."
        }), 500

    corpo_recebido = request.get_json(silent=True) or {}
    consulta = str(corpo_recebido.get("consulta") or request.args.get("consulta") or "inicio").strip()
    payload = montar_payload_inicio_botconversa(consulta)

    try:
        resposta = requests.post(
            webhook_url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            timeout=30
        )

        return jsonify({
            "ok": True,
            "message": "Webhook enviado para o BotConversa.",
            "status_code_botconversa": resposta.status_code,
            "resposta_botconversa": resposta.text,
            "payload_enviado": payload
        })

    except Exception as erro:
        return jsonify({
            "ok": False,
            "message": "Erro ao enviar webhook para o BotConversa.",
            "erro": str(erro),
            "payload_tentado": payload
        }), 500


@app.route("/api/horario", methods=["GET", "POST"])
def api_horario():
    dados = obter_dados_horario()
    agora = datetime.now(TIMEZONE_BRASILIA)
    calendario_mes = gerar_calendario_mes(agora.year, agora.month)

    return responder(
        dados,
        "Horário atual",
        "Consulta de data e hora atual da PEG",
        dados.get("mensagem_atendimento"),
        calendario_mes,
        tempo_real=True
    )


@app.route("/api/amanha", methods=["GET", "POST"])
def api_amanha():
    hoje = datetime.now(TIMEZONE_BRASILIA).date()
    amanha = hoje + timedelta(days=1)

    dados = gerar_dados_data(amanha.year, amanha.month, amanha.day)
    dados["tipo_consulta"] = "amanha"

    return responder(
        dados,
        "Consulta de amanhã",
        "Funcionamento previsto para amanhã",
        dados.get("mensagem_resposta")
    )


@app.route("/api/depois-de-amanha", methods=["GET", "POST"])
def api_depois_de_amanha():
    hoje = datetime.now(TIMEZONE_BRASILIA).date()
    depois = hoje + timedelta(days=2)

    dados = gerar_dados_data(depois.year, depois.month, depois.day)
    dados["tipo_consulta"] = "depois_de_amanha"

    return responder(
        dados,
        "Consulta de depois de amanhã",
        "Funcionamento previsto para depois de amanhã",
        dados.get("mensagem_resposta")
    )


@app.route("/api/proximo-dia/<string:dia_nome>", methods=["GET", "POST"])
def api_proximo_dia(dia_nome):
    chave = dia_nome.lower().strip()

    if chave not in DIAS_ENDPOINT:
        return jsonify({
            "erro": True,
            "mensagem": "Dia inválido. Use segunda, terca, quarta, quinta, sexta, sabado ou domingo."
        }), 400

    dados = proxima_data_por_dia_semana(DIAS_ENDPOINT[chave])
    dados["tipo_consulta"] = "proximo_dia"
    dados["consulta"] = f"próximo dia: {dia_nome}"

    return responder(
        dados,
        f"Próximo {dados['dia_semana']}",
        "Consulta de próximo dia da semana",
        dados.get("mensagem_resposta")
    )


@app.route("/api/proximo-feriado", methods=["GET", "POST"])
def api_proximo_feriado():
    dados = proximo_feriado()

    if dados is None:
        return jsonify({
            "erro": True,
            "mensagem": "Não foi possível localizar próximo feriado."
        }), 404

    return responder(
        dados,
        "Próximo feriado",
        "Consulta do próximo feriado ou data cadastrada",
        dados.get("mensagem_resposta")
    )


@app.route("/api/data/<string:data_texto>", methods=["GET", "POST"])
def api_data_especifica(data_texto):
    try:
        partes = data_texto.split("-")

        if len(partes) != 3:
            return jsonify({
                "erro": True,
                "mensagem": "Formato inválido. Use AAAA-MM-DD."
            }), 400

        ano = int(partes[0])
        mes = int(partes[1])
        dia = int(partes[2])

        dados = gerar_dados_data(ano, mes, dia)

        if dados is None:
            return jsonify({
                "erro": True,
                "mensagem": "Data inválida."
            }), 400

        dados["tipo_consulta"] = "data_especifica"

        return responder(
            dados,
            "Consulta de data específica",
            "Funcionamento previsto para a data solicitada",
            dados.get("mensagem_resposta")
        )

    except Exception:
        return jsonify({
            "erro": True,
            "mensagem": "Não foi possível consultar a data. Use AAAA-MM-DD."
        }), 400


@app.route("/api/feriados/<int:ano>", methods=["GET", "POST"])
def api_feriados_ano(ano):
    if ano < 1 or ano > 9999:
        return jsonify({
            "erro": True,
            "mensagem": "Ano inválido."
        }), 400

    dados = listar_feriados_ano(ano)
    dados["hoje"] = obter_dados_horario()

    return responder(
        dados,
        f"Feriados {ano}",
        "Datas fechadas e datas com loja aberta cadastradas para a PEG",
        f"{dados['total_feriados']} datas cadastradas"
    )


@app.route("/api/calendario", methods=["GET", "POST"])
def api_calendario_mes_atual():
    agora = datetime.now(TIMEZONE_BRASILIA)
    calendario_mes = gerar_calendario_mes(agora.year, agora.month)

    if calendario_mes is None:
        return jsonify({
            "erro": True,
            "mensagem": "Não foi possível gerar o calendário."
        }), 400

    calendario_mes["hoje"] = obter_dados_horario()
    calendario_mes["tipo_consulta"] = "mes_atual"

    return responder(
        calendario_mes,
        f"Calendário de {calendario_mes['mes_nome']} de {calendario_mes['ano']}",
        "Calendário operacional da PEG",
        f"{calendario_mes['total_dias']} dias no mês",
        calendario_mes,
        tempo_real=True
    )


@app.route("/api/calendario/<int:ano>", methods=["GET", "POST"])
def api_calendario_ano(ano):
    if ano < 1 or ano > 9999:
        return jsonify({
            "erro": True,
            "mensagem": "Ano inválido."
        }), 400

    dados = gerar_calendario_ano(ano)
    dados["hoje"] = obter_dados_horario()
    dados["tipo_consulta"] = "ano_completo"

    return responder(
        dados,
        f"Calendário {ano}",
        "Consulta do calendário anual da PEG",
        "Calendário anual disponível"
    )


@app.route("/api/calendario/<int:ano>/<int:mes>", methods=["GET", "POST"])
def api_calendario_mes(ano, mes):
    if ano < 1 or ano > 9999:
        return jsonify({
            "erro": True,
            "mensagem": "Ano inválido."
        }), 400

    if mes < 1 or mes > 12:
        return jsonify({
            "erro": True,
            "mensagem": "Mês inválido. Use um mês entre 1 e 12."
        }), 400

    calendario_mes = gerar_calendario_mes(ano, mes)

    if calendario_mes is None:
        return jsonify({
            "erro": True,
            "mensagem": "Não foi possível gerar o calendário solicitado."
        }), 400

    calendario_mes["hoje"] = obter_dados_horario()
    calendario_mes["tipo_consulta"] = "mes_especifico"

    return responder(
        calendario_mes,
        f"Calendário de {calendario_mes['mes_nome']} de {calendario_mes['ano']}",
        "Consulta do calendário mensal da PEG",
        f"{calendario_mes['total_dias']} dias no mês",
        calendario_mes
    )


@app.route("/health")
def health():
    return jsonify({
        "status": "online",
        "servico": "horario-calendario-feriados-peg"
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
