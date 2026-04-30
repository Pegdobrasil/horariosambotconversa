from flask import Flask, jsonify, Response
from datetime import datetime
from zoneinfo import ZoneInfo
import os

app = Flask(__name__)

TIMEZONE_BRASILIA = ZoneInfo("America/Sao_Paulo")


def obter_dados_horario():
    agora = datetime.now(TIMEZONE_BRASILIA)

    dias_semana = {
        0: "segunda-feira",
        1: "terça-feira",
        2: "quarta-feira",
        3: "quinta-feira",
        4: "sexta-feira",
        5: "sábado",
        6: "domingo"
    }

    meses = {
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

    dia_semana_numero = agora.weekday()
    dia_semana = dias_semana[dia_semana_numero]

    data_atual = agora.strftime("%Y-%m-%d")
    hora_atual = agora.strftime("%H:%M:%S")

    data_extenso = f"{dia_semana}, {agora.day:02d} de {meses[agora.month]} de {agora.year}"

    minutos_atuais = agora.hour * 60 + agora.minute

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
        mensagem_atendimento = "Estamos em horário de atendimento."
        status_atendimento = "aberto"
    else:
        mensagem_atendimento = "Estamos fora do horário de atendimento."
        status_atendimento = "fechado"

    dados = {
        "empresa": "PEG do Brasil",
        "timezone": "America/Sao_Paulo",
        "data_atual": data_atual,
        "data_extenso": data_extenso,
        "dia_semana": dia_semana,
        "hora_atual": hora_atual,
        "ano_atual": agora.year,
        "mes_atual": agora.month,
        "dia_mes": agora.day,
        "hora_numero": agora.hour,
        "minuto_numero": agora.minute,
        "segundo_numero": agora.second,
        "atendimento_aberto": atendimento_aberto,
        "status_atendimento": status_atendimento,
        "mensagem_atendimento": mensagem_atendimento,
        "horario_funcionamento": {
            "segunda_a_sexta": "09:00 às 18:00",
            "sabado": "09:00 às 13:00",
            "domingo": "Fechado"
        }
    }

    return dados


@app.route("/")
def index():
    dados = obter_dados_horario()

    html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <title>Horário de Brasília - PEG do Brasil</title>

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
      max-width: 900px;
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
      background-size: 360px auto;
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

    .peg-api-box {{
      margin-top: 28px;
      text-align: left;
    }}

    .peg-api-title {{
      font-size: 16px;
      font-weight: 800;
      color: #002b5c;
      margin-bottom: 10px;
    }}

    .peg-api-link {{
      display: block;
      background: #eff6ff;
      color: #005c99;
      padding: 12px;
      border-radius: 10px;
      font-size: 14px;
      text-decoration: none;
      border: 1px solid #bfdbfe;
      margin-bottom: 12px;
      word-break: break-word;
    }}

    .peg-json {{
      background: #0f172a;
      color: #e5e7eb;
      padding: 16px;
      border-radius: 12px;
      text-align: left;
      font-size: 14px;
      line-height: 1.6;
      white-space: pre-wrap;
      word-break: break-word;
      margin: 0;
    }}

    .peg-footer {{
      margin-top: 20px;
      font-size: 13px;
      color: #64748b;
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
    }}
  </style>
</head>

<body>

  <main class="peg-wrapper">
    <div class="peg-content">

      <h1 class="peg-title">Horário de Brasília</h1>

      <p class="peg-subtitle">
        Consulta de data e hora atual para integração da Sam - PEG do Brasil
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

      <div class="peg-api-box">
        <div class="peg-api-title">Endpoint para o BotConversa:</div>

        <a class="peg-api-link" href="/api/horario" target="_blank">
          /api/horario
        </a>

        <div class="peg-api-title">Resposta atual:</div>

        <pre id="jsonIntegracao" class="peg-json"></pre>
      </div>

      <div class="peg-footer">
        PEG do Brasil - Data e hora atualizadas automaticamente pelo fuso de Brasília
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

    atualizarHorario();
    setInterval(atualizarHorario, 1000);
  </script>

</body>
</html>
"""

    return Response(html, mimetype="text/html")


@app.route("/api/horario")
def api_horario():
    dados = obter_dados_horario()
    return jsonify(dados)


@app.route("/health")
def health():
    return jsonify({
        "status": "online",
        "servico": "horario-peg"
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
