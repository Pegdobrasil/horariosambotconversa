from flask import Flask, jsonify, Response, request
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import calendar
import json
import os

app = Flask(__name__)

TIMEZONE_BRASILIA = ZoneInfo("America/Sao_Paulo")

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

    datas = {
        date(ano, 1, 1): {
            "nome": "Confraternização Universal",
            "tipo": "feriado_nacional"
        },
        sexta_feira_santa: {
            "nome": "Sexta-feira Santa",
            "tipo": "feriado_nacional"
        },
        date(ano, 4, 21): {
            "nome": "Tiradentes",
            "tipo": "feriado_nacional"
        },
        date(ano, 5, 1): {
            "nome": "Dia do Trabalho",
            "tipo": "feriado_nacional"
        },
        corpus_christi: {
            "nome": "Corpus Christi",
            "tipo": "data_especial"
        },
        date(ano, 9, 7): {
            "nome": "Independência do Brasil",
            "tipo": "feriado_nacional"
        },
        date(ano, 9, 8): {
            "nome": "Nossa Senhora da Luz dos Pinhais, padroeira de Curitiba",
            "tipo": "feriado_municipal"
        },
        date(ano, 10, 12): {
            "nome": "Nossa Senhora Aparecida",
            "tipo": "feriado_nacional"
        },
        date(ano, 11, 2): {
            "nome": "Finados",
            "tipo": "feriado_nacional"
        },
        date(ano, 11, 15): {
            "nome": "Proclamação da República",
            "tipo": "feriado_nacional"
        },
        date(ano, 11, 20): {
            "nome": "Dia Nacional de Zumbi e da Consciência Negra",
            "tipo": "feriado_nacional"
        },
        date(ano, 12, 25): {
            "nome": "Natal",
            "tipo": "feriado_nacional"
        }
    }

    return datas


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
            "motivo_fechamento": f"{item['nome']}"
        }

    return {
        "eh_feriado_nacional": False,
        "eh_feriado_municipal": False,
        "eh_data_especial": False,
        "nome_feriado": None,
        "tipo_fechamento": None,
        "motivo_fechamento": None
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
        "motivo_fechamento": dados_data["motivo_fechamento"],
        "horario_funcionamento": {
            "segunda_a_sexta": "09:00 às 18:00",
            "sabado": "09:00 às 13:00",
            "domingo": "Fechado",
            "feriados_nacionais": "Fechado",
            "feriados_municipais_cadastrados": "Fechado",
            "datas_especiais_cadastradas": "Fechado"
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
            "motivo_fechamento": item["nome"]
        })

    return {
        "ano": ano,
        "tipo_consulta": "feriados_e_datas_fechadas",
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

    for ano in range(hoje.year, hoje.year + 3):
        for data_fechada, item in sorted(obter_datas_fechadas(ano).items()):
            if data_fechada >= hoje:
                dados = gerar_dados_data(data_fechada.year, data_fechada.month, data_fechada.day)
                dados["tipo_consulta"] = "proximo_feriado"
                return dados

    return None


def quer_visual():
    return request.args.get("visual") in ["1", "true", "sim", "html"]


CSS_PEG = """
<style>
* {
  box-sizing: border-box;
}

:root {
  --peg-blue: #005cff;
  --peg-cyan: #00c8ff;
  --peg-dark: #020617;
  --peg-card: rgba(15, 23, 42, 0.78);
  --peg-border: rgba(0, 200, 255, 0.22);
  --peg-text: #e5f4ff;
  --peg-muted: #94a3b8;
  --peg-green: #22c55e;
  --peg-red: #ef4444;
  --peg-yellow: #facc15;
}

body {
  margin: 0;
  min-height: 100vh;
  padding: 28px 14px;
  font-family: Arial, Helvetica, sans-serif;
  background:
    radial-gradient(circle at top left, rgba(0, 200, 255, 0.20), transparent 34%),
    radial-gradient(circle at top right, rgba(0, 92, 255, 0.22), transparent 32%),
    linear-gradient(135deg, #020617 0%, #071527 45%, #020617 100%);
  color: var(--peg-text);
  overflow-x: hidden;
}

body::before {
  content: "";
  position: fixed;
  inset: 0;
  background:
    linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px);
  background-size: 42px 42px;
  mask-image: linear-gradient(to bottom, rgba(0,0,0,0.8), transparent 85%);
  pointer-events: none;
}

.page {
  width: 100%;
  max-width: 1180px;
  margin: 0 auto;
  position: relative;
  z-index: 2;
}

.hero {
  position: relative;
  overflow: hidden;
  border: 1px solid var(--peg-border);
  border-radius: 28px;
  padding: 28px;
  background:
    linear-gradient(145deg, rgba(15, 23, 42, 0.94), rgba(2, 6, 23, 0.72)),
    radial-gradient(circle at 30% 20%, rgba(0, 200, 255, 0.16), transparent 35%);
  box-shadow:
    0 24px 80px rgba(0, 0, 0, 0.35),
    0 0 55px rgba(0, 92, 255, 0.18);
  backdrop-filter: blur(14px);
}

.hero::after {
  content: "";
  position: absolute;
  inset: 0;
  background-image: url("https://github.com/Pegdobrasil/peg-imagens-site/blob/main/logo%20branca.png?raw=true");
  background-repeat: no-repeat;
  background-position: right 36px top 28px;
  background-size: 220px auto;
  opacity: 0.06;
  pointer-events: none;
}

.hero-content {
  position: relative;
  z-index: 2;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 28px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
}

.brand-mark {
  width: 56px;
  height: 56px;
  border-radius: 18px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, var(--peg-blue), var(--peg-cyan));
  box-shadow: 0 0 28px rgba(0, 200, 255, 0.35);
  font-weight: 900;
  color: white;
  letter-spacing: -1px;
  font-size: 18px;
}

.brand-title {
  margin: 0;
  font-size: 20px;
  line-height: 1.1;
  color: white;
  font-weight: 900;
}

.brand-subtitle {
  margin: 4px 0 0;
  color: var(--peg-muted);
  font-size: 13px;
}

.live-pill {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  padding: 10px 14px;
  border-radius: 999px;
  color: #dff7ff;
  background: rgba(0, 200, 255, 0.08);
  border: 1px solid rgba(0, 200, 255, 0.28);
  font-size: 13px;
  font-weight: 800;
  white-space: nowrap;
}

.live-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--peg-green);
  box-shadow: 0 0 16px rgba(34, 197, 94, 0.85);
}

.main-grid {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 22px;
  align-items: stretch;
}

.clock-card,
.status-card {
  border-radius: 24px;
  padding: 28px;
  background:
    radial-gradient(circle at top left, rgba(0, 200, 255, 0.18), transparent 36%),
    rgba(2, 6, 23, 0.58);
  border: 1px solid rgba(148, 163, 184, 0.16);
  box-shadow: inset 0 0 35px rgba(0, 200, 255, 0.04);
}

.label {
  color: var(--peg-cyan);
  text-transform: uppercase;
  letter-spacing: 1.6px;
  font-weight: 900;
  font-size: 12px;
  margin-bottom: 12px;
}

.date {
  font-size: clamp(22px, 3vw, 34px);
  font-weight: 900;
  color: #ffffff;
  margin-bottom: 20px;
  text-transform: capitalize;
}

.clock {
  font-size: clamp(58px, 10vw, 120px);
  line-height: 0.9;
  font-weight: 900;
  letter-spacing: -4px;
  color: white;
  text-shadow:
    0 0 22px rgba(0, 200, 255, 0.22),
    0 0 52px rgba(0, 92, 255, 0.18);
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 900;
  border: 1px solid rgba(0, 200, 255, 0.28);
  background: rgba(0, 200, 255, 0.08);
  color: #dff7ff;
}

.status-badge.closed {
  border-color: rgba(239, 68, 68, 0.35);
  background: rgba(239, 68, 68, 0.10);
  color: #fee2e2;
}

.status-badge.holiday {
  border-color: rgba(250, 204, 21, 0.42);
  background: rgba(250, 204, 21, 0.12);
  color: #fef9c3;
}

.panel {
  border-radius: 24px;
  background: rgba(15, 23, 42, 0.74);
  border: 1px solid rgba(0, 200, 255, 0.14);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.26);
  overflow: hidden;
  margin-top: 22px;
}

.panel-header {
  padding: 18px 20px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.12);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.panel-title {
  margin: 0;
  color: white;
  font-size: 18px;
  font-weight: 900;
}

.panel-subtitle {
  margin: 4px 0 0;
  color: var(--peg-muted);
  font-size: 13px;
}

.panel-body {
  padding: 18px 20px 20px;
}

.endpoints-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.endpoint {
  display: block;
  color: #e0f2fe;
  text-decoration: none;
  background:
    linear-gradient(135deg, rgba(0, 92, 255, 0.16), rgba(0, 200, 255, 0.06));
  border: 1px solid rgba(0, 200, 255, 0.16);
  border-radius: 15px;
  padding: 13px 14px;
  font-size: 14px;
  font-weight: 800;
  word-break: break-word;
}

.endpoint:hover {
  border-color: rgba(0, 200, 255, 0.42);
  box-shadow: 0 0 24px rgba(0, 200, 255, 0.13);
}

.json {
  margin: 0;
  padding: 18px 20px 22px;
  color: #dbeafe;
  text-align: left;
  font-size: 13px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 520px;
  overflow: auto;
  background: rgba(2, 6, 23, 0.86);
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  background: rgba(2, 6, 23, 0.50);
}

.day-name {
  padding: 12px 6px;
  text-align: center;
  color: #bfdbfe;
  font-size: 12px;
  font-weight: 900;
  border-bottom: 1px solid rgba(148, 163, 184, 0.16);
  background: rgba(2, 6, 23, 0.40);
}

.day {
  min-height: 82px;
  padding: 9px;
  border-right: 1px solid rgba(148, 163, 184, 0.10);
  border-bottom: 1px solid rgba(148, 163, 184, 0.10);
  background: rgba(15, 23, 42, 0.48);
}

.day.empty {
  background: rgba(15, 23, 42, 0.20);
}

.day.today {
  background: rgba(0, 92, 255, 0.18);
  outline: 2px solid rgba(0, 200, 255, 0.70);
  outline-offset: -2px;
}

.day.closed {
  background: rgba(127, 29, 29, 0.30);
  outline: 1px solid rgba(250, 204, 21, 0.42);
  outline-offset: -1px;
}

.day-number {
  font-size: 17px;
  color: white;
  font-weight: 900;
}

.day-info {
  margin-top: 7px;
  color: var(--peg-muted);
  font-size: 11px;
  line-height: 1.25;
}

.footer {
  text-align: center;
  color: var(--peg-muted);
  margin-top: 22px;
  font-size: 13px;
}

@media (max-width: 920px) {
  .main-grid,
  .endpoints-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 620px) {
  body {
    padding: 14px;
  }

  .hero {
    padding: 18px;
    border-radius: 22px;
  }

  .topbar {
    flex-direction: column;
    align-items: flex-start;
  }

  .clock-card,
  .status-card {
    padding: 20px;
  }

  .clock {
    letter-spacing: -2px;
  }

  .day {
    min-height: 58px;
    padding: 5px;
  }

  .day-info {
    display: none;
  }

  .day-name {
    font-size: 10px;
    padding: 9px 3px;
  }

  .day-number {
    font-size: 14px;
  }
}
</style>
"""


def endpoint_cards():
    endpoints = [
        ("/api/horario", "Horário atual"),
        ("/api/amanha", "Amanhã"),
        ("/api/depois-de-amanha", "Depois de amanhã"),
        ("/api/proximo-dia/sexta", "Próxima sexta"),
        ("/api/proximo-feriado", "Próximo feriado"),
        ("/api/feriados/2026", "Feriados 2026"),
        ("/api/calendario", "Calendário atual"),
        ("/api/data/2026-05-01", "Data específica")
    ]

    html = ""

    for url, nome in endpoints:
        html += f'<a class="endpoint" href="{url}?visual=1"><strong>{nome}</strong><br>{url}?visual=1</a>'

    return html


def render_visual(titulo, subtitulo, dados, status_texto=None, calendario=None):
    json_formatado = json.dumps(dados, ensure_ascii=False, indent=2)

    data_extenso = dados.get("data_extenso") or dados.get("hoje", {}).get("data_extenso") or "Consulta PEG"
    hora_atual = dados.get("hora_atual") or dados.get("hoje", {}).get("hora_atual") or "--:--:--"

    loja_abre = dados.get("loja_abre")
    atendimento_aberto = dados.get("atendimento_aberto")
    nome_feriado = dados.get("nome_feriado")

    badge_class = ""

    if nome_feriado:
        badge_class = "holiday"
        status_final = f"Fechado: {nome_feriado}"
    elif loja_abre is False or atendimento_aberto is False:
        badge_class = "closed"
        status_final = status_texto or dados.get("mensagem_atendimento") or dados.get("mensagem_resposta") or "Fechado"
    else:
        status_final = status_texto or dados.get("mensagem_atendimento") or dados.get("mensagem_resposta") or "Consulta disponível"

    calendario_html = ""

    if calendario:
        nomes_dias = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

        calendario_html += """
        <section class="panel">
          <div class="panel-header">
            <div>
              <h2 class="panel-title">Calendário visual</h2>
              <p class="panel-subtitle">Dias de atendimento e datas fechadas</p>
            </div>
          </div>
          <div class="calendar-grid">
        """

        for nome in nomes_dias:
            calendario_html += f'<div class="day-name">{nome}</div>'

        hoje = datetime.now(TIMEZONE_BRASILIA).date().strftime("%Y-%m-%d")

        for semana in calendario["semanas"]:
            for dia in semana:
                if dia is None:
                    calendario_html += '<div class="day empty"></div>'
                else:
                    classes = ["day"]

                    if dia["data"] == hoje:
                        classes.append("today")

                    if dia["loja_abre"] is False:
                        classes.append("closed")

                    classe = " ".join(classes)

                    info = dia["funcionamento_previsto"]

                    if dia["nome_feriado"]:
                        info = dia["nome_feriado"]

                    calendario_html += f"""
                    <div class="{classe}">
                      <div class="day-number">{dia["dia"]}</div>
                      <div class="day-info">{dia["dia_semana"]}</div>
                      <div class="day-info">{info}</div>
                    </div>
                    """

        calendario_html += """
          </div>
        </section>
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
      <div class="hero-content">

        <div class="topbar">
          <div class="brand">
            <div class="brand-mark">PEG</div>
            <div>
              <h1 class="brand-title">{titulo}</h1>
              <p class="brand-subtitle">{subtitulo}</p>
            </div>
          </div>

          <div class="live-pill">
            <span class="live-dot"></span>
            API PEG ativa
          </div>
        </div>

        <div class="main-grid">
          <div class="clock-card">
            <div class="label">Consulta</div>
            <div class="date">{data_extenso.capitalize()}</div>
            <div class="clock">{hora_atual}</div>
          </div>

          <div class="status-card">
            <div class="label">Status</div>
            <div class="status-badge {badge_class}">
              {status_final}
            </div>
          </div>
        </div>

      </div>
    </section>

    <section class="panel">
      <div class="panel-header">
        <div>
          <h2 class="panel-title">Endpoints visuais</h2>
          <p class="panel-subtitle">Use sem ?visual=1 para retorno JSON no BotConversa</p>
        </div>
      </div>
      <div class="panel-body">
        <div class="endpoints-grid">
          {endpoint_cards()}
        </div>
      </div>
    </section>

    {calendario_html}

    <section class="panel">
      <div class="panel-header">
        <div>
          <h2 class="panel-title">Resposta JSON</h2>
          <p class="panel-subtitle">Dados retornados pela API</p>
        </div>
      </div>
      <pre class="json">{json_formatado}</pre>
    </section>

    <div class="footer">
      PEG do Brasil - Sistema de data, hora, calendário e feriados para atendimento automatizado
    </div>

  </div>
</body>
</html>
"""

    return Response(html, mimetype="text/html")


def responder(dados, titulo, subtitulo, status_texto=None, calendario=None):
    if quer_visual():
        return render_visual(titulo, subtitulo, dados, status_texto, calendario)
    return jsonify(dados)


@app.route("/")
def index():
    dados = obter_dados_horario()
    return render_visual(
        "Horário e Calendário PEG",
        "Base de consulta para a Sam - BotConversa",
        dados,
        dados.get("mensagem_atendimento")
    )


@app.route("/api/horario")
def api_horario():
    dados = obter_dados_horario()
    return responder(
        dados,
        "Horário atual",
        "Consulta de data e hora atual da PEG",
        dados.get("mensagem_atendimento")
    )


@app.route("/api/amanha")
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


@app.route("/api/depois-de-amanha")
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


@app.route("/api/proximo-dia/<string:dia_nome>")
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


@app.route("/api/proximo-feriado")
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
        "Consulta do próximo feriado ou data fechada",
        dados.get("mensagem_resposta")
    )


@app.route("/api/data/<string:data_texto>")
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


@app.route("/api/feriados/<int:ano>")
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
        "Datas fechadas cadastradas para a PEG",
        f"{dados['total_feriados']} datas cadastradas como fechadas"
    )


@app.route("/api/calendario")
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
        calendario_mes
    )


@app.route("/api/calendario/<int:ano>")
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


@app.route("/api/calendario/<int:ano>/<int:mes>")
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
