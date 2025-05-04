from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from datetime import datetime
import re
import unicodedata
import random
import time
import json

app = Flask(__name__)

# Função para procurar os dados sobre jogos da FURIA na hltv
def scraping_agenda():

    # Configurar o Selenium
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=options)

    # URL do time da furia na hltv
    url = "https://www.hltv.org/team/8297/furia#tab-matchesBox"
    driver.get(url)

    # Esperar carregar
    time.sleep(5)

    # Pegar HTML carregado
    html = driver.page_source
    driver.quit()
    soup = BeautifulSoup(html, "html.parser")
    matches_box = soup.find('div', id='matchesBox')
    agenda = []
    current_event = None
    # Passa por todos os elementos dos jogos, e salvam eles na string agenda
    for element in matches_box.find_all(['thead', 'tbody']):
        if element.name == 'thead':
            event_link = element.find('a')
            if event_link:
                current_event = event_link.text.strip()
        elif element.name == 'tbody':
            rows = element.find_all('tr', class_='team-row')
            for row in rows:
                date_cell = row.find('td', class_='date-cell')
                date_text = date_cell.text.strip() if date_cell else "Data desconhecida"
                teams = row.find_all('a', class_='team-name')
                team1 = teams[0].text.strip() if len(teams) > 0 else "Time 1 desconhecido"
                team2 = teams[1].text.strip() if len(teams) > 1 else "Time 2 desconhecido"
                score_spans = row.find('div', class_="score-cell").find_all('span', class_="score")
                score1 = score_spans[0].text.strip() if len(score_spans) > 0 else "-"
                score2 = score_spans[1].text.strip() if len(score_spans) > 1 else "-"

                agenda.append({
                    "evento": current_event,
                    "data": date_text,
                    "time1": team1,
                    "score1": score1,
                    "time2": team2,
                    "score2": score2
                })
    return agenda

def formatar_ultimos_resultados(jogos):

    # Filtra os resultados passados (com data anterior a hoje)
    resultados_passados = []
    hoje = datetime.now()
    for jogo in jogos:
        try:
            data_jogo = datetime.strptime(jogo['data'], "%d/%m/%Y")
            if data_jogo < hoje:
                resultados_passados.append((data_jogo, jogo))
        except ValueError:
            continue  # Ignora jogos com datas inválidas

    if not resultados_passados:
        return "Não encontrei resultados passados da FURIA. 😢"

    # Ordena pela data e pega os 5 mais recentes
    resultados_passados.sort(key=lambda x: x[0], reverse=True)
    ultimos_resultados = resultados_passados[:5]

    # Formata a mensagem com <br> para o chat
    resposta = "📅 <strong>Últimos 5 resultados da FURIA:</strong><br>"
    for jogo_data, jogo in ultimos_resultados:
        resposta += f"🏆 {jogo['evento']}<br>"
        resposta += f"📆 {jogo['data']}<br>"
        resposta += f"🔫 {jogo['time1']} {jogo['score1']} vs {jogo['score2']} {jogo['time2']}<br><br>"

    return resposta

def formatar_agenda_proximo(jogos):

    # Tenta converter a data de cada jogo e filtra os futuros
    jogos_futuros = []
    hoje = datetime.now()

    for jogo in jogos:
        try:
            data_jogo = datetime.strptime(jogo['data'], "%d/%m/%Y")
            if data_jogo >= hoje:
                jogos_futuros.append((data_jogo, jogo))
        except ValueError:
            continue  # Se falhar ao converter a data, ignora

    if not jogos_futuros:
        return "Não encontrei nenhum jogo futuro da FURIA no momento. 😢"

    # Ordena pela data e pega o próximo
    jogos_futuros.sort(key=lambda x: x[0])
    _, proximo = jogos_futuros[0]

    # Formata a mensagem com <br> para o chat
    resposta = "📅 <strong>Próximo jogo da FURIA:</strong><br>"
    resposta += f"🏆 {proximo['evento']}<br>"
    resposta += f"📆 {proximo['data']}<br>"
    resposta += f"🔫 {proximo['time1']} {proximo['score1']} vs {proximo['score2']} {proximo['time2']}<br>"

    return resposta

# Função para remover acentos
def remover_acentos(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

# Lógica do bot em Python (com respostas predefinidas)
def bot_response(user_message):

    # Respostas possíveis para diferentes cumprimentos
    greetings = ["ola", "oi", "eae", "opa"]
    gratidões = ["valeu", "vlw", "obrigado", "obg"]
    curiosidades = [
        """A FURIA é a única equipe brasileira que participou de todos os Majors desde 2019. É o time do Brasil! [flag_br] """,
        """A melhor campanha da equipe até hoje em Majors foi a chegada às semifinais do IEM Rio Major 2022, com a vitória histórica 
        sobre a NAVI nas quartas de final""",
        """Com menos de dois anos dentro do CS, a FURIA conquistou o que era sonho de muitas organizações há anos já no FPS da Valve:
        a classificação para um Major.""",
        """O nickname KSCERATO é uma abreviação do seu nome completo: Kaike Silva Cerato.""",
        """Na lineup atual, o KSCERATO é o único jogador que veio da nossa academia, a Furia ACADEMY""",
        """Em 2022 a FURIA fem, alcançou uma marca histórica sendo a única equipe de CS no top 10 das equipes femininas mais assistidas de 2022""",
        """A FURIA também é uma marca de moda 😎! Feita para quem vive o jogo! Disponível em: 'furia.gg'""",
        """A vitória histórica da FURIA contra a NAVI no IEM Major Rio 2022, teve um público de mais de 18 mil torcedores na Jeunesse Arena,
        além disso, alcançou máximo de 1.428.993 espectadores simultâneos nas transmissões online, HISTÓRICO! 🎉""",
        """A primeira lineup da história da FURIA foi A primeira lineup foi composta por Caike “caike” Costa, Vinicius “VINI” 
        Figueiredo, Guilherme “spacca” Spacca, Arthur “prd” Resende, Bruno “Sllayer” Silva e Nicholas “guerri” Nogueira, que 
        conquistaram o vice campeonato da Experience League no ano de sua fundação""",
        """A FURIA foi fundada em fevereiro de 2017 pelo empresário Jaime Pádua, e pelos empreendedores André Akkari 
        (jogador profissional de pôquer) e Cris Guedes.""",
        """A maior premiação em dinheiro que a equipe da FURIA já recebeu foi de $100,000 em duas ocasiões. Sendo elas: Vice-campeão no 
        Esports Championship Series Season 7 - Finals e campeão no Elisa Masters Espoo 2023""",
        """O apelido "Professor" do FalleN surgiu quando ele começou a dar aulas de Counter-Strike, e posteriormente, da sua academia de 
        treinamento FalleN Academy, e se tornou viral quando o streamer Gaules começou a usar o apelido em suas transmissões. Presente professor!"""
    ]

    # Remover acentos da mensagem do usuário para comparações sem acento
    message = remover_acentos(user_message.lower())
    if "fallen" in message and message.strip() != "fallen":
        return """Você quer saber sobre o FalleN? Se sim, digite apenas "FalleN". Se quiser saber sobre toda a lineup, digite "lineup" """
    if "kscerato" in message and message.strip() != "kscerato":
        return """Você quer saber sobre o KSCERATO? Se sim, digite apenas "KSCERATO". Se quiser saber sobre toda a lineup, digite "lineup" """
    if "yuurih" in message and message.strip() != "yuurih":
        return """Você quer saber sobre o yuurih? Se sim, digite apenas "yuurih". Se quiser saber sobre toda a lineup, digite "lineup" """
    if "molodoy" in message and message.strip() != "molodoy":
        return """Você quer saber sobre o molodoy? Se sim, digite apenas "molodoy". Se quiser saber sobre toda a lineup, digite "lineup" """
    if "yekindar" in message and message.strip() != "yekindar":
        return """Você quer saber sobre o YEKINDAR? Se sim, digite apenas "YEKINDAR". Se quiser saber sobre toda a lineup, digite "lineup" """
    if "kaahsensei" in message and message.strip() != "kaahsensei":
        return """Você quer saber sobre a kaahSENSEI? Se sim, digite apenas "kaahSENSEI". Se quiser saber sobre toda a lineup feminina, digite "lineup fem" """
    if "gabs" in message and message.strip() != "gabs":
        return """Você quer saber sobre a gabs? Se sim, digite apenas "gabs". Se quiser saber sobre toda a lineup feminina, digite "lineup fem" """
    if "izaa" in message and message.strip() != "izaa":
        return """Você quer saber sobre a izaa? Se sim, digite apenas "izaa". Se quiser saber sobre toda a lineup feminina, digite "lineup fem" """
    if "lulitenz" in message and message.strip() != "lulitenz":
        return """Você quer saber sobre a lulitenz? Se sim, digite apenas "lulitenz". Se quiser saber sobre toda a lineup feminina, digite "lineup fem" """
    if "bizinha" in message and message.strip() != "bizinha":
        return """Você quer saber sobre a bizinha? Se sim, digite apenas "bizinha". Se quiser saber sobre toda a lineup feminina, digite "lineup fem" """
    if "proximo jogo" in message and message.strip() != "proximo jogo":
        return """Você quer saber sobre o próximo jogo? Se sim, digite apenas "proximo jogo"."""
    if "curiosidade" in message and message.strip() != "curiosidades":
        return """Você quer saber curiosidades? Se sim, digite apenas "curiosidades"."""
    if "uniforme" in message and message.strip() != "uniforme":
        return """Você quer saber sobre a linha de moda da FURIA? Se sim, digite apenas "uniforme"."""
    if "resultado" in message and message.strip() != "resultados":
        return """Você quer saber os resultados anteriores da FURIA? Se sim, digite apenas "resultados"."""
    if "proximo" in message and message.strip() != "proximos jogos":
        return """Você quer saber quais serão os próximos jogos da FURIA? Se sim, digite apenas "proximos jogos"."""
    if message.strip() == "proximos jogos":
        jogos = scraping_agenda()
        resposta = formatar_agenda_proximo(jogos)
        return resposta
    if message.strip() == "resultados":
        jogos = scraping_agenda()
        resposta = formatar_ultimos_resultados(jogos)
        return resposta
    
    # Resposta para cumprimentos
    if any(greeting in message for greeting in greetings):
        return "Eae furioso! Bem-vindo ao ChatFURIOSO CS, feito para os fãs da FURIA no CS2, aproveite! GLHF😎"
    if any(gratidõe in message for gratidõe in gratidões):
        return "Não tem de que! Pode contar sempre com a gente!😎"
    
    # Respostas gerais
    responses = {
        "saiba mais players": """Quer saber mais dos nossos jogadores? Só escrever o nome do player (masculino ou feminino) que eu vou contar uns fatos daoras 
        sobre eles pra você! 😎""",
        "fallen": """O FalleN, ou carinhosamente chamado de Professor, é um dos maiores nomes do Counter-Strike mundial, bicampeão de Majors e referência no 
        cenário brasileiro, sendo eleito o segundo (2016) e o quinto (2017) melhor jogador do mundo 🌎. Além de jogador, nosso professor também é empresário 🤵 e foi eleito pela Forbes uma 
        das 30 personalidades mais influentes dos games, ele é sensacional. Atualmente, arrebenta todo mundo pela FURIA com suas táticas e suas plays de AWP, e já tá marcado na história.
        Isso é Gabriel Toledo!""",
        "yuurih": """O yuurih é um dos pilares do nosso time. Ganhou destaque no CS:GO e se firmou como peça-chave da equipe em transições importantes, incluindo a chegada 
        ao CS2. Conhecido por seu estilo agressivo de rifle, mira precisa 🎯 e sangue frio nos clutchs! Já foi eleito o décimo-quarto 
        (2020) e o décimo-nono (2022) melhor jogador do mundo, simplesmente incrível! Faz parte da FURIA desde 2017 e sempre honrou a 
        nossa camisa!""",
        "kscerato": """O KSCERATO é uma estrela ⭐! Sendo nosso jogador-chave em diversas ocasiões, tem um jogo muito inteligente e 
        consegue vencer clutchs como ninguém. É uma peça fundamental da FURIA desde 2018, além disso passou pela FURIA Academy antes 
        de entrar no time principal! Já foi eleito o décimo-oitavo (2020), décimo-quinto (2021), nono (2022) e décimo-nono (2023) melhor jogador do mundo, FENÔMENO! 🎯""",
        "yekindar": """O YEKINDAR é uma das novas contratações da FURIA! É um dos jogadores mais agressivos e impactantes do cenário de CS2, 
        tem um estilo explosivo e é capaz de decidir rodadas! Natural da Letônia, rapidamente chamou atenção 
        internacional com suas atuações, e se tornou referência no papel de entry fragger. Já foi eleito o oitavo (2021) e o décimo-quinto (2022) melhor jogador do mundo,
        e agora está vindo para brilhar na FURIA!✨""",
        "molodoy": """O molodoy é o caçula da FURIA, com apenas 20 anos e uma mira insana! Natural do Cazaquistão, o jovem talento da FURIA vem
        se destacando como um dos AWPers mais promissores do cenário. Com apenas um ano de carreira profissional, já apresentou 
        estatísticas impressionantes, como rating de 1.26 e impacto de quase 1.30 em 2025🤯. Ainda vamos ouvir falar muito desse muleque brilhando pela FURIA!""",
        "gabs": """Com seu estilo agressivo e preciso, gabs se destaca pela mira afiada 🎯 e pela leitura rápida das jogadas. É uma das 
        peças mais impactantes da nossa equipe e constantemente desequilibra rounds a favor da FURIA.""",
        "izaa": """Versátil e técnica, a nossa capitã izaa brilha tanto em situações de clutch quanto como suporte tático, é a cabeça da nossa equipe! 
        Sua calma sob pressão e consistência fazem dela uma jogadora destaque na nossa equipe. É uma das jogadoras mais antigas da equipe, defendendo nossa camisa
        há mais de 5 anos, ÍDOLA! ⭐""",
        "kaahsensei": """A kaahSENSEI é uma referência do time feminino da FURIA, ela combina toda sua experiência com sua inteligência tática. 
        É conhecida por seu poder dentro de clutchs e por guiar a equipe com confiança e visão de jogo. É a atleta mais antiga da FURIA e
        defende nossa equipe com todo amor possível, ela é ídola máxima do nosso time! ❤️""",
        "bizinha": """A bizinha se destaca por causa da regularidade e comunicação no jogo, é uma jogadora estratégica que dá muita calma
        pra toda a equipe! É um dos pilares pro sucesso desse time!""",
        "lulitenz": """Representando a Argentina [flag_ag] na FURIA! Nossa hermana lulitenz tem muita garra e criatividade dentro do servidor. 
        Com jogadas imprevisíveis e ousadas, traz uma energia única pra dentro do time e surpreende geral com sua capacidade de decisão!""",
        "lineup": """Atualmente, os defensores do nosso manto são:<br>
        [flag_br] yuurih - Yuri Santos<br>
        [flag_br] KSCERATO - Kaike Cerato<br>
        [flag_br] FalleN©️ - Gabriel Toledo<br>
        [flag_kz] molodoy - Danil Golubenko<br>
        [flag_lv] YEKINDAR - Mareks Galinskis""",
        "lineup fem": """Atualmente, as defensoras do nosso manto são:<br>
        [flag_br] kaahSENSEI - Karina Takahashi<br>
        [flag_br] gabs - Gabriela Freindorfer<br>
        [flag_br] izaa©️ - Izabella Galle<br>
        [flag_br] bizinha - Bruna Marvila<br>
        [flag_ag] lulitenz - Lucia Dubra""",
        "uniforme": "Garanta já seu uniforme do time de CS da FURIA e se mostre um verdadeiro FURIOSO 😎 em: 'furia.gg'\nNão vai perder em?",
        "curiosidades": random.choice(curiosidades),
        "outros jogos": """A FURIA participa de muitos outros jogos que você pode acompanhar! Dá uma olhada:<br>
        Valorant🎯<br>
        League of Legends🧙‍♂️<br>
        PUBG🪖<br>
        Rainbow Six🧨<br>
        Rocket League🚗<br>
        Apex Legends🪂<br>
        Futebol de 7⚽<br>
        Vem acompanhar a FURIA nos outros esportes e se tornar um verdadeiro FURIOSO!""",
        "default": "Opa, não entendi o que voce quis dizer 🤔. Pode digitar de novo?"
    }

    return responses.get(message, responses["default"])

# Rota principal que renderiza o HTML
@app.route('/')
def index():
    return render_template('index.html')

# Rota para o envio de mensagens do chat
@app.route('/send_message', methods=['POST'])
def send_message():
    user_message = request.form['user_message']
    response = bot_response(user_message)
    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(debug=True)
