import streamlit as st
import pandas as pd
import numpy as np
import random
import copy

# Configuração da Página
st.set_page_config(page_title="UniFUT Simulação", layout="wide", page_icon="⚽")

# --- CLASSES ESTRUTURAIS ---

class Team:
    def __init__(self, name, league, conference, division, rating):
        self.name = name
        self.league = league # 'LNF', 'College 1', 'College 2'
        self.conference = conference
        self.division = division # Para LNF: Norte, Sul, etc. Para College: Nome da Conferência
        self.rating = rating # 0 a 100
        self.wins = 0
        self.losses = 0
        self.draws = 0
        self.points = 0
        self.goals_for = 0
        self.goals_against = 0
        self.schedule = []
        
    def reset_stats(self):
        self.wins = 0
        self.losses = 0
        self.draws = 0
        self.points = 0
        self.goals_for = 0
        self.goals_against = 0

    @property
    def goal_diff(self):
        return self.goals_for - self.goals_against

    @property
    def games_played(self):
        return self.wins + self.losses + self.draws

class UniFUTEngine:
    def __init__(self):
        self.teams = []
        self.season_year = 2026
        
    def add_team(self, team):
        self.teams.append(team)
        
    def get_teams_by_league(self, league):
        return [t for t in self.teams if t.league == league]

    def simulate_match(self, team_a, team_b, is_knockout=False):
        # Lógica simples de simulação baseada em Rating + Fator Casa
        home_advantage = 5
        diff = (team_a.rating + home_advantage) - team_b.rating
        
        # Probabilidade baseada na diferença
        prob_a = 1 / (1 + 10 ** (-diff / 400)) # Elo-like formula simplified
        
        # Geração de gols (Poisson)
        # Média de gols baseada na força relativa
        avg_goals = 2.5
        goals_a = np.random.poisson(avg_goals * (prob_a + 0.1))
        goals_b = np.random.poisson(avg_goals * ((1 - prob_a) + 0.1))
        
        if is_knockout and goals_a == goals_b:
            # Pênaltis ou Prorrogação (decisão forçada)
            winner = random.choice([team_a, team_b])
            if winner == team_a: goals_a += 1
            else: goals_b += 1
            
        return goals_a, goals_b

    def update_table(self, team_a, team_b, goals_a, goals_b):
        team_a.goals_for += goals_a
        team_a.goals_against += goals_b
        team_b.goals_for += goals_b
        team_b.goals_against += goals_a
        
        if goals_a > goals_b:
            team_a.wins += 1
            team_a.points += 3
            team_b.losses += 1
        elif goals_b > goals_a:
            team_b.wins += 1
            team_b.points += 3
            team_a.losses += 1
        else:
            team_a.draws += 1
            team_a.points += 1
            team_b.draws += 1
            team_b.points += 1

# --- INICIALIZAÇÃO DOS DADOS (BASEADO NO PDF) ---

@st.cache_resource
def initialize_system():
    engine = UniFUTEngine()
    
    # 1. LNF (MANTÉM IGUAL AO ANTERIOR - HARDCODED É MAIS SEGURO PARA ELITE)
    # (Copie a lista lnf_data do código anterior aqui, pois ela já está correta conforme o PDF)
    lnf_data = [
        ("Flamengo", "Brasileira", "Leste", 92), ("Bahia", "Brasileira", "Leste", 85),
        ("Atlético-MG", "Brasileira", "Leste", 89), ("Athletico-PR", "Brasileira", "Leste", 86),
        ("Corinthians", "Brasileira", "Oeste", 88), ("Vitória", "Brasileira", "Oeste", 82),
        ("Cuiabá", "Brasileira", "Oeste", 83), ("Juventude", "Brasileira", "Oeste", 81),
        ("Botafogo", "Brasileira", "Norte", 90), ("Ceará", "Brasileira", "Norte", 84),
        ("Remo", "Brasileira", "Norte", 78), ("Chapecoense", "Brasileira", "Norte", 79),
        ("Palmeiras", "Brasileira", "Sul", 93), ("Fortaleza", "Brasileira", "Sul", 88),
        ("Ponte Preta", "Brasileira", "Sul", 77), ("Paysandu", "Brasileira", "Sul", 78),
        ("São Paulo", "Nacional", "Leste", 89), ("Grêmio", "Nacional", "Leste", 87),
        ("Criciúma", "Nacional", "Leste", 80), ("Atlético-GO", "Nacional", "Leste", 81),
        ("Fluminense", "Nacional", "Oeste", 86), ("Sport", "Nacional", "Oeste", 83),
        ("Guarani", "Nacional", "Oeste", 76), ("Coritiba", "Nacional", "Oeste", 82),
        ("Internacional", "Nacional", "Norte", 88), ("RB Bragantino", "Nacional", "Norte", 85),
        ("Goiás", "Nacional", "Norte", 82), ("Avaí", "Nacional", "Norte", 79),
        ("Vasco", "Nacional", "Sul", 86), ("Cruzeiro", "Nacional", "Sul", 88),
        ("América-MG", "Nacional", "Sul", 81), ("Santos", "Nacional", "Sul", 87)
    ]
    
    for name, conf, div, rating in lnf_data:
        engine.add_team(Team(name, "LNF", conf, div, rating))
        
    # 2. COLLEGE (CARREGAR DO JSON)
    # Verifica se o arquivo existe. Se não, gera dados dummy para não quebrar.
    if os.path.exists("teams_db.json"):
        with open("teams_db.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # Carregar College 1
        for team in data.get("college1", []):
            engine.add_team(Team(team["name"], "College 1", "College", team["conference"], team["rating"]))
            
        # Carregar College 2
        for team in data.get("college2", []):
            engine.add_team(Team(team["name"], "College 2", "College", team["conference"], team["rating"]))
    else:
        # Fallback caso o usuário esqueça de rodar o db_builder
        print("AVISO: teams_db.json não encontrado. Rodar db_builder.py")
        # (Aqui entraria o código antigo de geração aleatória como backup)

    return engine

# --- INTERFACE E SIMULAÇÃO ---

def run_lnf_regular_season(engine):
    lnf_teams = engine.get_teams_by_league("LNF")
    # Resetar
    for t in lnf_teams: t.reset_stats()
    
    # Simulação Simplificada de 19 jogos
    # Para ser rápido, vamos simular confrontos baseados na lógica de força
    progress_bar = st.progress(0)
    total_games = len(lnf_teams) * 19 // 2
    games_played = 0
    
    for team in lnf_teams:
        # Encontrar oponentes (Lógica simplificada para demo)
        # Na versão final, implementar a lógica exata de rodízio do PDF
        opponents = random.sample([t for t in lnf_teams if t != team], 19)
        
        for opp in opponents:
            # Evitar duplicidade de processamento (A x B e B x A)
            # Aqui, apenas processamos o resultado para a tabela
            g_a, g_b = engine.simulate_match(team, opp)
            team.goals_for += g_a
            team.goals_against += g_b
            if g_a > g_b:
                team.wins += 1
                team.points += 3
            elif g_b > g_a:
                team.losses += 1
            else:
                team.draws += 1
                team.points += 1
                
    st.toast("Temporada Regular LNF Concluída!")

def get_standings_df(teams):
    data = []
    for t in teams:
        data.append({
            "Time": t.name,
            "Conf": t.conference if t.league == 'LNF' else t.division,
            "Div": t.division if t.league == 'LNF' else '-',
            "Pts": t.points,
            "V": t.wins,
            "E": t.draws,
            "D": t.losses,
            "GP": t.goals_for,
            "GC": t.goals_against,
            "SG": t.goal_diff
        })
    df = pd.DataFrame(data)
    return df.sort_values(by=["Pts", "V", "SG"], ascending=False).reset_index(drop=True)

# --- APP STREAMLIT ---

st.title("UniFUT - Sistema Nacional de Futebol 2026")
st.markdown("**Simulador Oficial da Nova Estrutura do Futebol Brasileiro**")

if "engine" not in st.session_state:
    st.session_state.engine = initialize_system()
    st.session_state.simulated_lnf = False

engine = st.session_state.engine

# Sidebar
st.sidebar.header("Controle de Simulação")
season_year = st.sidebar.number_input("Ano da Temporada", value=2026)

if st.sidebar.button("Simular Temporada Regular LNF"):
    run_lnf_regular_season(engine)
    st.session_state.simulated_lnf = True

# Abas Principais
tab_lnf, tab_college, tab_copas, tab_draft = st.tabs(["LNF (Elite)", "College (Base)", "Copas & Bowls", "Draft"])

with tab_lnf:
    st.header(f"Liga Nacional de Futebol - {season_year}")
    
    if st.session_state.simulated_lnf:
        # Exibir tabelas por Conferência
        col1, col2 = st.columns(2)
        
        lnf_teams = engine.get_teams_by_league("LNF")
        df = get_standings_df(lnf_teams)
        
        with col1:
            st.subheader("Conferência Brasileira")
            df_br = df[df["Conf"] == "Brasileira"].drop(columns=["Conf"])
            st.dataframe(df_br, height=400)
            
        with col2:
            st.subheader("Conferência Nacional")
            df_nac = df[df["Conf"] == "Nacional"].drop(columns=["Conf"])
            st.dataframe(df_nac, height=400)
            
        st.divider()
        st.subheader("Simulação de Playoffs (Top 7 por Conferência)")
        if st.button("Gerar Playoffs LNF"):
            # Lógica simples de pegar os Top 7
            top7_br = df_br.head(7)["Time"].tolist()
            top7_nac = df_nac.head(7)["Time"].tolist()
            
            st.write(f"**Classificados Brasileira:** {', '.join(top7_br)}")
            st.write(f"**Classificados Nacional:** {', '.join(top7_nac)}")
            
            # Super Bowl Simulado
            finalist_br = top7_br[0] # Simplificação: Seed 1 vence
            finalist_nac = top7_nac[0]
            
            st.success(f"🏆 SUPER BOWL BRASILEIRO: {finalist_br} vs {finalist_nac}")
            score_a, score_b = engine.simulate_match(
                next(t for t in lnf_teams if t.name == finalist_br),
                next(t for t in lnf_teams if t.name == finalist_nac),
                is_knockout=True
            )
            st.metric(label="Resultado Final", value=f"{finalist_br} {score_a} x {score_b} {finalist_nac}")
            
    else:
        st.info("Clique em 'Simular Temporada Regular' no menu lateral para iniciar.")
        st.write("Estrutura carregada: 32 Franquias, 2 Conferências, 8 Divisões.")

with tab_college:
    st.header("Sistema Secundário (College 1)")
    st.write("96 Times divididos em 8 Conferências Regionais.")
    
    college_teams = engine.get_teams_by_league("College 1")
    
    # Filtro por conferência
    confs = list(set([t.division for t in college_teams]))
    selected_conf = st.selectbox("Selecione a Conferência", confs)
    
    # Mostrar times da conferência
    conf_teams = [t for t in college_teams if t.division == selected_conf]
    df_college = pd.DataFrame([{"Time": t.name, "Rating": t.rating} for t in conf_teams])
    st.dataframe(df_college)
    
    st.info("A simulação detalhada do College (20 jogos) será implementada na v2 do software.")

with tab_copas:
    st.header("Copas & Bowls")
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("Copa do Brasil (CBF)")
        st.write("Integração LNF + College + Qualification League.")
        st.write("*Formato de 5 Fases definido no manual.*")
        
    with col_b:
        st.subheader("Copa da Liga (UniFUT)")
        st.write("Exclusiva para os 192 times do College.")
        st.write("*Mata-mata em jogo único com mando do menor.*")

with tab_draft:
    st.header("Draft UniFUT")
    st.write("Ordem de escolha baseada na campanha inversa da LNF.")
    st.write("Jogadores elegíveis do College (mínimo 2 anos de sistema).")
    
    if st.session_state.simulated_lnf:
        lnf_teams = engine.get_teams_by_league("LNF")
        # Ordenar reverso por pontos (Pior primeiro)
        draft_order = sorted(lnf_teams, key=lambda x: x.points)
        
        st.subheader("Ordem do Draft - Top 10 Picks")
        for i, team in enumerate(draft_order[:10]):
            st.text(f"Pick #{i+1}: {team.name}")
    else:
        st.warning("Simule a temporada da LNF para definir a ordem do Draft.")
