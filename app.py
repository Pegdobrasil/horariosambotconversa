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

    body {{
      margin: 0;
      padding: 30px 15px;
      font-family: Arial, Helvetica, sans-serif;
      background: #f4f7fb;
      color: #111827;
    }}

    .peg-wrapper {{
      max-width: 1050px;
      margin: 0 auto;
      background: #ffffff;
      border-radius: 18px;
      padding: 30px;
      box-shadow: 0 10px 35px rgba(0, 0, 0, 0.10);
      border: 1px solid #dbe4f0;
      text-align: center;
      position: relative;
      overflow: hidden;
    }}

    .peg-wrapper::before {{
      content: "";
      position: absolute;
      inset: 0;
      background-image: url("https://github.com/Pegdobrasil/peg-imagens-site/blob/main/logo%20branca.png?raw=true");
      background-repeat: no-repeat;
      background-position: center;
      background-size: 420px auto;
      opacity: 0.04;
      pointer-events: none;
    }}

    .peg-content {{
      position: relative;
      z-index: 2;
    }}

    .peg-title {{
      font-size: 36px;
      font-weight: 900;
      margin: 0;
      color: #002b5c;
    }}

    .peg-subtitle {{
      margin: 8px 0 22px;
      color: #475569;
      font-size: 15px;
    }}

    .peg-divider {{
      width: 100%;
      height: 1px;
      background: #d7dee9;
      margin: 20px 0;
    }}

    .peg-date {{
      font-size: 27px;
      font-weight: 800;
      color: #111827;
      margin-bottom: 20px;
    }}

    .peg-clock-box {{
      background: #e8eef7;
      border: 1px solid #cbd5e1;
      border-radius: 16px;
      padding: 38px 15px;
      margin-bottom: 20px;
    }}

    .peg-clock {{
      font-size: clamp(60px, 12vw, 145px);
      line-height: 1;
      font-weight: 900;
      letter-spacing: 2px;
      color: #101827;
    }}

    .peg-status {{
      display: inline-block;
      margin-top: 5px;
      padding: 10px 18px;
      border-radius: 999px;
      font-size: 15px;
      font-weight: 800;
      background: #eaf4ff;
      color: #005c99;
      border: 1px solid #b7dfff;
    }}

    .peg-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-top: 30px;
      text-align: left;
    }}

    .peg-card {{
      background: #f8fbff;
      border: 1px solid #dbeafe;
      border-radius: 14px;
      padding: 18px;
    }}

    .peg-card-title {{
      font-size: 17px;
      font-weight: 900;
      color: #002b5c;
      margin-bottom: 12px;
    }}

    .peg-link {{
      display: block;
      background: #eff6ff;
      color: #005c99;
      padding: 11px 12px;
      border-radius: 10px;
      font-size: 14px;
      text-decoration: none;
      border: 1px solid #bfdbfe;
      margin-bottom: 8px;
      word-break: break-word;
      font-weight: 700;
    }}

    .peg-link:hover {{
      background: #dbeafe;
    }}

    .peg-json {{
      margin-top: 30px;
      background: #0f172a;
      color: #e5e7eb;
      padding: 16px;
      border-radius: 12px;
      text-align: left;
      font-size: 14px;
      line-height: 1.6;
      white-space: pre-wrap;
      word-break: break-word;
    }}

    .peg-calendar {{
      margin-top: 25px;
      background: #ffffff;
      border: 1px solid #dbe4f0;
      border-radius: 14px;
      overflow: hidden;
    }}

    .peg-calendar-header {{
      background: #002b5c;
      color: #ffffff;
      padding: 14px;
      font-weight: 900;
      font-size: 18px;
      text-transform: capitalize;
    }}

    .peg-calendar-grid {{
      display: grid;
      grid-template-columns: repeat(7, 1fr);
    }}

    .peg-calendar-day-name {{
      background: #e8eef7;
      padding: 10px 5px;
      font-weight: 800;
      color: #002b5c;
      border-bottom: 1px solid #dbe4f0;
      font-size: 13px;
    }}

    .peg-calendar-day {{
      min-height: 72px;
      border-right: 1px solid #e5e7eb;
      border-bottom: 1px solid #e5e7eb;
      padding: 8px;
      font-size: 13px;
      text-align: left;
      background: #ffffff;
    }}

    .peg-calendar-day:nth-child(7n) {{
      border-right: none;
    }}

    .peg-calendar-day.empty {{
      background: #f8fafc;
    }}

    .peg-calendar-day.today {{
      background: #eaf4ff;
      border: 2px solid #005c99;
      font-weight: 900;
    }}

    .peg-calendar-number {{
      font-weight: 900;
      font-size: 16px;
      color: #111827;
    }}

    .peg-calendar-info {{
      margin-top: 6px;
      color: #64748b;
      font-size: 12px;
    }}

    .peg-footer {{
      margin-top: 20px;
      font-size: 13px;
      color: #64748b;
    }}

    @media (max-width: 800px) {{
      .peg-grid {{
        grid-template-columns: 1fr;
      }}
    }}

    @media (max-width: 600px) {{
      body {{
        padding: 15px;
      }}

      .peg-wrapper {{
        padding: 22px 16px;
      }}

      .peg-title {{
        font-size: 27px;
      }}

      .peg-date {{
        font-size: 20px;
      }}

      .peg-clock-box {{
        padding: 28px 10px;
      }}

      .peg-calendar-day {{
        min-height: 58px;
        padding: 5px;
        font-size: 11px;
      }}

      .peg-calendar-day-name {{
        font-size: 11px;
        padding: 8px 3px;
      }}

      .peg-calendar-number {{
        font-size: 14px;
      }}

      .peg-calendar-info {{
        display: none;
      }}
    }}
  </style>
</head>

<body>

  <main class="peg-wrapper">
    <div class="peg-content">

      <h1 class="peg-title">Horário e Calendário de Brasília</h1>

      <p class="peg-subtitle">
        Consulta de data, hora e calendário para integração da Sam - PEG do Brasil
      </p>

      <div class="peg-divider"></div>

      <div id="dataAtual" class="peg-date">
        {dados["data_extenso"].capitalize()}
      </div>

      <div class="peg-clock-box">
        <div id="horaAtual" class="peg-clock">
          {dados["hora_atual"]}
        </div>
      </div>

      <div id="statusAtendimento" class="peg-status">
        {dados["mensagem_atendimento"]}
      </div>

      <div class="peg-grid">
        <div class="peg-card">
          <div class="peg-card-title">Endpoints para o BotConversa</div>

          <a class="peg-link" href="/api/horario" target="_blank">/api/horario</a>
          <a class="peg-link" href="/api/calendario" target="_blank">/api/calendario</a>
          <a class="peg-link" href="/api/calendario/{dados["ano_atual"]}" target="_blank">/api/calendario/{dados["ano_atual"]}</a>
          <a class="peg-link" href="/api/calendario/{dados["ano_atual"]}/{dados["mes_atual"]:02d}" target="_blank">/api/calendario/{dados["ano_atual"]}/{dados["mes_atual"]:02d}</a>
          <a class="peg-link" href="/api/data/{dados["data_atual"]}" target="_blank">/api/data/{dados["data_atual"]}</a>
        </div>

        <div class="peg-card">
          <div class="peg-card-title">Como a Sam pode consultar</div>

          <p><strong>Data e hora atual:</strong><br>/api/horario</p>
          <p><strong>Mês atual:</strong><br>/api/calendario</p>
          <p><strong>Ano completo:</strong><br>/api/calendario/2026</p>
          <p><strong>Mês específico:</strong><br>/api/calendario/2026/04</p>
          <p><strong>Data específica:</strong><br>/api/data/2026-04-30</p>
        </div>
      </div>

      <div id="calendarioVisual" class="peg-calendar"></div>

      <pre id="jsonIntegracao" class="peg-json"></pre>

      <div class="peg-footer">
        PEG do Brasil - Data, hora e calendário atualizados automaticamente pelo fuso de Brasília
      </div>

    </div>
  </main>

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

        html += `<div class="peg-calendar-header">${{calendario.mes_nome}} de ${{calendario.ano}}</div>`;
        html += `<div class="peg-calendar-grid">`;

        nomesDias.forEach(nome => {{
          html += `<div class="peg-calendar-day-name">${{nome}}</div>`;
        }});

        calendario.semanas.forEach(semana => {{
          semana.forEach(dia => {{
            if (!dia) {{
              html += `<div class="peg-calendar-day empty"></div>`;
            }} else {{
              const hoje = dia.data === calendario.hoje.data_atual ? "today" : "";
              html += `
                <div class="peg-calendar-day ${{hoje}}">
                  <div class="peg-calendar-number">${{dia.dia}}</div>
                  <div class="peg-calendar-info">${{dia.dia_semana}}</div>
                  <div class="peg-calendar-info">${{dia.funcionamento_previsto}}</div>
                </div>
              `;
            }}
          }});
        }});

        html += `</div>`;

        document.getElementById("calendarioVisual").innerHTML = html;

      }} catch (erro) {{
        document.getElementById("calendarioVisual").innerHTML =
          "<div class='peg-calendar-header'>Erro ao carregar calendário</div>";
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
