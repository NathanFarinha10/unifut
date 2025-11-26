import streamlit as st
import pandas as pd
import numpy as np
import random
import copy
import json 
import os

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

class LNFScheduler:
    def __init__(self, teams, year):
        self.teams = teams
        self.year = year
        # Mapear estrutura: Conf -> Div -> Lista de Times (ordenados por Seed/Rating)
        self.structure = self._build_structure()

    def _build_structure(self):
        struct = {}
        for t in self.teams:
            if t.conference not in struct: struct[t.conference] = {}
            if t.division not in struct[t.conference]: struct[t.conference][t.division] = []
            struct[t.conference][t.division].append(t)
        
        # Ordenar cada divisão por Rating (simulando seed do ano anterior)
        for conf in struct:
            for div in struct[conf]:
                struct[conf][div].sort(key=lambda x: x.rating, reverse=True)
        return struct

    def generate_schedule(self):
        schedule = [] # Lista de tuplas (Home, Away, Tipo)
        
        confs = list(self.structure.keys()) # ['Brasileira', 'Nacional']
        divs_order = ["Leste", "Oeste", "Norte", "Sul"] # Ordem padrão para rodízio
        
        # Lógica de Rodízio baseada no ano (Cyclic)
        # Ex: Ano 0 -> Leste x Oeste. Ano 1 -> Leste x Norte...
        rotation_offset = self.year % 3 
        
        for conf in confs:
            for div_name in divs_order:
                my_div_teams = self.structure[conf][div_name]
                
                # --- 1. JOGOS DIVISIONAIS (6 Jogos) ---
                # Ida e volta contra todos da mesma divisão
                for i in range(len(my_div_teams)):
                    for j in range(i + 1, len(my_div_teams)):
                        t1, t2 = my_div_teams[i], my_div_teams[j]
                        schedule.append((t1, t2, "Divisional"))
                        schedule.append((t2, t1, "Divisional"))

                # Definir Oponentes de Rodízio
                # Lógica simplificada: Divisões mapeadas por índice 0..3
                idx = divs_order.index(div_name)
                
                # Alvo Intra-Conferência (Rodízio)
                # Ex: 0 enfrenta 1, 2 enfrenta 3... rotacionando com o ano
                intra_target_idx = (idx + 1 + rotation_offset) % 4
                intra_target_div = divs_order[intra_target_idx]
                intra_opponents = self.structure[conf][intra_target_div]
                
                # Alvo Inter-Conferência (Rodízio)
                other_conf = [c for c in confs if c != conf][0]
                inter_target_idx = (idx + rotation_offset) % 4
                inter_target_div = divs_order[inter_target_idx]
                inter_opponents = self.structure[other_conf][inter_target_div]

                # Iterar sobre meu time (t1) e gerar jogos contra as divisões alvo
                for i, t1 in enumerate(my_div_teams):
                    # Seed do t1 (0 a 3)
                    seed_t1 = i 
                    
                    # --- 2. INTRA-CONFERÊNCIA RODÍZIO (4 Jogos) ---
                    # Enfrenta toda a divisão alvo (Single game)
                    for t2 in intra_opponents:
                        # Mando aleatório para balancear
                        if random.choice([True, False]): schedule.append((t1, t2, "Intra-Rot"))
                        else: schedule.append((t2, t1, "Intra-Rot"))

                    # --- 3. INTER-CONFERÊNCIA RODÍZIO (4 Jogos) ---
                    # Enfrenta toda a divisão alvo da outra conf (Single game)
                    for t2 in inter_opponents:
                        if random.choice([True, False]): schedule.append((t1, t2, "Inter-Rot"))
                        else: schedule.append((t2, t1, "Inter-Rot"))
                        
                    # --- JOGOS POR POSIÇÃO (Seeds iguais se enfrentam) ---
                    
                    # Divisões que SOBRARAM na minha conferência (não é a minha, nem a do rodízio)
                    remaining_intra_divs = [d for d in divs_order if d != div_name and d != intra_target_div]
                    
                    # --- 4. INTRA-POSIÇÃO (2 Jogos) ---
                    for rem_div in remaining_intra_divs:
                        # Pega o time de MESMO SEED na divisão restante
                        rival = self.structure[conf][rem_div][seed_t1]
                        if random.choice([True, False]): schedule.append((t1, rival, "Intra-Pos"))
                        else: schedule.append((rival, t1, "Intra-Pos"))
                    
                    # Divisões que SOBRARAM na outra conferência
                    remaining_inter_divs = [d for d in divs_order if d != inter_target_div]
                    
                    # --- 5. INTER-POSIÇÃO (3 Jogos) ---
                    for rem_div in remaining_inter_divs:
                        rival = self.structure[other_conf][rem_div][seed_t1]
                        if random.choice([True, False]): schedule.append((t1, rival, "Inter-Pos"))
                        else: schedule.append((rival, t1, "Inter-Pos"))

        # Limpeza: Como iteramos por divisão, jogos "Single Game" (Intra/Inter) podem ser gerados duplicados
        # (A gera contra B, depois B gera contra A). Vamos remover duplicatas.
        unique_schedule = []
        seen_matchups = set()
        
        for h, a, type_ in schedule:
            # ID único do jogo independente do mando
            match_id = tuple(sorted([h.name, a.name])) 
            
            if type_ == "Divisional":
                # Divisional é ida e volta, permitimos 2 ocorrências do match_id
                # Mas precisamos garantir Home/Away. O loop acima já gera H/A e A/H explicitamente.
                # Apenas adicionamos.
                 unique_schedule.append((h, a, type_))
                 
            else:
                # Jogos de rodízio/posição são turno único
                if match_id not in seen_matchups:
                    seen_matchups.add(match_id)
                    unique_schedule.append((h, a, type_))
        
        return unique_schedule

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
    
    # 1. Resetar status
    for t in lnf_teams: t.reset_stats()
    
    # 2. Gerar Calendário Oficial (19 jogos)
    st.toast("Gerando calendário oficial de 19 jogos...")
    scheduler = LNFScheduler(lnf_teams, engine.season_year)
    schedule = scheduler.generate_schedule()
    
    # 3. Simular Partidas
    progress_bar = st.progress(0)
    total_games = len(schedule)
    
    for i, (home, away, match_type) in enumerate(schedule):
        # Simulação
        g_h, g_a = engine.simulate_match(home, away)
        
        # Atualizar tabela
        engine.update_table(home, away, g_h, g_a)
        
        # Atualizar barra de progresso
        if i % 10 == 0:
            progress_bar.progress((i + 1) / total_games)
            
    progress_bar.progress(100)
    st.toast("Temporada Regular LNF (19 Rodadas) Concluída!", icon="✅")
    
    # Debug: Verificar se todos jogaram 19 jogos
    # (Opcional - pode remover na versão final)
    with st.expander("Auditoria de Calendário (Debug)"):
        for t in lnf_teams:
            if t.games_played != 19:
                st.error(f"ERRO: {t.name} jogou {t.games_played} vezes!")
        st.write(f"Total de jogos processados: {total_games}")

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
