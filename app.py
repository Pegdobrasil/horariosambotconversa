from flask import Flask, jsonify, Response, request
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import calendar
import json
import os

app = Flask(__name__)

TIMEZONE_BRASILIA = ZoneInfo("America/Sao_Paulo")

LOGO_PEG_URL = "https://magazord-public.s3.sa-east-1.amazonaws.com/pegdobrasil/img/2025/03/banner/138072/medium/logo-vazia.png"

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
  padding: 30px 18px;
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
  max-width: 1540px;
  margin: 0 auto;
  position: relative;
  z-index: 2;
}

.hero {
  position: relative;
  overflow: hidden;
  border: 1px solid var(--peg-border);
  border-radius: 30px;
  padding: 32px;
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
  background-position: right 42px top 32px;
  background-size: 260px auto;
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
  margin-bottom: 30px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 16px;
}

.brand-mark {
  width: 82px;
  height: 82px;
  border-radius: 22px;
  display: grid;
  place-items: center;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(0, 200, 255, 0.24);
  box-shadow: 0 0 28px rgba(0, 200, 255, 0.25);
  padding: 11px;
}

.brand-logo {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}

.brand-title {
  margin: 0;
  font-size: 24px;
  line-height: 1.1;
  color: white;
  font-weight: 900;
}

.brand-subtitle {
  margin: 5px 0 0;
  color: var(--peg-muted);
  font-size: 14px;
}

.live-pill {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  padding: 11px 16px;
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
  animation: pulse 1.4s infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }

  50% {
    transform: scale(1.35);
    opacity: 0.65;
  }
}

.main-grid {
  display: grid;
  grid-template-columns: 1.28fr 0.72fr;
  gap: 26px;
  align-items: stretch;
}

.clock-card,
.status-card {
  border-radius: 26px;
  padding: 32px;
  background:
    radial-gradient(circle at top left, rgba(0, 200, 255, 0.18), transparent 36%),
    rgba(2, 6, 23, 0.58);
  border: 1px solid rgba(148, 163, 184, 0.16);
  box-shadow: inset 0 0 35px rgba(0, 200, 255, 0.04);
}

.clock-card {
  min-height: 360px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 70px 36px 44px;
  position: relative;
}

.clock-card .label {
  position: absolute;
  top: 28px;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  text-align: center;
}

.label {
  color: var(--peg-cyan);
  text-transform: uppercase;
  letter-spacing: 1.6px;
  font-weight: 900;
  font-size: 12px;
  margin-bottom: 14px;
}

.date {
  font-size: clamp(26px, 2.8vw, 42px);
  font-weight: 900;
  color: #ffffff;
  margin-bottom: 26px;
  text-transform: capitalize;
  max-width: 100%;
}

.clock {
  font-size: clamp(78px, 8vw, 150px);
  line-height: 0.9;
  font-weight: 900;
  letter-spacing: -4px;
  color: white;
  text-align: center;
  text-shadow:
    0 0 22px rgba(0, 200, 255, 0.22),
    0 0 52px rgba(0, 92, 255, 0.18);
  transition: transform 0.18s ease, text-shadow 0.18s ease;
}

.clock.tick {
  transform: scale(1.015);
  text-shadow:
    0 0 28px rgba(0, 200, 255, 0.34),
    0 0 70px rgba(0, 92, 255, 0.28);
}

.status-card {
  position: relative;
  overflow: hidden;
  background:
    radial-gradient(circle at top right, rgba(0, 200, 255, 0.20), transparent 38%),
    radial-gradient(circle at bottom left, rgba(0, 92, 255, 0.18), transparent 40%),
    rgba(2, 6, 23, 0.66);
}

.status-content {
  position: relative;
  z-index: 2;
}

.status-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.status-orb {
  width: 82px;
  height: 82px;
  min-width: 82px;
  border-radius: 24px;
  display: grid;
  place-items: center;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(0, 200, 255, 0.20);
  padding: 12px;
  transition: 0.25s ease;
}

.status-orb img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}

.status-orb.open {
  border-color: rgba(34, 197, 94, 0.48);
  animation: statusFadeGreen 2.8s ease-in-out infinite;
}

.status-orb.closed {
  border-color: rgba(239, 68, 68, 0.52);
  animation: statusFadeRed 2.8s ease-in-out infinite;
}

.status-orb.holiday {
  border-color: rgba(250, 204, 21, 0.52);
  animation: statusFadeYellow 2.8s ease-in-out infinite;
}

@keyframes statusFadeGreen {
  0%, 100% {
    box-shadow:
      0 0 16px rgba(34, 197, 94, 0.16),
      0 0 34px rgba(34, 197, 94, 0.10),
      inset 0 0 16px rgba(34, 197, 94, 0.05);
    background: rgba(34, 197, 94, 0.04);
  }

  50% {
    box-shadow:
      0 0 34px rgba(34, 197, 94, 0.55),
      0 0 74px rgba(34, 197, 94, 0.32),
      inset 0 0 26px rgba(34, 197, 94, 0.14);
    background: rgba(34, 197, 94, 0.14);
  }
}

@keyframes statusFadeRed {
  0%, 100% {
    box-shadow:
      0 0 16px rgba(239, 68, 68, 0.16),
      0 0 34px rgba(239, 68, 68, 0.10),
      inset 0 0 16px rgba(239, 68, 68, 0.05);
    background: rgba(239, 68, 68, 0.04);
  }

  50% {
    box-shadow:
      0 0 34px rgba(239, 68, 68, 0.58),
      0 0 74px rgba(239, 68, 68, 0.34),
      inset 0 0 26px rgba(239, 68, 68, 0.15);
    background: rgba(239, 68, 68, 0.14);
  }
}

@keyframes statusFadeYellow {
  0%, 100% {
    box-shadow:
      0 0 16px rgba(250, 204, 21, 0.16),
      0 0 34px rgba(250, 204, 21, 0.10),
      inset 0 0 16px rgba(250, 204, 21, 0.05);
    background: rgba(250, 204, 21, 0.04);
  }

  50% {
    box-shadow:
      0 0 34px rgba(250, 204, 21, 0.58),
      0 0 74px rgba(250, 204, 21, 0.34),
      inset 0 0 26px rgba(250, 204, 21, 0.15);
    background: rgba(250, 204, 21, 0.14);
  }
}

.status-text-block {
  flex: 1;
}

.status-overline {
  color: var(--peg-cyan);
  font-size: 11px;
  letter-spacing: 1.4px;
  text-transform: uppercase;
  font-weight: 900;
  margin-bottom: 7px;
}

.status-title {
  color: white;
  font-size: 24px;
  font-weight: 900;
  line-height: 1.12;
  margin: 0;
}

.status-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  width: 100%;
  gap: 10px;
  padding: 14px 18px;
  border-radius: 18px;
  font-size: 14px;
  font-weight: 900;
  border: 1px solid rgba(0, 200, 255, 0.28);
  background: rgba(0, 200, 255, 0.08);
  color: #dff7ff;
  line-height: 1.4;
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

.status-badge.holiday-open {
  border-color: rgba(34, 197, 94, 0.48);
  background: rgba(34, 197, 94, 0.13);
  color: #dcfce7;
}

.status-mini-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin: 20px 0 18px;
}

.status-mini-card {
  padding: 14px;
  border-radius: 18px;
  background:
    linear-gradient(135deg, rgba(0, 92, 255, 0.12), rgba(0, 200, 255, 0.05));
  border: 1px solid rgba(0, 200, 255, 0.13);
}

.status-mini-card span {
  display: block;
  color: var(--peg-muted);
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.7px;
  margin-bottom: 7px;
}

.status-mini-card strong {
  display: block;
  color: white;
  font-size: 15px;
  line-height: 1.2;
}

.hours-list {
  display: grid;
  gap: 10px;
  margin-top: 18px;
}

.hours-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: #dbeafe;
  font-size: 14px;
  padding: 11px 12px;
  border-radius: 14px;
  border: 1px solid rgba(148, 163, 184, 0.10);
  background: rgba(15, 23, 42, 0.36);
}

.hours-item span:first-child {
  color: var(--peg-muted);
}

.hours-item strong {
  text-align: right;
}

.side-grid {
  display: grid;
  grid-template-columns: 0.72fr 1.28fr;
  gap: 26px;
  align-items: start;
  margin-top: 26px;
}

.panel {
  border-radius: 26px;
  background: rgba(15, 23, 42, 0.74);
  border: 1px solid rgba(0, 200, 255, 0.14);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.26);
  overflow: hidden;
}

.panel-header {
  padding: 20px 22px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.12);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.calendar-panel .panel-header {
  background:
    linear-gradient(135deg, rgba(0, 92, 255, 0.92), rgba(0, 200, 255, 0.40));
}

.calendar-header-flex {
  width: 100%;
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: center;
}

.calendar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.calendar-btn,
.calendar-today-btn {
  height: 38px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.24);
  background: rgba(2, 6, 23, 0.34);
  color: white;
  font-weight: 900;
  cursor: pointer;
  transition: 0.22s ease;
  display: grid;
  place-items: center;
  line-height: 1;
}

.calendar-btn {
  width: 38px;
  font-size: 22px;
}

.calendar-today-btn {
  padding: 0 14px;
  font-size: 12px;
  letter-spacing: 0.7px;
  text-transform: uppercase;
}

.calendar-date-input {
  height: 38px;
  min-width: 154px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.24);
  background: rgba(2, 6, 23, 0.34);
  color: white;
  padding: 0 12px;
  font-size: 13px;
  font-weight: 800;
  outline: none;
  color-scheme: dark;
}

.calendar-date-input:focus {
  border-color: rgba(0, 200, 255, 0.62);
  box-shadow: 0 0 18px rgba(0, 200, 255, 0.18);
}

.calendar-btn:hover,
.calendar-today-btn:hover {
  transform: translateY(-2px);
  background: rgba(0, 200, 255, 0.20);
  box-shadow: 0 0 22px rgba(0, 200, 255, 0.22);
}

.panel-title {
  margin: 0;
  color: white;
  font-size: 20px;
  font-weight: 900;
}

.panel-subtitle {
  margin: 5px 0 0;
  color: var(--peg-muted);
  font-size: 13px;
}

.calendar-panel .panel-subtitle {
  color: rgba(255, 255, 255, 0.78);
}

.panel-body {
  padding: 20px 22px 22px;
}

.endpoints-grid {
  display: grid;
  grid-template-columns: 1fr;
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
  padding: 14px 15px;
  font-size: 14px;
  font-weight: 800;
  word-break: break-word;
}

.endpoint:hover {
  border-color: rgba(0, 200, 255, 0.42);
  box-shadow: 0 0 24px rgba(0, 200, 255, 0.13);
}

.json-panel {
  margin-top: 26px;
}

.json {
  margin: 0;
  padding: 20px 22px 24px;
  color: #dbeafe;
  text-align: left;
  font-size: 13px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 560px;
  overflow: auto;
  background: rgba(2, 6, 23, 0.86);
}

.calendar-content {
  display: grid;
  grid-template-columns: 1fr 220px;
  gap: 0;
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  background: rgba(2, 6, 23, 0.50);
}

.calendar-legend {
  padding: 18px;
  background:
    radial-gradient(circle at top right, rgba(0, 200, 255, 0.10), transparent 48%),
    rgba(2, 6, 23, 0.62);
  border-left: 1px solid rgba(148, 163, 184, 0.14);
}

.legend-title {
  margin: 0 0 12px;
  color: white;
  font-size: 13px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.8px;
}

.legend-item {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  margin-bottom: 11px;
  color: #dbeafe;
  font-size: 12px;
  line-height: 1.35;
}

.legend-dot {
  width: 13px;
  height: 13px;
  min-width: 13px;
  border-radius: 5px;
  margin-top: 1px;
  border: 1px solid rgba(255, 255, 255, 0.20);
}

.legend-dot.open {
  background: rgba(0, 200, 255, 0.36);
  box-shadow: 0 0 12px rgba(0, 200, 255, 0.18);
}

.legend-dot.closed {
  background: rgba(239, 68, 68, 0.56);
  box-shadow: 0 0 12px rgba(239, 68, 68, 0.14);
}

.legend-dot.holiday {
  background: rgba(250, 204, 21, 0.58);
  box-shadow: 0 0 12px rgba(250, 204, 21, 0.16);
}

.legend-dot.today {
  background: rgba(34, 197, 94, 0.62);
  box-shadow: 0 0 12px rgba(34, 197, 94, 0.22);
}

.legend-dot.holiday-open {
  background: rgba(34, 197, 94, 0.62);
  box-shadow: 0 0 12px rgba(34, 197, 94, 0.22);
}

.legend-note {
  margin-top: 14px;
  padding: 12px;
  border-radius: 14px;
  background: rgba(34, 197, 94, 0.10);
  border: 1px solid rgba(34, 197, 94, 0.22);
  color: #dcfce7;
  font-size: 11px;
  line-height: 1.45;
}

.legend-note-title {
  font-weight: 900;
  color: #bbf7d0;
  margin-bottom: 8px;
}

.legend-note-list {
  margin: 0;
  padding-left: 16px;
}

.legend-note-list li {
  margin-bottom: 6px;
}

.legend-note-list li:last-child {
  margin-bottom: 0;
}

.day-name {
  padding: 13px 6px;
  text-align: center;
  color: #bfdbfe;
  font-size: 12px;
  font-weight: 900;
  border-bottom: 1px solid rgba(148, 163, 184, 0.16);
  background: rgba(2, 6, 23, 0.40);
}

.day {
  min-height: 96px;
  padding: 10px;
  border-right: 1px solid rgba(148, 163, 184, 0.10);
  border-bottom: 1px solid rgba(148, 163, 184, 0.10);
  background: rgba(15, 23, 42, 0.48);
  transition: 0.22s ease;
  position: relative;
}

.day:hover {
  background: rgba(0, 92, 255, 0.14);
  box-shadow: inset 0 0 18px rgba(0, 200, 255, 0.12);
}

.day.empty {
  background: rgba(15, 23, 42, 0.20);
}

.day.open {
  background:
    radial-gradient(circle at top right, rgba(0, 200, 255, 0.12), transparent 55%),
    rgba(15, 23, 42, 0.58);
}

.day.closed {
  background:
    radial-gradient(circle at top right, rgba(239, 68, 68, 0.14), transparent 55%),
    rgba(127, 29, 29, 0.30);
  outline: 1px solid rgba(239, 68, 68, 0.38);
  outline-offset: -1px;
}

.day.holiday {
  background:
    radial-gradient(circle at top right, rgba(250, 204, 21, 0.20), transparent 55%),
    rgba(113, 63, 18, 0.40);
  outline: 1px solid rgba(250, 204, 21, 0.55);
  outline-offset: -1px;
}

.day.holiday-open {
  background:
    radial-gradient(circle at top right, rgba(34, 197, 94, 0.26), transparent 55%),
    rgba(20, 83, 45, 0.42);
  outline: 1px solid rgba(34, 197, 94, 0.62);
  outline-offset: -1px;
  box-shadow: inset 0 0 22px rgba(34, 197, 94, 0.10);
}

.day.selected-date {
  outline: 3px solid rgba(0, 200, 255, 0.98);
  outline-offset: -3px;
  box-shadow:
    inset 0 0 26px rgba(0, 200, 255, 0.22),
    0 0 26px rgba(0, 200, 255, 0.22);
}

.day.today.open,
.day.today.holiday-open {
  background:
    radial-gradient(circle at top right, rgba(34, 197, 94, 0.32), transparent 55%),
    rgba(20, 83, 45, 0.52);
  outline: 2px solid rgba(34, 197, 94, 0.85);
  outline-offset: -2px;
  box-shadow:
    inset 0 0 24px rgba(34, 197, 94, 0.16),
    0 0 22px rgba(34, 197, 94, 0.18);
}

.day.today.closed {
  background:
    radial-gradient(circle at top right, rgba(239, 68, 68, 0.30), transparent 55%),
    rgba(127, 29, 29, 0.55);
  outline: 2px solid rgba(239, 68, 68, 0.80);
  outline-offset: -2px;
  box-shadow:
    inset 0 0 24px rgba(239, 68, 68, 0.16),
    0 0 22px rgba(239, 68, 68, 0.16);
}

.day.today.holiday {
  background:
    radial-gradient(circle at top right, rgba(250, 204, 21, 0.36), transparent 55%),
    rgba(113, 63, 18, 0.62);
  outline: 2px solid rgba(250, 204, 21, 0.90);
  outline-offset: -2px;
  box-shadow:
    inset 0 0 24px rgba(250, 204, 21, 0.16),
    0 0 22px rgba(250, 204, 21, 0.16);
}

.day-number {
  font-size: 18px;
  color: white;
  font-weight: 900;
}

.day-info {
  margin-top: 7px;
  color: var(--peg-muted);
  font-size: 11px;
  line-height: 1.25;
}

.day.open .day-info {
  color: #bfdbfe;
}

.day.closed .day-info {
  color: #fecaca;
}

.day.holiday .day-info {
  color: #fef3c7;
}

.day.holiday-open .day-info {
  color: #dcfce7;
}

.day-tag {
  display: inline-block;
  margin-top: 7px;
  padding: 3px 7px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 900;
  border: 1px solid rgba(255, 255, 255, 0.16);
}

.day-tag.open {
  color: #bbf7d0;
  background: rgba(34, 197, 94, 0.12);
  border-color: rgba(34, 197, 94, 0.28);
}

.day-tag.closed {
  color: #fecaca;
  background: rgba(239, 68, 68, 0.12);
  border-color: rgba(239, 68, 68, 0.28);
}

.day-tag.holiday {
  color: #fef3c7;
  background: rgba(250, 204, 21, 0.12);
  border-color: rgba(250, 204, 21, 0.34);
}

.day-tag.holiday-open {
  color: #dcfce7;
  background: rgba(34, 197, 94, 0.16);
  border-color: rgba(34, 197, 94, 0.38);
}

.footer {
  text-align: center;
  color: var(--peg-muted);
  margin-top: 26px;
  font-size: 13px;
}

@media (max-width: 1200px) {
  .page {
    max-width: 1120px;
  }

  .main-grid,
  .side-grid {
    grid-template-columns: 1fr;
  }

  .calendar-content {
    grid-template-columns: 1fr;
  }

  .calendar-legend {
    border-left: none;
    border-top: 1px solid rgba(148, 163, 184, 0.14);
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

  .brand-mark {
    width: 64px;
    height: 64px;
    border-radius: 18px;
  }

  .brand-title {
    font-size: 20px;
  }

  .clock-card {
    min-height: 280px;
    padding: 62px 18px 28px;
    position: relative;
  }

  .clock-card .label {
    top: 24px;
  }

  .calendar-header-flex {
    align-items: flex-start;
    flex-direction: column;
  }

  .calendar-actions {
    width: 100%;
    justify-content: space-between;
  }

  .calendar-btn {
    width: 44px;
    height: 38px;
  }

  .calendar-today-btn {
    height: 38px;
    padding: 0 12px;
  }

  .calendar-date-input {
    width: 100%;
    min-width: 100%;
  }

  .status-card {
    padding: 20px;
  }

  .status-topline {
    align-items: flex-start;
    flex-direction: column;
  }

  .status-orb {
    width: 72px;
    height: 72px;
    min-width: 72px;
    border-radius: 20px;
    padding: 11px;
  }

  .status-title {
    font-size: 20px;
  }

  .status-mini-grid {
    grid-template-columns: 1fr;
  }

  .clock {
    letter-spacing: -2px;
  }

  .day {
    min-height: 58px;
    padding: 5px;
  }

  .day-info,
  .day-tag {
    display: none;
  }

  .day-name {
    font-size: 10px;
    padding: 9px 3px;
  }

  .day-number {
    font-size: 14px;
  }

  .calendar-legend {
    display: none;
  }
}
</style>
"""


def endpoint_cards():
    endpoints = [
        ("/api/inicio", "Início"),
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


def montar_legenda_calendario_html():
    return """
    <aside class="calendar-legend">
      <h3 class="legend-title">Legenda</h3>

      <div class="legend-item">
        <span class="legend-dot open"></span>
        <span>Loja aberta conforme horário de atendimento</span>
      </div>

      <div class="legend-item">
        <span class="legend-dot today"></span>
        <span>Data de hoje com loja aberta</span>
      </div>

      <div class="legend-item">
        <span class="legend-dot closed"></span>
        <span>Loja fechada por domingo ou fora do expediente cadastrado</span>
      </div>

      <div class="legend-item">
        <span class="legend-dot holiday"></span>
        <span>Loja fechada por feriado cadastrado</span>
      </div>

      <div class="legend-item">
        <span class="legend-dot holiday-open"></span>
        <span>Feriado em que a loja não fecha</span>
      </div>

      <div class="legend-note">
        <div class="legend-note-title">A loja não fecha em:</div>
        <ul class="legend-note-list">
          <li>Nossa Senhora da Luz dos Pinhais</li>
          <li>Nossa Senhora Aparecida</li>
          <li>Dia Nacional de Zumbi e da Consciência Negra</li>
        </ul>
      </div>
    </aside>
    """


def montar_calendario_html(calendario):
    if not calendario:
        return ""

    nomes_dias = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    hoje = datetime.now(TIMEZONE_BRASILIA).date()
    hoje_iso = hoje.strftime("%Y-%m-%d")

    calendario_html = f"""
    <section class="panel calendar-panel">
      <div class="panel-header">
        <div class="calendar-header-flex">
          <div>
            <h2 id="tituloCalendarioPeg" class="panel-title">Calendário de {calendario["mes_nome"]} de {calendario["ano"]}</h2>
            <p class="panel-subtitle">Dias de atendimento, feriados fechados e feriados com loja aberta</p>
          </div>

          <div class="calendar-actions">
            <button class="calendar-btn" type="button" onclick="mudarMesCalendarioPeg(-1)" aria-label="Mês anterior">‹</button>
            <button class="calendar-today-btn" type="button" onclick="voltarHojeCalendarioPeg()">Hoje</button>
            <input id="dataSelecionadaCalendarioPeg" class="calendar-date-input" type="date" value="{hoje_iso}" onchange="selecionarDataCalendarioPeg(this.value)">
            <button class="calendar-btn" type="button" onclick="mudarMesCalendarioPeg(1)" aria-label="Próximo mês">›</button>
          </div>
        </div>
      </div>

      <div class="calendar-content">
        <div class="calendar-grid">
    """

    for nome in nomes_dias:
        calendario_html += f'<div class="day-name">{nome}</div>'

    for semana in calendario["semanas"]:
        for dia in semana:
            if dia is None:
                calendario_html += '<div class="day empty"></div>'
            else:
                classes = ["day"]

                if dia["loja_abre"] is True:
                    classes.append("open")

                if dia["loja_abre"] is False:
                    classes.append("closed")

                if dia["nome_feriado"]:
                    classes.append("holiday")

                if dia["eh_feriado_com_loja_aberta"]:
                    classes.append("holiday-open")

                if dia["data"] == hoje_iso:
                    classes.append("today")

                classe = " ".join(classes)

                info = dia["funcionamento_previsto"]
                tag_classe = "open"
                tag_texto = "Aberto"

                if dia["eh_feriado_com_loja_aberta"]:
                    info = dia["nome_feriado_aberto"]
                    tag_classe = "holiday-open"
                    tag_texto = "Aberto"
                elif dia["nome_feriado"]:
                    info = dia["nome_feriado"]
                    tag_classe = "holiday"
                    tag_texto = "Feriado"
                elif dia["loja_abre"] is False:
                    tag_classe = "closed"
                    tag_texto = "Fechado"

                calendario_html += f"""
                <div class="{classe}" data-dia-calendario="{dia["data"]}">
                  <div class="day-number">{dia["dia"]}</div>
                  <div class="day-info">{dia["dia_semana"]}</div>
                  <div class="day-info">{info}</div>
                  <div class="day-tag {tag_classe}">{tag_texto}</div>
                </div>
                """

    calendario_html += f"""
        </div>
        {montar_legenda_calendario_html()}
      </div>
    </section>
    """

    return calendario_html


def render_visual(titulo, subtitulo, dados, status_texto=None, calendario=None, tempo_real=False):
    json_formatado = json.dumps(dados, ensure_ascii=False, indent=2)

    data_extenso = dados.get("data_extenso") or dados.get("hoje", {}).get("data_extenso") or "Consulta PEG"
    hora_atual = dados.get("hora_atual") or dados.get("hoje", {}).get("hora_atual") or "--:--:--"

    loja_abre = dados.get("loja_abre")
    atendimento_aberto = dados.get("atendimento_aberto")
    nome_feriado = dados.get("nome_feriado")
    eh_feriado_com_loja_aberta = dados.get("eh_feriado_com_loja_aberta")

    badge_class = ""
    status_titulo = "Consulta ativa"
    status_orb_class = "open"

    if eh_feriado_com_loja_aberta:
        badge_class = "holiday-open"
        status_titulo = "Feriado com loja aberta"
        status_orb_class = "open"
        status_final = status_texto or "Feriado com loja aberta"
    elif nome_feriado:
        badge_class = "holiday"
        status_titulo = "Fechado por feriado"
        status_orb_class = "holiday"
        status_final = f"Fechado: {nome_feriado}"
    elif loja_abre is False or atendimento_aberto is False:
        badge_class = "closed"
        status_titulo = "Atendimento fechado"
        status_orb_class = "closed"
        status_final = status_texto or dados.get("mensagem_atendimento") or dados.get("mensagem_resposta") or "Fechado"
    else:
        status_titulo = "Atendimento aberto"
        status_orb_class = "open"
        status_final = status_texto or dados.get("mensagem_atendimento") or dados.get("mensagem_resposta") or "Consulta disponível"

    calendario_html = montar_calendario_html(calendario)

    calendario_ano = calendario["ano"] if calendario else datetime.now(TIMEZONE_BRASILIA).year
    calendario_mes = calendario["mes"] if calendario else datetime.now(TIMEZONE_BRASILIA).month
    hoje_iso = datetime.now(TIMEZONE_BRASILIA).date().strftime("%Y-%m-%d")

    script_tempo_real = ""

    if tempo_real:
        script_tempo_real = f"""
<script>
let calendarioPegAno = {calendario_ano};
let calendarioPegMes = {calendario_mes};
let calendarioPegDataSelecionada = "{hoje_iso}";

async function atualizarHorarioPeg() {{
  try {{
    const resposta = await fetch("/api/horario", {{ cache: "no-store" }});
    const dados = await resposta.json();

    const dataEl = document.getElementById("dataAtualPeg");
    const horaEl = document.getElementById("horaAtualPeg");
    const statusEl = document.getElementById("statusAtualPeg");
    const statusTitleEl = document.getElementById("statusTituloPeg");
    const statusOrbEl = document.getElementById("statusOrbPeg");
    const miniDataEl = document.getElementById("statusMiniDataPeg");
    const miniDiaEl = document.getElementById("statusMiniDiaPeg");
    const miniHorarioEl = document.getElementById("statusMiniHorarioPeg");
    const miniSituacaoEl = document.getElementById("statusMiniSituacaoPeg");
    const jsonEl = document.getElementById("jsonAtualPeg");

    if (dataEl) {{
      dataEl.textContent = dados.data_extenso;
    }}

    if (horaEl) {{
      horaEl.textContent = dados.hora_atual;
      horaEl.classList.remove("tick");
      void horaEl.offsetWidth;
      horaEl.classList.add("tick");
    }}

    let statusTitulo = "Atendimento aberto";
    let statusOrbClass = "open";

    if (dados.eh_feriado_com_loja_aberta) {{
      statusTitulo = "Feriado com loja aberta";
      statusOrbClass = "open";
    }} else if (dados.nome_feriado) {{
      statusTitulo = "Fechado por feriado";
      statusOrbClass = "holiday";
    }} else if (!dados.atendimento_aberto) {{
      statusTitulo = "Atendimento fechado";
      statusOrbClass = "closed";
    }}

    if (statusTitleEl) {{
      statusTitleEl.textContent = statusTitulo;
    }}

    if (statusOrbEl) {{
      statusOrbEl.classList.remove("open", "closed", "holiday", "holiday-open");
      statusOrbEl.classList.add(statusOrbClass);
    }}

    if (statusEl) {{
      statusEl.textContent = dados.mensagem_atendimento;
      statusEl.classList.remove("closed", "holiday", "holiday-open");

      if (dados.eh_feriado_com_loja_aberta) {{
        statusEl.classList.add("holiday-open");
      }} else if (dados.nome_feriado) {{
        statusEl.classList.add("holiday");
      }} else if (!dados.atendimento_aberto) {{
        statusEl.classList.add("closed");
      }}
    }}

    if (miniDataEl) {{
      miniDataEl.textContent = dados.data_br;
    }}

    if (miniDiaEl) {{
      miniDiaEl.textContent = dados.dia_semana;
    }}

    if (miniHorarioEl) {{
      miniHorarioEl.textContent = dados.funcionamento_previsto_hoje || "Fechado";
    }}

    if (miniSituacaoEl) {{
      miniSituacaoEl.textContent = dados.status_atendimento;
    }}

    if (jsonEl) {{
      jsonEl.textContent = JSON.stringify(dados, null, 2);
    }}
  }} catch (erro) {{
    console.log("Erro ao atualizar horário PEG", erro);
  }}
}}

function obterDataHojePeg() {{
  const agora = new Date();
  const ano = agora.getFullYear();
  const mes = String(agora.getMonth() + 1).padStart(2, "0");
  const dia = String(agora.getDate()).padStart(2, "0");
  return `${{ano}}-${{mes}}-${{dia}}`;
}}

function montarLegendaCalendarioPeg() {{
  return `
    <aside class="calendar-legend">
      <h3 class="legend-title">Legenda</h3>

      <div class="legend-item">
        <span class="legend-dot open"></span>
        <span>Loja aberta conforme horário de atendimento</span>
      </div>

      <div class="legend-item">
        <span class="legend-dot today"></span>
        <span>Data de hoje com loja aberta</span>
      </div>

      <div class="legend-item">
        <span class="legend-dot closed"></span>
        <span>Loja fechada por domingo ou fora do expediente cadastrado</span>
      </div>

      <div class="legend-item">
        <span class="legend-dot holiday"></span>
        <span>Loja fechada por feriado cadastrado</span>
      </div>

      <div class="legend-item">
        <span class="legend-dot holiday-open"></span>
        <span>Feriado em que a loja não fecha</span>
      </div>

      <div class="legend-note">
        <div class="legend-note-title">A loja não fecha em:</div>
        <ul class="legend-note-list">
          <li>Nossa Senhora da Luz dos Pinhais</li>
          <li>Nossa Senhora Aparecida</li>
          <li>Dia Nacional de Zumbi e da Consciência Negra</li>
        </ul>
      </div>
    </aside>
  `;
}}

function montarHtmlCalendarioPeg(dados) {{
  const nomesDias = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];
  const hoje = dados.hoje.data_atual;

  let html = `
    <section class="panel calendar-panel">
      <div class="panel-header">
        <div class="calendar-header-flex">
          <div>
            <h2 id="tituloCalendarioPeg" class="panel-title">Calendário de ${{dados.mes_nome}} de ${{dados.ano}}</h2>
            <p class="panel-subtitle">Dias de atendimento, feriados fechados e feriados com loja aberta</p>
          </div>

          <div class="calendar-actions">
            <button class="calendar-btn" type="button" onclick="mudarMesCalendarioPeg(-1)" aria-label="Mês anterior">‹</button>
            <button class="calendar-today-btn" type="button" onclick="voltarHojeCalendarioPeg()">Hoje</button>
            <input id="dataSelecionadaCalendarioPeg" class="calendar-date-input" type="date" value="${{calendarioPegDataSelecionada}}" onchange="selecionarDataCalendarioPeg(this.value)">
            <button class="calendar-btn" type="button" onclick="mudarMesCalendarioPeg(1)" aria-label="Próximo mês">›</button>
          </div>
        </div>
      </div>

      <div class="calendar-content">
        <div class="calendar-grid">
  `;

  nomesDias.forEach(nome => {{
    html += `<div class="day-name">${{nome}}</div>`;
  }});

  dados.semanas.forEach(semana => {{
    semana.forEach(dia => {{
      if (!dia) {{
        html += `<div class="day empty"></div>`;
      }} else {{
        let classes = "day";

        if (dia.loja_abre === true) {{
          classes += " open";
        }}

        if (dia.loja_abre === false) {{
          classes += " closed";
        }}

        if (dia.nome_feriado) {{
          classes += " holiday";
        }}

        if (dia.eh_feriado_com_loja_aberta) {{
          classes += " holiday-open";
        }}

        if (dia.data === hoje) {{
          classes += " today";
        }}

        if (dia.data === calendarioPegDataSelecionada) {{
          classes += " selected-date";
        }}

        let info = dia.funcionamento_previsto;
        let tagClasse = "open";
        let tagTexto = "Aberto";

        if (dia.eh_feriado_com_loja_aberta) {{
          info = dia.nome_feriado_aberto;
          tagClasse = "holiday-open";
          tagTexto = "Aberto";
        }} else if (dia.nome_feriado) {{
          info = dia.nome_feriado;
          tagClasse = "holiday";
          tagTexto = "Feriado";
        }} else if (dia.loja_abre === false) {{
          tagClasse = "closed";
          tagTexto = "Fechado";
        }}

        html += `
          <div class="${{classes}}" data-dia-calendario="${{dia.data}}">
            <div class="day-number">${{dia.dia}}</div>
            <div class="day-info">${{dia.dia_semana}}</div>
            <div class="day-info">${{info}}</div>
            <div class="day-tag ${{tagClasse}}">${{tagTexto}}</div>
          </div>
        `;
      }}
    }});
  }});

  html += `
        </div>
        ${{montarLegendaCalendarioPeg()}}
      </div>
    </section>
  `;

  return html;
}}

async function carregarCalendarioPeg(ano, mes) {{
  try {{
    const resposta = await fetch(`/api/calendario/${{ano}}/${{mes}}`, {{ cache: "no-store" }});
    const dados = await resposta.json();

    const painel = document.getElementById("calendarioAtualPeg");

    if (!painel) {{
      return;
    }}

    calendarioPegAno = dados.ano;
    calendarioPegMes = dados.mes;

    painel.innerHTML = montarHtmlCalendarioPeg(dados);

  }} catch (erro) {{
    console.log("Erro ao carregar calendário PEG", erro);
  }}
}}

function mudarMesCalendarioPeg(direcao) {{
  calendarioPegMes += direcao;

  if (calendarioPegMes < 1) {{
    calendarioPegMes = 12;
    calendarioPegAno -= 1;
  }}

  if (calendarioPegMes > 12) {{
    calendarioPegMes = 1;
    calendarioPegAno += 1;
  }}

  carregarCalendarioPeg(calendarioPegAno, calendarioPegMes);
}}

function voltarHojeCalendarioPeg() {{
  const hoje = obterDataHojePeg();
  calendarioPegDataSelecionada = hoje;

  const partes = hoje.split("-");
  calendarioPegAno = Number(partes[0]);
  calendarioPegMes = Number(partes[1]);

  carregarCalendarioPeg(calendarioPegAno, calendarioPegMes);
}}

function selecionarDataCalendarioPeg(valor) {{
  if (!valor) {{
    return;
  }}

  calendarioPegDataSelecionada = valor;

  const partes = valor.split("-");

  if (partes.length !== 3) {{
    return;
  }}

  calendarioPegAno = Number(partes[0]);
  calendarioPegMes = Number(partes[1]);

  carregarCalendarioPeg(calendarioPegAno, calendarioPegMes);
}}

async function atualizarCalendarioPeg() {{
  await carregarCalendarioPeg(calendarioPegAno, calendarioPegMes);
}}

atualizarHorarioPeg();
carregarCalendarioPeg(calendarioPegAno, calendarioPegMes);

setInterval(atualizarHorarioPeg, 1000);
setInterval(atualizarCalendarioPeg, 60000);
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
      <div class="hero-content">

        <div class="topbar">
          <div class="brand">
            <div class="brand-mark">
              <img class="brand-logo" src="{LOGO_PEG_URL}" alt="PEG do Brasil">
            </div>
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
            <div id="dataAtualPeg" class="date">{data_extenso.capitalize()}</div>
            <div id="horaAtualPeg" class="clock">{hora_atual}</div>
          </div>

          <div class="status-card">
            <div class="status-content">
              <div class="status-topline">
                <div id="statusOrbPeg" class="status-orb {status_orb_class}">
                  <img src="{LOGO_PEG_URL}" alt="PEG do Brasil">
                </div>

                <div class="status-text-block">
                  <div class="status-overline">Status operacional</div>
                  <h2 id="statusTituloPeg" class="status-title">{status_titulo}</h2>
                </div>
              </div>

              <div id="statusAtualPeg" class="status-badge {badge_class}">
                {status_final}
              </div>

              <div class="status-mini-grid">
                <div class="status-mini-card">
                  <span>Data</span>
                  <strong id="statusMiniDataPeg">{dados.get("data_br", "-")}</strong>
                </div>

                <div class="status-mini-card">
                  <span>Dia</span>
                  <strong id="statusMiniDiaPeg">{dados.get("dia_semana", "-")}</strong>
                </div>

                <div class="status-mini-card">
                  <span>Funcionamento</span>
                  <strong id="statusMiniHorarioPeg">{dados.get("funcionamento_previsto_hoje", dados.get("funcionamento_previsto", "Fechado"))}</strong>
                </div>

                <div class="status-mini-card">
                  <span>Situação</span>
                  <strong id="statusMiniSituacaoPeg">{dados.get("status_atendimento", "consulta")}</strong>
                </div>
              </div>

              <div class="hours-list">
                <div class="hours-item">
                  <span>Segunda a sexta</span>
                  <strong>09:00 às 18:00</strong>
                </div>

                <div class="hours-item">
                  <span>Sábado</span>
                  <strong>09:00 às 13:00</strong>
                </div>

                <div class="hours-item">
                  <span>Domingo</span>
                  <strong>Fechado</strong>
                </div>

                <div class="hours-item">
                  <span>Feriados fechados</span>
                  <strong>Fechado</strong>
                </div>

                <div class="hours-item">
                  <span>Feriados com loja aberta</span>
                  <strong>Funcionamento normal</strong>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </section>

    <section class="side-grid">
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

      <div id="calendarioAtualPeg">
        {calendario_html}
      </div>
    </section>

    <section class="panel json-panel">
      <div class="panel-header">
        <div>
          <h2 class="panel-title">Resposta JSON</h2>
          <p class="panel-subtitle">Dados retornados pela API</p>
        </div>
      </div>
      <pre id="jsonAtualPeg" class="json">{json_formatado}</pre>
    </section>

    <div class="footer">
      PEG do Brasil - Sistema de data, hora, calendário e feriados para atendimento automatizado
    </div>

  </div>

  {script_tempo_real}
</body>
</html>
"""

    return Response(html, mimetype="text/html")


def responder(dados, titulo, subtitulo, status_texto=None, calendario=None, tempo_real=False):
    if quer_visual():
        return render_visual(titulo, subtitulo, dados, status_texto, calendario, tempo_real)
    return jsonify(dados)


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


@app.route("/api/inicio")
def api_inicio():
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


@app.route("/api/horario")
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
        "Consulta do próximo feriado ou data cadastrada",
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
        "Datas fechadas e datas com loja aberta cadastradas para a PEG",
        f"{dados['total_feriados']} datas cadastradas"
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
        calendario_mes,
        tempo_real=True
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
