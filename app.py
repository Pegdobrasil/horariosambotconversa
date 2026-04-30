from flask import Flask, jsonify, Response
from datetime import datetime, date
from zoneinfo import ZoneInfo
import calendar
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


def verificar_atendimento(dt):
    dia_semana_numero = dt.weekday()
    minutos_atuais = dt.hour * 60 + dt.minute

    inicio_atendimento = 9 * 60
    fim_segunda_sexta = 18 * 60
    fim_sabado = 13 * 60

    atendimento_aberto = False

    if dia_semana_numero in [0, 1, 2, 3, 4]:
        if inicio_atendimento <= minutos_atuais < fim_segunda_sexta:
            atendimento_aberto = True

    elif dia_semana_numero == 5:
        if inicio_atendimento <= minutos_atuais < fim_sabado:
            atendimento_aberto = True

    if atendimento_aberto:
        return {
            "atendimento_aberto": True,
            "status_atendimento": "aberto",
            "mensagem_atendimento": "Estamos em horário de atendimento."
        }

    return {
        "atendimento_aberto": False,
        "status_atendimento": "fechado",
        "mensagem_atendimento": "Estamos fora do horário de atendimento."
    }


def obter_dados_horario():
    agora = datetime.now(TIMEZONE_BRASILIA)

    dia_semana_numero = agora.weekday()
    dia_semana = DIAS_SEMANA[dia_semana_numero]

    data_atual = agora.strftime("%Y-%m-%d")
    hora_atual = agora.strftime("%H:%M:%S")

    data_extenso = f"{dia_semana}, {agora.day:02d} de {MESES[agora.month]} de {agora.year}"

    atendimento = verificar_atendimento(agora)

    dados = {
        "empresa": "PEG do Brasil",
        "timezone": "America/Sao_Paulo",
        "data_atual": data_atual,
        "data_extenso": data_extenso,
        "dia_semana": dia_semana,
        "dia_semana_numero": dia_semana_numero,
        "hora_atual": hora_atual,
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
        "horario_funcionamento": {
            "segunda_a_sexta": "09:00 às 18:00",
            "sabado": "09:00 às 13:00",
            "domingo": "Fechado"
        }
    }

    return dados


def gerar_dados_data(ano, mes, dia):
    try:
        data_consulta = date(ano, mes, dia)

        dia_semana_numero = data_consulta.weekday()
        dia_semana = DIAS_SEMANA[dia_semana_numero]

        data_extenso = f"{dia_semana}, {dia:02d} de {MESES[mes]} de {ano}"

        eh_final_de_semana = dia_semana_numero in [5, 6]
        eh_domingo = dia_semana_numero == 6
        eh_sabado = dia_semana_numero == 5
        eh_dia_util = dia_semana_numero in [0, 1, 2, 3, 4]

        if eh_dia_util:
            funcionamento = "09:00 às 18:00"
            loja_abre = True
        elif eh_sabado:
            funcionamento = "09:00 às 13:00"
            loja_abre = True
        else:
            funcionamento = "Fechado"
            loja_abre = False

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
            "loja_abre": loja_abre,
            "funcionamento_previsto": funcionamento
        }

    except ValueError:
        return None


def gerar_calendario_mes(ano, mes):
    try:
        primeiro_dia, total_dias = calendar.monthrange(ano, mes)

        dias = []

        for dia in range(1, total_dias + 1):
            dados_dia = gerar_dados_data(ano, mes, dia)
            dias.append(dados_dia)

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
        calendario_mes = gerar_calendario_mes(ano, mes)
        meses.append(calendario_mes)

    return {
        "ano": ano,
        "total_meses": 12,
        "meses": meses
    }


@app.route("/")
def index():
    dados = obter_dados_horario()

    html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <title>Horário e Calendário - PEG do Brasil</title>

  <style>
    * {{
      box-sizing: border-box;
    }}

    :root {{
      --peg-blue: #005cff;
      --peg-cyan: #00c8ff;
      --peg-dark: #020617;
      --peg-card: rgba(15, 23, 42, 0.78);
      --peg-border: rgba(0, 200, 255, 0.22);
      --peg-text: #e5f4ff;
      --peg-muted: #94a3b8;
      --peg-green: #22c55e;
      --peg-red: #ef4444;
    }}

    body {{
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
    }}

    body::before {{
      content: "";
      position: fixed;
      inset: 0;
      background:
        linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px);
      background-size: 42px 42px;
      mask-image: linear-gradient(to bottom, rgba(0,0,0,0.8), transparent 85%);
      pointer-events: none;
    }}

    .page {{
      width: 100%;
      max-width: 1180px;
      margin: 0 auto;
      position: relative;
      z-index: 2;
    }}

    .hero {{
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
    }}

    .hero::before {{
      content: "";
      position: absolute;
      inset: -2px;
      background: linear-gradient(120deg, transparent, rgba(0, 200, 255, 0.34), transparent);
      transform: translateX(-100%);
      animation: neonSweep 7s infinite;
      pointer-events: none;
    }}

    .hero::after {{
      content: "";
      position: absolute;
      inset: 0;
      background-image: url("https://github.com/Pegdobrasil/peg-imagens-site/blob/main/logo%20branca.png?raw=true");
      background-repeat: no-repeat;
      background-position: right 36px top 28px;
      background-size: 220px auto;
      opacity: 0.06;
      pointer-events: none;
    }}

    @keyframes neonSweep {{
      0% {{
        transform: translateX(-100%);
        opacity: 0;
      }}
      28% {{
        opacity: 1;
      }}
      55% {{
        transform: translateX(100%);
        opacity: 0;
      }}
      100% {{
        transform: translateX(100%);
        opacity: 0;
      }}
    }}

    .hero-content {{
      position: relative;
      z-index: 2;
    }}

    .topbar {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
      margin-bottom: 28px;
    }}

    .brand {{
      display: flex;
      align-items: center;
      gap: 14px;
    }}

    .brand-mark {{
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
    }}

    .brand-title {{
      margin: 0;
      font-size: 18px;
      line-height: 1.1;
      color: white;
      font-weight: 900;
    }}

    .brand-subtitle {{
      margin: 4px 0 0;
      color: var(--peg-muted);
      font-size: 13px;
    }}

    .live-pill {{
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
    }}

    .live-dot {{
      width: 9px;
      height: 9px;
      border-radius: 50%;
      background: var(--peg-green);
      box-shadow: 0 0 16px rgba(34, 197, 94, 0.85);
      animation: pulse 1.4s infinite;
    }}

    @keyframes pulse {{
      0%, 100% {{
        transform: scale(1);
        opacity: 1;
      }}
      50% {{
        transform: scale(1.35);
        opacity: 0.65;
      }}
    }}

    .main-grid {{
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 22px;
      align-items: stretch;
    }}

    .clock-card {{
      border-radius: 24px;
      padding: 28px;
      background:
        radial-gradient(circle at top left, rgba(0, 200, 255, 0.18), transparent 36%),
        rgba(2, 6, 23, 0.58);
      border: 1px solid rgba(148, 163, 184, 0.16);
      box-shadow: inset 0 0 35px rgba(0, 200, 255, 0.04);
    }}

    .label {{
      color: var(--peg-cyan);
      text-transform: uppercase;
      letter-spacing: 1.6px;
      font-weight: 900;
      font-size: 12px;
      margin-bottom: 12px;
    }}

    .date {{
      font-size: clamp(22px, 3vw, 34px);
      font-weight: 900;
      color: #ffffff;
      margin-bottom: 24px;
      text-transform: capitalize;
    }}

    .clock {{
      font-size: clamp(64px, 11vw, 142px);
      line-height: 0.9;
      font-weight: 900;
      letter-spacing: -4px;
      color: white;
      text-shadow:
        0 0 22px rgba(0, 200, 255, 0.22),
        0 0 52px rgba(0, 92, 255, 0.18);
    }}

    .timezone {{
      margin-top: 18px;
      color: var(--peg-muted);
      font-size: 14px;
    }}

    .side-card {{
      display: flex;
      flex-direction: column;
      gap: 14px;
    }}

    .status-card,
    .mini-card {{
      border-radius: 22px;
      padding: 20px;
      background: var(--peg-card);
      border: 1px solid rgba(148, 163, 184, 0.14);
      box-shadow: 0 12px 36px rgba(0, 0, 0, 0.20);
    }}

    .status-title {{
      font-size: 14px;
      color: var(--peg-muted);
      font-weight: 800;
      margin-bottom: 10px;
    }}

    .status-badge {{
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
    }}

    .status-badge.closed {{
      border-color: rgba(239, 68, 68, 0.35);
      background: rgba(239, 68, 68, 0.10);
      color: #fee2e2;
    }}

    .status-dot {{
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--peg-green);
      box-shadow: 0 0 18px rgba(34, 197, 94, 0.9);
    }}

    .status-dot.closed {{
      background: var(--peg-red);
      box-shadow: 0 0 18px rgba(239, 68, 68, 0.9);
    }}

    .hours-list {{
      display: grid;
      gap: 10px;
      margin-top: 12px;
    }}

    .hours-item {{
      display: flex;
      justify-content: space-between;
      gap: 10px;
      color: #dbeafe;
      font-size: 14px;
      padding-bottom: 10px;
      border-bottom: 1px solid rgba(148, 163, 184, 0.12);
    }}

    .hours-item:last-child {{
      border-bottom: none;
      padding-bottom: 0;
    }}

    .hours-item span:first-child {{
      color: var(--peg-muted);
    }}

    .section-grid {{
      display: grid;
      grid-template-columns: 0.95fr 1.05fr;
      gap: 22px;
      margin-top: 22px;
    }}

    .panel {{
      border-radius: 24px;
      background: rgba(15, 23, 42, 0.74);
      border: 1px solid rgba(0, 200, 255, 0.14);
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.26);
      overflow: hidden;
    }}

    .panel-header {{
      padding: 18px 20px;
      border-bottom: 1px solid rgba(148, 163, 184, 0.12);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
    }}

    .panel-title {{
      margin: 0;
      color: white;
      font-size: 18px;
      font-weight: 900;
    }}

    .panel-subtitle {{
      margin: 4px 0 0;
      color: var(--peg-muted);
      font-size: 13px;
    }}

    .panel-body {{
      padding: 18px 20px 20px;
    }}

    .endpoint {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      color: #e0f2fe;
      text-decoration: none;
      background:
        linear-gradient(135deg, rgba(0, 92, 255, 0.16), rgba(0, 200, 255, 0.06));
      border: 1px solid rgba(0, 200, 255, 0.16);
      border-radius: 15px;
      padding: 13px 14px;
      margin-bottom: 10px;
      font-size: 14px;
      font-weight: 800;
      word-break: break-word;
      transition: 0.25s ease;
    }}

    .endpoint:hover {{
      transform: translateY(-2px);
      border-color: rgba(0, 200, 255, 0.42);
      box-shadow: 0 0 24px rgba(0, 200, 255, 0.13);
    }}

    .endpoint small {{
      color: var(--peg-muted);
      font-weight: 700;
      white-space: nowrap;
    }}

    .calendar {{
      margin: 0;
    }}

    .calendar-top {{
      background:
        linear-gradient(135deg, rgba(0, 92, 255, 0.96), rgba(0, 200, 255, 0.76));
      padding: 18px 20px;
      color: white;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }}

    .calendar-month {{
      font-size: 20px;
      font-weight: 900;
      text-transform: capitalize;
    }}

    .calendar-note {{
      font-size: 12px;
      opacity: 0.85;
      font-weight: 800;
    }}

    .calendar-grid {{
      display: grid;
      grid-template-columns: repeat(7, 1fr);
      background: rgba(2, 6, 23, 0.50);
    }}

    .day-name {{
      padding: 12px 6px;
      text-align: center;
      color: #bfdbfe;
      font-size: 12px;
      font-weight: 900;
      border-bottom: 1px solid rgba(148, 163, 184, 0.16);
      background: rgba(2, 6, 23, 0.40);
    }}

    .day {{
      min-height: 82px;
      padding: 9px;
      border-right: 1px solid rgba(148, 163, 184, 0.10);
      border-bottom: 1px solid rgba(148, 163, 184, 0.10);
      background: rgba(15, 23, 42, 0.48);
      position: relative;
    }}

    .day:nth-child(7n) {{
      border-right: none;
    }}

    .day.empty {{
      background: rgba(15, 23, 42, 0.20);
    }}

    .day.today {{
      background:
        radial-gradient(circle at top right, rgba(0, 200, 255, 0.22), transparent 55%),
        rgba(0, 92, 255, 0.18);
      outline: 2px solid rgba(0, 200, 255, 0.70);
      outline-offset: -2px;
      box-shadow: inset 0 0 24px rgba(0, 200, 255, 0.14);
    }}

    .day-number {{
      font-size: 17px;
      color: white;
      font-weight: 900;
    }}

    .day-info {{
      margin-top: 7px;
      color: var(--peg-muted);
      font-size: 11px;
      line-height: 1.25;
    }}

    .day.today .day-info {{
      color: #dff7ff;
    }}

    .json-box {{
      margin-top: 22px;
      border-radius: 24px;
      background: rgba(2, 6, 23, 0.86);
      border: 1px solid rgba(0, 200, 255, 0.14);
      overflow: hidden;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.26);
    }}

    .json-header {{
      padding: 16px 20px;
      color: white;
      font-weight: 900;
      border-bottom: 1px solid rgba(148, 163, 184, 0.12);
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
    }}

    .json-header span {{
      color: var(--peg-muted);
      font-size: 12px;
      font-weight: 800;
    }}

    .json {{
      margin: 0;
      padding: 18px 20px 22px;
      color: #dbeafe;
      text-align: left;
      font-size: 13px;
      line-height: 1.7;
      white-space: pre-wrap;
      word-break: break-word;
      max-height: 360px;
      overflow: auto;
    }}

    .footer {{
      text-align: center;
      color: var(--peg-muted);
      margin-top: 22px;
      font-size: 13px;
    }}

    @media (max-width: 920px) {{
      .main-grid,
      .section-grid {{
        grid-template-columns: 1fr;
      }}

      .hero::after {{
        background-position: center top 34px;
        background-size: 180px auto;
      }}
    }}

    @media (max-width: 620px) {{
      body {{
        padding: 14px;
      }}

      .hero {{
        padding: 18px;
        border-radius: 22px;
      }}

      .topbar {{
        flex-direction: column;
        align-items: flex-start;
      }}

      .brand-mark {{
        width: 50px;
        height: 50px;
        border-radius: 16px;
      }}

      .clock-card {{
        padding: 20px;
        border-radius: 20px;
      }}

      .clock {{
        letter-spacing: -2px;
      }}

      .section-grid {{
        gap: 16px;
      }}

      .panel-header {{
        flex-direction: column;
        align-items: flex-start;
      }}

      .day {{
        min-height: 58px;
        padding: 5px;
      }}

      .day-info {{
        display: none;
      }}

      .day-name {{
        font-size: 10px;
        padding: 9px 3px;
      }}

      .day-number {{
        font-size: 14px;
      }}
    }}
  </style>
</head>

<body>
  <div class="page">

    <section class="hero">
      <div class="hero-content">

        <div class="topbar">
          <div class="brand">
            <div class="brand-mark">PEG</div>
            <div>
              <h1 class="brand-title">Horário e Calendário PEG</h1>
              <p class="brand-subtitle">Base de consulta para a Sam - BotConversa</p>
            </div>
          </div>

          <div class="live-pill">
            <span class="live-dot"></span>
            Atualização em tempo real
          </div>
        </div>

        <div class="main-grid">
          <div class="clock-card">
            <div class="label">Horário de Brasília</div>

            <div id="dataAtual" class="date">
              {dados["data_extenso"].capitalize()}
            </div>

            <div id="horaAtual" class="clock">
              {dados["hora_atual"]}
            </div>

            <div class="timezone">
              Fuso usado pela API: America/Sao_Paulo
            </div>
          </div>

          <aside class="side-card">
            <div class="status-card">
              <div class="status-title">Status de atendimento</div>

              <div id="statusBadge" class="status-badge">
                <span id="statusDot" class="status-dot"></span>
                <span id="statusAtendimento">{dados["mensagem_atendimento"]}</span>
              </div>
            </div>

            <div class="mini-card">
              <div class="status-title">Horário de funcionamento</div>

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
              </div>
            </div>
          </aside>
        </div>

      </div>
    </section>

    <section class="section-grid">
      <div class="panel">
        <div class="panel-header">
          <div>
            <h2 class="panel-title">Endpoints da integração</h2>
            <p class="panel-subtitle">Links para a Sam consultar pelo BotConversa</p>
          </div>
        </div>

        <div class="panel-body">
          <a class="endpoint" href="/api/horario" target="_blank">
            <span>/api/horario</span>
            <small>hora atual</small>
          </a>

          <a class="endpoint" href="/api/calendario" target="_blank">
            <span>/api/calendario</span>
            <small>mês atual</small>
          </a>

          <a class="endpoint" href="/api/calendario/{dados["ano_atual"]}" target="_blank">
            <span>/api/calendario/{dados["ano_atual"]}</span>
            <small>ano completo</small>
          </a>

          <a class="endpoint" href="/api/calendario/{dados["ano_atual"]}/{dados["mes_atual"]:02d}" target="_blank">
            <span>/api/calendario/{dados["ano_atual"]}/{dados["mes_atual"]:02d}</span>
            <small>mês específico</small>
          </a>

          <a class="endpoint" href="/api/data/{dados["data_atual"]}" target="_blank">
            <span>/api/data/{dados["data_atual"]}</span>
            <small>data específica</small>
          </a>
        </div>
      </div>

      <div id="calendarioVisual" class="panel calendar"></div>
    </section>

    <section class="json-box">
      <div class="json-header">
        Resposta atual da API
        <span>JSON usado pela integração</span>
      </div>

      <pre id="jsonIntegracao" class="json"></pre>
    </section>

    <div class="footer">
      PEG do Brasil - Sistema de data, hora e calendário para atendimento automatizado
    </div>

  </div>

  <script>
    async function atualizarHorario() {{
      try {{
        const resposta = await fetch("/api/horario", {{
          cache: "no-store"
        }});

        const dados = await resposta.json();

        document.getElementById("dataAtual").textContent =
          dados.data_extenso.charAt(0).toUpperCase() + dados.data_extenso.slice(1);

        document.getElementById("horaAtual").textContent = dados.hora_atual;

        document.getElementById("statusAtendimento").textContent =
          dados.mensagem_atendimento;

        const statusBadge = document.getElementById("statusBadge");
        const statusDot = document.getElementById("statusDot");

        if (dados.atendimento_aberto) {{
          statusBadge.classList.remove("closed");
          statusDot.classList.remove("closed");
        }} else {{
          statusBadge.classList.add("closed");
          statusDot.classList.add("closed");
        }}

        document.getElementById("jsonIntegracao").textContent =
          JSON.stringify(dados, null, 2);

        document.body.setAttribute("data-data-atual", dados.data_atual);
        document.body.setAttribute("data-hora-atual", dados.hora_atual);
        document.body.setAttribute("data-dia-semana", dados.dia_semana);
        document.body.setAttribute("data-atendimento-aberto", dados.atendimento_aberto);

      }} catch (erro) {{
        document.getElementById("jsonIntegracao").textContent =
          "Erro ao carregar dados de horário.";
      }}
    }}

    async function carregarCalendarioVisual() {{
      try {{
        const resposta = await fetch("/api/calendario", {{
          cache: "no-store"
        }});

        const calendario = await resposta.json();

        const nomesDias = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];

        let html = "";

        html += `
          <div class="calendar-top">
            <div>
              <div class="calendar-month">${{calendario.mes_nome}} de ${{calendario.ano}}</div>
              <div class="calendar-note">Calendário operacional da PEG</div>
            </div>
            <div class="calendar-note">${{calendario.total_dias}} dias</div>
          </div>
        `;

        html += `<div class="calendar-grid">`;

        nomesDias.forEach(nome => {{
          html += `<div class="day-name">${{nome}}</div>`;
        }});

        calendario.semanas.forEach(semana => {{
          semana.forEach(dia => {{
            if (!dia) {{
              html += `<div class="day empty"></div>`;
            }} else {{
              const hoje = dia.data === calendario.hoje.data_atual ? "today" : "";

              html += `
                <div class="day ${{hoje}}">
                  <div class="day-number">${{dia.dia}}</div>
                  <div class="day-info">${{dia.dia_semana}}</div>
                  <div class="day-info">${{dia.funcionamento_previsto}}</div>
                </div>
              `;
            }}
          }});
        }});

        html += `</div>`;

        document.getElementById("calendarioVisual").innerHTML = html;

      }} catch (erro) {{
        document.getElementById("calendarioVisual").innerHTML =
          "<div class='calendar-top'><div class='calendar-month'>Erro ao carregar calendário</div></div>";
      }}
    }}

    atualizarHorario();
    carregarCalendarioVisual();

    setInterval(atualizarHorario, 1000);
    setInterval(carregarCalendarioVisual, 60000);
  </script>

</body>
</html>
"""

    return Response(html, mimetype="text/html")


@app.route("/api/horario")
def api_horario():
    dados = obter_dados_horario()
    return jsonify(dados)


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

    return jsonify(calendario_mes)


@app.route("/api/calendario/<int:ano>")
def api_calendario_ano(ano):
    if ano < 1 or ano > 9999:
        return jsonify({
            "erro": True,
            "mensagem": "Ano inválido."
        }), 400

    calendario_ano = gerar_calendario_ano(ano)
    calendario_ano["hoje"] = obter_dados_horario()
    calendario_ano["tipo_consulta"] = "ano_completo"

    return jsonify(calendario_ano)


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

    return jsonify(calendario_mes)


@app.route("/api/data/<string:data_texto>")
def api_data_especifica(data_texto):
    try:
        partes = data_texto.split("-")

        if len(partes) != 3:
            return jsonify({
                "erro": True,
                "mensagem": "Formato inválido. Use o formato AAAA-MM-DD."
            }), 400

        ano = int(partes[0])
        mes = int(partes[1])
        dia = int(partes[2])

        dados_data = gerar_dados_data(ano, mes, dia)

        if dados_data is None:
            return jsonify({
                "erro": True,
                "mensagem": "Data inválida."
            }), 400

        dados_data["hoje"] = obter_dados_horario()
        dados_data["tipo_consulta"] = "data_especifica"

        return jsonify(dados_data)

    except Exception:
        return jsonify({
            "erro": True,
            "mensagem": "Não foi possível consultar a data. Use o formato AAAA-MM-DD."
        }), 400


@app.route("/health")
def health():
    return jsonify({
        "status": "online",
        "servico": "horario-calendario-peg"
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
