import streamlit as st
import pandas as pd
import numpy as np
import random
import copy
import json 
import os
from faker import Faker

# --- ASSETS E IMAGENS ---
# URLs de logos para os 32 times da LNF (Baseado na lista do PDF)
LOGO_URLS = {
    "Flamengo": "https://upload.wikimedia.org/wikipedia/commons/2/2e/Flamengo_braz_logo.svg",
    "Bahia": "https://upload.wikimedia.org/wikipedia/pt/2/2c/Esporte_Clube_Bahia_logo.png",
    "Atlético-MG": "https://upload.wikimedia.org/wikipedia/commons/2/27/Clube_Atl%C3%A9tico_Mineiro_logo.svg",
    "Athletico-PR": "https://upload.wikimedia.org/wikipedia/commons/c/cb/Club_Athletico_Paranaense_2019.svg",
    "Corinthians": "https://upload.wikimedia.org/wikipedia/pt/b/b4/Corinthians_simbolo.png",
    "Vitória": "https://upload.wikimedia.org/wikipedia/pt/8/80/Esporte_Clube_Vit%C3%B3ria_logo.png",
    "Cuiabá": "https://upload.wikimedia.org/wikipedia/pt/2/20/Cuiab%C3%A1EC2020.png",
    "Juventude": "https://upload.wikimedia.org/wikipedia/pt/8/87/EC_Juventude_logo.png",
    "Botafogo": "https://upload.wikimedia.org/wikipedia/commons/c/cb/Botafogo_de_Futebol_e_Regatas_logo.svg",
    "Ceará": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Cear%C3%A1_Sporting_Club_logo.svg/1200px-Cear%C3%A1_Sporting_Club_logo.svg.png",
    "Remo": "https://upload.wikimedia.org/wikipedia/commons/7/7f/Clube_do_Remo_logo.svg",
    "Chapecoense": "https://upload.wikimedia.org/wikipedia/commons/b/b2/Associa%C3%A7%C3%A3o_Chapecoense_de_Futebol_logo.svg",
    "Palmeiras": "https://upload.wikimedia.org/wikipedia/commons/1/10/Palmeiras_logo.svg",
    "Fortaleza": "https://upload.wikimedia.org/wikipedia/commons/4/42/Fortaleza_Esporte_Clube_logo.svg",
    "Ponte Preta": "https://upload.wikimedia.org/wikipedia/commons/6/64/Associa%C3%A7%C3%A3o_Atl%C3%A9tica_Ponte_Preta_logo.svg",
    "Paysandu": "https://upload.wikimedia.org/wikipedia/commons/2/23/Paysandu_Sport_Club_logo.svg",
    "São Paulo": "https://upload.wikimedia.org/wikipedia/commons/6/6f/Brasao_do_Sao_Paulo_Futebol_Clube.svg",
    "Grêmio": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7b/Gremio_logo.svg/1200px-Gremio_logo.svg.png",
    "Criciúma": "https://upload.wikimedia.org/wikipedia/commons/0/04/Criciuma_EC_logo.svg",
    "Atlético-GO": "https://upload.wikimedia.org/wikipedia/commons/d/d4/Atl%C3%A9tico_Goianiense_logo.svg",
    "Fluminense": "https://upload.wikimedia.org/wikipedia/commons/a/ad/Fluminense_FC_escudo.png",
    "Sport": "https://upload.wikimedia.org/wikipedia/pt/1/17/Sport_Club_do_Recife.png",
    "Guarani": "https://upload.wikimedia.org/wikipedia/commons/3/32/Guarani_Futebol_Clube_logo.svg",
    "Coritiba": "https://upload.wikimedia.org/wikipedia/commons/8/83/Coritiba_Foot_Ball_Club_logo.svg",
    "Internacional": "https://upload.wikimedia.org/wikipedia/commons/f/f1/Escudo_do_Sport_Club_Internacional.svg",
    "RB Bragantino": "https://upload.wikimedia.org/wikipedia/pt/9/94/Red_Bull_Bragantino.png",
    "Goiás": "https://upload.wikimedia.org/wikipedia/commons/4/49/Goi%C3%A1s_Esporte_Clube_logo.svg",
    "Avaí": "https://upload.wikimedia.org/wikipedia/commons/f/fe/Avai_FC_%2805-09-2017%29.svg",
    "Vasco": "https://upload.wikimedia.org/wikipedia/pt/a/ac/CRVascodaGama.png",
    "Cruzeiro": "https://upload.wikimedia.org/wikipedia/commons/b/bc/Cruzeiro_Esporte_Clube_%28logo%29.svg",
    "América-MG": "https://upload.wikimedia.org/wikipedia/commons/a/ac/Am%C3%A9rica_Mineiro_logo.svg",
    "Santos": "https://upload.wikimedia.org/wikipedia/commons/1/15/Santos_Logo.png"
}

# Fallback para times do College (Escudo Genérico da UniFUT)
GENERIC_LOGO = "https://cdn-icons-png.flaticon.com/512/18/18405.png" # Ícone de troféu simples

# Configuração da Página
st.set_page_config(page_title="UniFUT Simulação", layout="wide", page_icon="⚽")

# --- CLASSES ESTRUTURAIS ---

class Player:
    def __init__(self, name, position, age, overall, team_name):
        self.name = name
        self.position = position
        self.age = age
        self.overall = overall
        # Potencial: Jovens têm teto mais alto
        self.potential = overall + random.randint(5, 15) if age < 23 else overall + random.randint(0, 3)
        self.team_name = team_name
        
        # Economia
        self.contract_years = random.randint(1, 4)
        self.market_value = self._calculate_value()
        self.wage = self._calculate_wage()
        
        # Stats e Evolução
        self.goals = 0
        self.assists = 0
        self.matches = 0
        self.mvp_points = 0
        self.last_evolution = 0 # Armazena o ganho/perda da última temporada (Ex: +2, -1)

    def _calculate_value(self):
        base = self.overall ** 3.5
        age_factor = 1.0 if 22 <= self.age <= 32 else (1.5 if self.age < 22 else 0.6)
        return int(base * 0.5 * age_factor)

    def _calculate_wage(self):
        return int((self.overall ** 3) * 12)
    
    def reset_season_stats(self):
        self.goals = 0; self.assists = 0; self.matches = 0; self.mvp_points = 0

    def evolve(self):
        """
        Calcula a evolução do jogador baseado na temporada (RPG Engine).
        Retorna o valor da mudança (ex: +2, -1, 0).
        """
        growth = 0
        
        # 1. Fator Idade (Curva de Desenvolvimento)
        if self.age < 24:
            base_chance = 60 # Jovens tendem a crescer
        elif 24 <= self.age <= 30:
            base_chance = 20 # Auge (estabilidade)
        else:
            base_chance = -30 # Veteranos tendem a cair (Regressão)
            
        # 2. Fator Performance (XP)
        # Cada jogo soma pontos de chance. Gols somam mais.
        performance_xp = (self.matches * 2) + (self.goals * 3) + (self.assists * 2)
        
        # Bônus para quem joga muito
        if self.matches > 10: base_chance += 10
        if self.matches > 20: base_chance += 15
        
        # Bônus por desempenho excepcional
        if performance_xp > 50: base_chance += 20
        
        # 3. Fator Potencial
        # Se já atingiu o potencial, é muito difícil crescer mais
        if self.overall >= self.potential:
            base_chance -= 40
            
        # --- CÁLCULO FINAL (Rolagem de Dados) ---
        roll = random.randint(0, 100) + (base_chance / 2)
        
        if roll > 95: growth = 3      # Explosão (+3)
        elif roll > 80: growth = 2    # Ótima evolução (+2)
        elif roll > 50: growth = 1    # Evolução padrão (+1)
        elif roll < 20 and self.age > 30: growth = -1 # Regressão leve
        elif roll < 5 and self.age > 32: growth = -2  # Regressão forte
        
        # Aplicar
        self.overall += growth
        self.overall = max(40, min(99, self.overall)) # Limites (40-99)
        self.last_evolution = growth
        
        # Recalcular valor de mercado após evolução (Valorização/Desvalorização)
        self.market_value = self._calculate_value()
        
        return growth

    # Serialização Atualizada (Incluindo last_evolution)
    def to_dict(self):
        return {
            "name": self.name, "position": self.position, "age": self.age,
            "overall": self.overall, "potential": self.potential, "team_name": self.team_name,
            "goals": self.goals, "matches": self.matches, "contract_years": self.contract_years,
            "last_evolution": self.last_evolution
        }

    @classmethod
    def from_dict(cls, data):
        p = cls(data["name"], data["position"], data["age"], data["overall"], data["team_name"])
        p.potential = data.get("potential", p.overall)
        p.goals = data.get("goals", 0)
        p.matches = data.get("matches", 0)
        p.contract_years = data.get("contract_years", 1)
        p.last_evolution = data.get("last_evolution", 0)
        return p

class Team:
    def __init__(self, name, league, conference, division, rating):
        self.name = name
        self.league = league 
        self.conference = conference
        self.division = division 
        self.rating = rating 
        self.players = []
        self.logo = LOGO_URLS.get(name, GENERIC_LOGO)
        
        # Economia
        self.budget = 0
        self.payroll = 0
        self.revenue = 0
        self.salary_cap = 0
        
        # Stats
        self.wins = 0
        self.losses = 0
        self.draws = 0
        self.points = 0
        self.goals_for = 0
        self.goals_against = 0
        
    def update_financials(self):
        self.payroll = sum(p.wage for p in self.players)
    
    def reset_stats(self):
        self.wins = 0; self.losses = 0; self.draws = 0; self.points = 0
        self.goals_for = 0; self.goals_against = 0

    @property
    def goal_diff(self): return self.goals_for - self.goals_against
    @property
    def games_played(self): return self.wins + self.losses + self.draws

    # --- SERIALIZAÇÃO ---
    def to_dict(self):
        return {
            "name": self.name, "league": self.league, "conference": self.conference,
            "division": self.division, "rating": self.rating,
            "budget": self.budget, "salary_cap": self.salary_cap,
            "revenue": self.revenue,
            "players": [p.to_dict() for p in self.players]
        }

    @classmethod
    def from_dict(cls, data):
        t = cls(data["name"], data["league"], data["conference"], data["division"], data["rating"])
        t.budget = data.get("budget", 0)
        t.salary_cap = data.get("salary_cap", 0)
        t.revenue = data.get("revenue", 0)
        t.players = [Player.from_dict(p_data) for p_data in data.get("players", [])]
        t.update_financials()
        return t
        
    def update_financials(self):
        # Recalcula folha salarial baseada no elenco atual
        self.payroll = sum(p.wage for p in self.players)
    
    def reset_stats(self):
        self.wins = 0
        self.losses = 0
        self.draws = 0
        self.points = 0
        self.goals_for = 0
        self.goals_against = 0
        # Não resetamos dinheiro, pois acumula entre temporadas

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
        self.structure = self._build_structure()

    def _build_structure(self):
        struct = {}
        for t in self.teams:
            if t.conference not in struct: struct[t.conference] = {}
            if t.division not in struct[t.conference]: struct[t.conference][t.division] = []
            struct[t.conference][t.division].append(t)
        
        # Ordenar cada divisão por Rating (simulando seed para definir confrontos por posição)
        for conf in struct:
            for div in struct[conf]:
                struct[conf][div].sort(key=lambda x: x.rating, reverse=True)
        return struct

    def generate_schedule(self):
        schedule = []
        divs_order = ["Leste", "Oeste", "Norte", "Sul"]
        
        # MAPA DE RODÍZIO (PARES FIXOS)
        # Garante reciprocidade exata: Se 0 enfrenta 1, 1 enfrenta 0.
        # Índices: 0=Leste, 1=Oeste, 2=Norte, 3=Sul
        rotation_map = [
            {0:1, 1:0, 2:3, 3:2}, # Ano 1: Leste x Oeste / Norte x Sul
            {0:2, 2:0, 1:3, 3:1}, # Ano 2: Leste x Norte / Oeste x Sul
            {0:3, 3:0, 1:2, 2:1}  # Ano 3: Leste x Sul / Oeste x Norte
        ]
        
        # Offset diferente para Intra e Inter conferência para variar os oponentes
        intra_year_idx = self.year % 3
        inter_year_idx = (self.year + 1) % 3 
        
        intra_map = rotation_map[intra_year_idx]
        inter_map = rotation_map[inter_year_idx]

        for conf in self.structure:
            for div_name in divs_order:
                my_idx = divs_order.index(div_name)
                my_teams = self.structure[conf][div_name]
                
                # Definir divisões alvo baseadas nos mapas
                target_intra_idx = intra_map[my_idx]
                target_intra_div = divs_order[target_intra_idx]
                
                target_inter_idx = inter_map[my_idx]
                target_inter_div = divs_order[target_inter_idx]
                
                other_conf = "Nacional" if conf == "Brasileira" else "Brasileira"

                for i, t1 in enumerate(my_teams):
                    seed = i # 0 a 3 (ranking na divisão)
                    
                    # --- 1. DIVISIONAL (6 Jogos) ---
                    # Ida e Volta contra os 3 rivais da mesma divisão
                    for j, t2 in enumerate(my_teams):
                        if t1 == t2: continue
                        # Adicionamos aqui apenas o jogo onde t1 é mandante
                        # O loop quando chegar em t2 adicionará a volta
                        schedule.append((t1, t2, "Divisional"))

                    # --- 2. INTRA-CONFERÊNCIA RODÍZIO (4 Jogos) ---
                    # Contra todos da divisão alvo (Leste x Oeste)
                    target_teams = self.structure[conf][target_intra_div]
                    for t2 in target_teams:
                        schedule.append((t1, t2, "Intra-Rot"))

                    # --- 3. INTER-CONFERÊNCIA RODÍZIO (4 Jogos) ---
                    # Contra todos da divisão alvo da outra conferência
                    target_teams_inter = self.structure[other_conf][target_inter_div]
                    for t2 in target_teams_inter:
                        schedule.append((t1, t2, "Inter-Rot"))
                        
                    # --- 4. INTRA-POSIÇÃO (2 Jogos) ---
                    # Contra mesmo seed das 2 divisões que sobraram na minha conferência
                    for other_div_name in divs_order:
                        if other_div_name == div_name: continue # Minha divisão
                        if other_div_name == target_intra_div: continue # Já joguei no rodízio
                        
                        rival = self.structure[conf][other_div_name][seed]
                        schedule.append((t1, rival, "Intra-Pos"))
                        
                    # --- 5. INTER-POSIÇÃO (3 Jogos) ---
                    # Contra mesmo seed das 3 divisões que sobraram na outra conferência
                    for other_div_name in divs_order:
                        if other_div_name == target_inter_div: continue # Já joguei no rodízio
                        
                        rival = self.structure[other_conf][other_div_name][seed]
                        schedule.append((t1, rival, "Inter-Pos"))

        # --- LIMPEZA E DEDUPLICAÇÃO ---
        # Como o loop roda para todos os times, jogos de turno único (Rotação/Posição)
        # são gerados duas vezes (A gera contra B, depois B gera contra A).
        # Vamos remover as duplicatas mantendo apenas uma ocorrência.
        
        unique_schedule = []
        seen = set()
        
        for h, a, type_ in schedule:
            if h.name == a.name: continue
            
            if type_ == "Divisional":
                # Divisional é ida e volta explícita, aceitamos todas as ocorrências geradas
                # (O loop acima gera A x B e depois B x A, ambos são válidos)
                unique_schedule.append((h, a, type_))
            else:
                # Jogos de turno único: Dedupicar usando ID ordenado
                match_id = tuple(sorted([h.name, a.name]))
                if match_id not in seen:
                    seen.add(match_id)
                    # Sorteia mando para não viciar
                    if random.choice([True, False]):
                        unique_schedule.append((h, a, type_))
                    else:
                        unique_schedule.append((a, h, type_))
                        
        return unique_schedule

class UniFUTEngine:
    def __init__(self):
        self.teams = []
        self.season_year = 2026
        self.fake = Faker('pt_BR') # Inicializa gerador de nomes BR
        
    def add_team(self, team):
        self.teams.append(team)
        
    def get_teams_by_league(self, league):
        # Filtro flexível (ex: 'College' pega College 1 e 2)
        if league == 'College':
            return [t for t in self.teams if 'College' in t.league]
        return [t for t in self.teams if t.league == league]

    def simulate_match(self, team_a, team_b, is_knockout=False, return_events=False):
        home_advantage = 5
        diff = (team_a.rating + home_advantage) - team_b.rating
        prob_a = 1 / (1 + 10 ** (-diff / 400))
        
        avg_goals = 2.5
        goals_a = np.random.poisson(avg_goals * (prob_a + 0.1))
        goals_b = np.random.poisson(avg_goals * ((1 - prob_a) + 0.1))
        
        match_events = []
        
        # --- ATRIBUIÇÃO DE GOLS E STATS ---
        scorers_a = self._assign_goals(team_a, goals_a)
        scorers_b = self._assign_goals(team_b, goals_b)
        
        # Registrar estatísticas nos jogadores
        for p in scorers_a: p.goals += 1
        for p in scorers_b: p.goals += 1
        
        # Incrementar partidas jogadas (titulares fictícios)
        # Simplificação: Todos do elenco ganham +1 jogo? Não, vamos pegar 11 aleatórios
        for t in [team_a, team_b]:
            starters = random.sample(t.players, min(11, len(t.players)))
            for p in starters: p.matches += 1

        # NARRATIVA (Atualizada com nomes dos artilheiros)
        if return_events:
            match_events.append(f"📢 INÍCIO: {team_a.name} vs {team_b.name}")
            
            # Misturar gols de A e B para cronologia
            timeline = []
            for p in scorers_a: timeline.append((random.randint(1,90), team_a.name, p.name))
            for p in scorers_b: timeline.append((random.randint(1,90), team_b.name, p.name))
            timeline.sort(key=lambda x: x[0])
            
            current_time = 0
            for m, team_name, player_name in timeline:
                match_events.append(f"⚽ **{m}' GOL do {team_name}!** Marcou: {player_name}")
            
            match_events.append(f"⏱️ FIM: {team_a.name} {goals_a} x {goals_b} {team_b.name}")

        if is_knockout and goals_a == goals_b:
            winner = random.choice([team_a, team_b])
            if winner == team_a: goals_a += 1
            else: goals_b += 1
            if return_events: match_events.append(f"✅ {winner.name} vence na prorrogação/pênaltis!")
            
        if return_events: return goals_a, goals_b, match_events
        return goals_a, goals_b

    def _assign_goals(self, team, num_goals):
        """Retorna lista de objetos Player que fizeram os gols"""
        if num_goals == 0 or not team.players: return []
        
        # Pesos por posição: ATA(10), MID(3), DEF(1), GK(0.1)
        weights = []
        for p in team.players:
            if p.position == "ATA": w = 10
            elif p.position == "MID": w = 3
            elif p.position == "DEF": w = 1
            else: w = 0.1
            weights.append(w)
            
        return random.choices(team.players, weights=weights, k=num_goals)
    
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

    def generate_rosters(self):
        positions = ["GK", "DEF", "MID", "ATA"]
        
        for team in self.teams:
            # Se já tem jogadores, não gera de novo
            if len(team.players) > 0: continue
            
            # Gerar 25 jogadores por time
            for _ in range(25):
                pos = random.choice(positions)
                
                # Idade: LNF mais velha, College mais jovem
                if team.league == 'LNF':
                    age = random.randint(18, 36)
                    # Rating baseado na força do time + variação
                    ovr = int(np.random.normal(team.rating, 3))
                else:
                    age = random.randint(16, 23) # College focado em base
                    # College tem jogadores um pouco piores que o rating do time
                    # para simular potencial de evolução
                    ovr = int(np.random.normal(team.rating - 2, 4))
                
                # Limites (0-99)
                ovr = max(40, min(99, ovr))
                
                player = Player(self.fake.name_male(), pos, age, ovr, team.name)
                team.players.append(player)
            
            # Ordenar elenco por Overall
            team.players.sort(key=lambda x: x.overall, reverse=True)
            
    # --- MÉTODOS DE MATA-MATA (SPRINT D) ---

    def simulate_knockout_stage(self, teams, round_name):
        """Simula uma rodada de mata-mata e retorna os vencedores e os resultados."""
        winners = []
        results = []
        
        # Embaralhar para sorteio (exceto se já vier ordenado por chaveamento)
        # Aqui assumimos sorteio puro para simplificar o MVP
        random.shuffle(teams)
        
        # Garantir número par
        if len(teams) % 2 != 0:
            bye_team = teams.pop()
            winners.append(bye_team)
            results.append(f"{bye_team.name} avançou (Bye)")
            
        for i in range(0, len(teams), 2):
            t1 = teams[i]
            t2 = teams[i+1]
            
            # Simula jogo único (com pênaltis se empatar)
            g1, g2 = self.simulate_match(t1, t2, is_knockout=True)
            
            winner = t1 if g1 > g2 else t2
            winners.append(winner)
            results.append(f"{t1.name} {g1} x {g2} {t2.name}")
            
        return winners, results

    def run_copa_brasil(self):
        """
        Simulação da Copa do Brasil conforme Manual (Página 45/46):
        - Fase 1: College 2 (Piores)
        - Fase 2: Vencedores F1 + College 1 + Resto College 2
        - Fase 3: Vencedores F2 + LNF (Exceto Seeds)
        - Fase 4 (Oitavas): Vencedores F3 + Seeds LNF (Top 8)
        """
        log = {}
        
        # 1. Seleção dos Times
        college2 = self.get_teams_by_league("College 2")
        college1 = self.get_teams_by_league("College 1")
        lnf = self.get_teams_by_league("LNF")
        
        # LNF Seeds (Top 8 campanha anterior/rating) -> Entram na Fase 4
        lnf_sorted = sorted(lnf, key=lambda x: x.rating, reverse=True)
        lnf_seeds = lnf_sorted[:8]
        lnf_normal = lnf_sorted[8:]
        
        # FASE 1: Preliminar (Apenas 64 times do College 2 jogam para afunilar)
        f1_teams = college2[:64] 
        f1_winners, f1_res = self.simulate_knockout_stage(f1_teams, "Fase 1")
        log["Fase 1 (Preliminar College)"] = f1_res
        
        # FASE 2: Mistura Geral (Vencedores F1 + Resto College 2 + College 1)
        # Total esperado: 32 (vencedores F1) + 32 (resto C2) + 96 (C1) = 160 times -> 80 jogos
        # Simplificação MVP: Vamos pegar 64 times aleatórios dessa mistura para avançar
        pool_f2 = f1_winners + college2[64:] + college1
        f2_teams = random.sample(pool_f2, 64) # Força bruta para caber na chave
        f2_winners, f2_res = self.simulate_knockout_stage(f2_teams, "Fase 2")
        log["Fase 2 (Geral College)"] = f2_res
        
        # FASE 3: Entrada da LNF (32 Vencedores F2 + 24 LNF Normal = 56 times? Ajuste matemático necessário)
        # Ajuste para chave perfeita de Oitavas (precisamos de 8 vencedores na Fase 3 para somar aos 8 seeds = 16)
        # Então Fase 3 precisa de 16 times (8 jogos).
        # Vamos pegar os 8 melhores da Fase 2 e colocar contra 8 da LNF Normal
        f3_teams = f2_winners[:8] + lnf_normal[:8]
        f3_winners, f3_res = self.simulate_knockout_stage(f3_teams, "Fase 3")
        log["Fase 3 (Entrada LNF)"] = f3_res
        
        # FASE 4: OITAVAS DE FINAL (8 Vencedores F3 + 8 Seeds LNF)
        last_16 = f3_winners + lnf_seeds
        
        # Mata-mata até o fim
        stages = ["Oitavas de Final", "Quartas de Final", "Semifinal", "Grande Final"]
        current_teams = last_16
        
        for stage in stages:
            winners, res = self.simulate_knockout_stage(current_teams, stage)
            log[stage] = res
            current_teams = winners
            
        return log, current_teams[0] # Retorna log e campeão

    def run_regional_bowls(self):
        """
        Simula os Bowls Regionais (Campeões de Conferência se enfrentam)
        Manual Página 34/105 - Rotação Regional
        """
        college_teams = self.get_teams_by_league("College") # Pega todos (1 e 2)
        
        # Agrupar por conferência e pegar o melhor rating de cada
        confs = {}
        for t in college_teams:
            if t.division not in confs: confs[t.division] = []
            confs[t.division].append(t)
            
        champions = {}
        for conf_name, teams in confs.items():
            # Em uma simulação completa, seria o campeão da tabela. 
            # Aqui usamos o Rating/Sorte como proxy
            champions[conf_name] = sorted(teams, key=lambda x: x.rating, reverse=True)[0]
            
        # Definir confrontos (Rotação fixa conforme manual)
        # Ex: Amazônica x Nordeste, Sul x Sudeste...
        matchups = [
            ("Amazônica", "Nordeste Atlântico", "North Star Bowl"),
            ("Nordeste Sul", "Centro-Oeste", "Caldeirão Bowl"),
            ("Sudeste Norte", "Paulista", "Coffee Bowl"),
            ("Sudeste Sul", "Sul", "Oceanic Bowl")
        ]
        
        results = []
        for c1, c2, bowl_name in matchups:
            t1 = champions.get(c1)
            t2 = champions.get(c2)
            if t1 and t2:
                g1, g2 = self.simulate_match(t1, t2, is_knockout=True)
                winner = t1.name if g1 > g2 else t2.name
                results.append({
                    "Bowl": bowl_name,
                    "Confronto": f"{c1} vs {c2}",
                    "Placar": f"{t1.name} {g1} x {g2} {t2.name}",
                    "Campeão": winner
                })
                
        return results

    def run_ncp(self):
        """
        Simula o National College Playoff (NCP) - Manual Seção 6
        Formato de 12 Times:
        - Seeds 1-4: Bye (Folgam na Rodada 1)
        - Rodada 1: 5x12, 6x11, 7x10, 8x9
        - Quartas: Vencedores x Seeds 1-4
        """
        log = []
        
        # 1. Selecionar os Top 12 do Ranking Nacional (College)
        # Como critério de MVP, usamos o Rating como proxy do Ranking
        college_teams = self.get_teams_by_league("College")
        ranked_teams = sorted(college_teams, key=lambda x: x.rating, reverse=True)
        top12 = ranked_teams[:12]
        
        # Seeds
        seeds_1_4 = top12[:4]  # Folgam
        seeds_5_12 = top12[4:] # Jogam Rodada 1
        
        log.append(f"🌟 **Top 4 (Bye nas Quartas):** {', '.join([t.name for t in seeds_1_4])}")
        
        # --- RODADA 1 (First Round) ---
        # Confrontos: 5x12, 6x11, 7x10, 8x9
        # Índice 0 é seed 5, Índice 7 é seed 12
        matchups_r1 = [
            (seeds_5_12[0], seeds_5_12[7]), # 5 vs 12
            (seeds_5_12[1], seeds_5_12[6]), # 6 vs 11
            (seeds_5_12[2], seeds_5_12[5]), # 7 vs 10
            (seeds_5_12[3], seeds_5_12[4]), # 8 vs 9
        ]
        
        winners_r1 = []
        log.append("--- 🏁 RODADA 1 (Wild Card College) ---")
        
        for t1, t2 in matchups_r1:
            g1, g2 = self.simulate_match(t1, t2, is_knockout=True)
            winner = t1 if g1 > g2 else t2
            winners_r1.append(winner)
            log.append(f"Seed {top12.index(t1)+1} {t1.name} {g1} x {g2} {t2.name} Seed {top12.index(t2)+1}")
            
        # --- QUARTAS DE FINAL ---
        # Vencedores da R1 enfrentam os Seeds 1-4
        # Para simplificar o chaveamento dinâmico, vamos fazer emparelhamento direto:
        # Seed 1 x Pior Seed Restante (no MVP, simplificamos para ordem da lista)
        
        # Inverter winners para que o "pior" enfrente o seed 1? 
        # Vamos parear direto: Seed 1 x Vencedor do Jogo 8v9 (que é o matchup 3 da lista winners_r1 invertida)
        # Matchups fixos do Bracket padrão:
        # Q1: Seed 1 vs Vencedor (8x9)
        # Q2: Seed 2 vs Vencedor (7x10)
        # Q3: Seed 3 vs Vencedor (6x11)
        # Q4: Seed 4 vs Vencedor (5x12)
        
        matchups_q = [
            (seeds_1_4[0], winners_r1[3]), # 1 vs (8x9)
            (seeds_1_4[1], winners_r1[2]), # 2 vs (7x10)
            (seeds_1_4[2], winners_r1[1]), # 3 vs (6x11)
            (seeds_1_4[3], winners_r1[0]), # 4 vs (5x12)
        ]
        
        winners_q = []
        log.append("--- 🥣 QUARTAS DE FINAL (Bowls Temáticos) ---")
        
        bowl_names = ["Heritage Bowl", "Prime Bowl", "Leadership Bowl", "New Horizons Bowl"]
        
        for i, (t1, t2) in enumerate(matchups_q):
            g1, g2 = self.simulate_match(t1, t2, is_knockout=True)
            winner = t1 if g1 > g2 else t2
            winners_q.append(winner)
            log.append(f"**{bowl_names[i]}**: {t1.name} {g1} x {g2} {t2.name}")

        # --- SEMIFINAIS ---
        # Q1 vs Q4 / Q2 vs Q3
        matchups_s = [
            (winners_q[0], winners_q[3]),
            (winners_q[1], winners_q[2])
        ]
        
        winners_s = []
        log.append("--- 🏆 SEMIFINAIS NACIONAIS ---")
        
        for t1, t2 in matchups_s:
            g1, g2 = self.simulate_match(t1, t2, is_knockout=True)
            winner = t1 if g1 > g2 else t2
            winners_s.append(winner)
            log.append(f"{t1.name} {g1} x {g2} {t2.name}")
            
        # --- FINAL NACIONAL ---
        log.append("--- 🎆 NATIONAL CHAMPIONSHIP GAME ---")
        f1, f2 = winners_s[0], winners_s[1]
        g1, g2 = self.simulate_match(f1, f2, is_knockout=True)
        champion = f1 if g1 > g2 else f2
        
        log.append(f"RESULTADO FINAL: {f1.name} {g1} x {g2} {f2.name}")
        
        return log, champion

    # --- MÉTODOS ECONÔMICOS (SPRINT 2.0) ---

    def initialize_economy(self):
        """Define orçamentos iniciais baseados no Manual (Seção 11/23)"""
        for team in self.teams:
            team.update_financials() # Calcular folha inicial
            
            if team.league == "LNF":
                # LNF: Teto R$ 350M. Orçamento inicial robusto.
                team.salary_cap = 350_000_000
                team.budget = random.randint(300_000_000, 500_000_000)
            
            elif "College 1" in team.league:
                # College 1: Teto R$ 40M.
                team.salary_cap = 40_000_000
                team.budget = random.randint(25_000_000, 45_000_000)
            
            else:
                # College 2: Teto R$ 15M.
                team.salary_cap = 15_000_000
                team.budget = random.randint(5_000_000, 15_000_000)

    def distribute_tv_rights(self):
        """
        Distribuição de Receitas LNF (Regra 50/25/25) - Manual Pg. 223
        Exemplo de Pool: R$ 2.5 Bilhões
        """
        total_pool = 2_500_000_000
        lnf_teams = self.get_teams_by_league("LNF")
        
        # 1. Cota Igualitária (50%)
        equal_share = (total_pool * 0.50) / len(lnf_teams)
        
        # 2. Cota Performance (25%) - Baseada em Pontos
        total_points = sum(t.points for t in lnf_teams)
        perf_pot = total_pool * 0.25
        
        # 3. Cota Audiência/Mercado (25%) - Baseada em Rating (Proxy de torcida)
        total_rating = sum(t.rating for t in lnf_teams)
        audience_pot = total_pool * 0.25
        
        for team in lnf_teams:
            # Calcular
            share_perf = (team.points / total_points) * perf_pot if total_points > 0 else 0
            share_aud = (team.rating / total_rating) * audience_pot
            
            total_revenue = equal_share + share_perf + share_aud
            
            # Aplicar
            team.revenue += total_revenue
            team.budget += total_revenue
            
            # Subtrair Folha Salarial (Custo Anual)
            team.budget -= team.payroll

    def process_draft_payment(self, lnf_team, college_team_name, round_num):
        """
        Transferência de dinheiro no Draft (Manual Seção 10.9)
        """
        # Tabela de Preços
        prices = {
            1: 1_000_000, 2: 600_000, 3: 350_000,
            4: 200_000, 5: 100_000, 6: 50_000, 7: 25_000
        }
        fee = prices.get(round_num, 0)
        
        # LNF Paga
        lnf_team.budget -= fee
        
        # College Recebe (busca o time pelo nome)
        # Otimização: buscar em dicionário seria melhor, aqui varre lista (MVP)
        for t in self.teams:
            if t.name == college_team_name:
                t.budget += fee
                t.revenue += fee # Conta como receita
                break

    def advance_season(self, champion_lnf, champion_ncp):
        """
        Realiza a virada de ano com Evolução Dinâmica (Sprint 7.0)
        """
        # 1. Salvar Histórico
        top_scorer_lnf = self.get_top_scorer("LNF")
        mvp = top_scorer_lnf # Simplificação
        
        self.history.append({
            "Ano": self.season_year,
            "LNF Campeão": champion_lnf.name,
            "College Campeão": champion_ncp.name,
            "Artilheiro LNF": f"{top_scorer_lnf.name} ({top_scorer_lnf.goals} gols)",
            "MVP": mvp.name
        })
        
        # 2. Ciclo de Vida e Evolução (RPG)
        retired_count = 0
        evolution_log = {"up": 0, "down": 0, "stable": 0}
        
        for team in self.teams:
            new_roster = []
            for p in team.players:
                # --- EVOLUÇÃO DINÂMICA ---
                growth = p.evolve() # Calcula ganho baseado na temporada atual
                
                if growth > 0: evolution_log["up"] += 1
                elif growth < 0: evolution_log["down"] += 1
                else: evolution_log["stable"] += 1
                
                # Envelhecimento
                p.age += 1
                p.reset_season_stats() # Zera gols PARA O PRÓXIMO ANO
                
                # Aposentadoria
                chance_retire = (p.age - 32) * 10 if p.age > 32 else 0
                if random.randint(0, 100) < chance_retire:
                    retired_count += 1
                    # Regen (Reposição da Base)
                    pos = p.position
                    ovr = random.randint(50, 70)
                    new_p = Player(self.fake.name_male(), pos, random.randint(16, 19), ovr, team.name)
                    new_p.name += " (Jr)"
                    new_p.last_evolution = 0 # Novo, sem histórico
                    new_roster.append(new_p)
                else:
                    new_roster.append(p)
            
            team.players = new_roster
            team.reset_stats() # Zera pontos na tabela
            team.revenue = 0 # Zera receita do ano (novo orçamento)
            
        # 3. Atualizar Ano
        self.season_year += 1
        
        return f"Temporada {self.season_year} Iniciada! 📈 {evolution_log['up']} evoluíram, 📉 {evolution_log['down']} regrediram. 🚪 {retired_count} aposentadorias."

    def get_top_scorer(self, league_filter=None):
        all_players = []
        teams = self.get_teams_by_league(league_filter) if league_filter else self.teams
        for t in teams: all_players.extend(t.players)
        
        if not all_players: return None
        return sorted(all_players, key=lambda x: x.goals, reverse=True)[0]

    # ... (Métodos anteriores da engine continuam iguais) ...

    # --- MÉTODOS DE SAVE/LOAD (SPRINT 5.0) ---
    def to_json(self):
        """Exporta o estado completo do jogo para um dicionário JSON"""
        return json.dumps({
            "season_year": self.season_year,
            "history": self.history,
            "teams": [t.to_dict() for t in self.teams]
        }, indent=4)

    @classmethod
    def load_from_json(cls, json_str):
        """Reconstroi a Engine a partir de uma string JSON"""
        data = json.loads(json_str)
        
        new_engine = cls()
        new_engine.season_year = data["season_year"]
        new_engine.history = data.get("history", [])
        
        # Reconstruir times e jogadores
        new_engine.teams = []
        for t_data in data["teams"]:
            new_engine.add_team(Team.from_dict(t_data))
            
        return new_engine

    # --- AI GM & MERCADO (SPRINT 6.0) ---

    def run_transfer_window(self):
        """
        Simula uma Janela de Transferências completa.
        1. Renovações de contrato.
        2. Free Agency (Sem contrato).
        3. Compras e Vendas entre clubes.
        """
        transfer_log = []
        
        # 1. Processar Contratos (Fim de ano)
        free_agents = []
        for t in self.teams:
            new_roster = []
            for p in t.players:
                p.contract_years -= 1
                if p.contract_years <= 0:
                    # Tenta renovar? (Simplificação: Se titular e time tem dinheiro, renova)
                    cost_renew = p.wage * 1.2 # Aumento salarial
                    if t.budget > cost_renew * 2 and p.overall > (t.rating - 5):
                        p.contract_years = random.randint(2, 4)
                        p.wage = int(cost_renew)
                        new_roster.append(p)
                    else:
                        # Dispensa (Vira Free Agent)
                        p.team_name = "Free Agent"
                        free_agents.append(p)
                else:
                    new_roster.append(p)
            t.players = new_roster

        # 2. Mercado Ativo (LNF comprando)
        lnf_teams = self.get_teams_by_league("LNF")
        random.shuffle(lnf_teams) # Ordem aleatória de negociação
        
        for buyer in lnf_teams:
            # Lógica do GM: Onde sou fraco?
            # Analisar média por posição
            weakest_pos = self._analyze_weakness(buyer)
            if not weakest_pos: continue
            
            # Definir Orçamento para Transferência (30% do caixa atual)
            budget_avail = buyer.budget * 0.30
            
            # Buscar Alvo no Mercado (College ou LNF)
            target = self._scout_player(weakest_pos, buyer.rating, budget_avail)
            
            if target:
                # Executar Transferência
                seller = self._find_team_by_name(target.team_name)
                if seller:
                    transfer_value = int(target.market_value * 1.2) # Ágio de mercado
                    
                    # Transação
                    if buyer.budget >= transfer_value:
                        # Pagar
                        buyer.budget -= transfer_value
                        seller.budget += transfer_value
                        seller.revenue += transfer_value # Receita pro vendedor
                        
                        # Mover Jogador
                        seller.players.remove(target)
                        target.team_name = buyer.name
                        target.contract_years = random.randint(3, 5)
                        target.wage = int(target.wage * 1.5) # Aumento pro jogador ir
                        buyer.players.append(target)
                        
                        # Log
                        transfer_log.append({
                            "Comprador": buyer.name,
                            "Vendedor": seller.name,
                            "Jogador": f"{target.name} ({target.position} {target.overall})",
                            "Valor": f"R$ {transfer_value/1e6:.1f}M"
                        })

        # 3. Assinar Free Agents (Times preenchem buracos de graça)
        for fa in free_agents:
            # Tenta achar um time qualquer que aceite
            potential_teams = random.sample(self.teams, 5)
            for t in potential_teams:
                if len(t.players) < 28: # Limite de elenco
                    fa.team_name = t.name
                    fa.contract_years = 2
                    t.players.append(fa)
                    break # Achou casa

        return transfer_log

    def _analyze_weakness(self, team):
        """Retorna a posição onde o time tem a pior média de titulares"""
        positions = {"GK": [], "DEF": [], "MID": [], "ATA": []}
        for p in team.players:
            positions[p.position].append(p.overall)
        
        # Calcular médias dos titulares (Top 1 GK, Top 4 DEF, etc)
        avgs = {}
        if positions["GK"]: avgs["GK"] = max(positions["GK"])
        else: avgs["GK"] = 0
        
        if len(positions["DEF"]) >= 4: avgs["DEF"] = np.mean(sorted(positions["DEF"], reverse=True)[:4])
        else: avgs["DEF"] = 0
        
        if len(positions["MID"]) >= 3: avgs["MID"] = np.mean(sorted(positions["MID"], reverse=True)[:3])
        else: avgs["MID"] = 0
        
        if len(positions["ATA"]) >= 3: avgs["ATA"] = np.mean(sorted(positions["ATA"], reverse=True)[:3])
        else: avgs["ATA"] = 0
        
        # Retorna a chave com menor valor
        return min(avgs, key=avgs.get)

    def _scout_player(self, position, min_rating, max_price):
        """Procura um jogador no universo que seja melhor que o time atual e caiba no bolso"""
        candidates = []
        # Otimização: Olhar apenas 20 times aleatórios para não travar o loop
        scouted_teams = random.sample(self.teams, 20)
        
        for t in scouted_teams:
            for p in t.players:
                if p.position == position and p.overall > min_rating and p.market_value <= max_price:
                    candidates.append(p)
        
        if candidates:
            # Retorna o melhor candidato encontrado
            return sorted(candidates, key=lambda x: x.overall, reverse=True)[0]
        return None

    def _find_team_by_name(self, name):
        for t in self.teams:
            if t.name == name: return t
        return None

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
    
    engine.generate_rosters()

    engine.initialize_economy()

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
            "Logo": t.logo, # <--- NOVA COLUNA
            "Time": t.name,
            "Conf": t.conference if t.league == 'LNF' else t.division,
            "Div": t.division if t.league == 'LNF' else '-',
            "Pts": t.points,
            "V": t.wins,
            "E": t.draws,
            "D": t.losses,
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

if not hasattr(engine, 'history'):
    engine.history = []

# Sidebar
st.sidebar.header("Controle de Simulação")
# --- SIDEBAR: SISTEMA DE ARQUIVOS ---
st.sidebar.header("💾 Sistema")

# 1. Botão de Download (Salvar)
# Prepara o arquivo na memória
save_data = engine.to_json()
st.sidebar.download_button(
    label="📥 Salvar Jogo (Download .json)",
    data=save_data,
    file_name=f"save_unifut_{engine.season_year}.json",
    mime="application/json",
    help="Baixe o arquivo para continuar depois."
)

# 2. Botão de Upload (Carregar)
uploaded_file = st.sidebar.file_uploader("📤 Carregar Jogo", type=["json"])

if uploaded_file is not None:
    try:
        # Ler o arquivo
        json_str = uploaded_file.getvalue().decode("utf-8")
        
        # Botão de confirmação para não carregar acidentalmente
        if st.sidebar.button("Confirmar Carregamento"):
            # Recriar a engine com os dados do arquivo
            st.session_state.engine = UniFUTEngine.load_from_json(json_str)
            st.session_state.simulated_lnf = False # Resetar estado da UI
            st.success("Jogo carregado com sucesso! A página irá recarregar.")
            st.rerun()
            
    except Exception as e:
        st.sidebar.error(f"Erro ao carregar arquivo: {e}")

st.sidebar.divider()
# ... (continua o resto da sidebar original) ...
season_year = st.sidebar.number_input("Ano da Temporada", value=2026)

if st.sidebar.button("Simular Temporada Regular LNF"):
    run_lnf_regular_season(engine)
    st.session_state.simulated_lnf = True


# Abas Principais
tab_lnf, tab_college, tab_copas, tab_draft, tab_finance, tab_clubs, tab_history, tab_market = st.tabs(["LNF (Elite)", "College (Base)", "Copas & Bowls", "Draft", "💰 Finanças", "Clubes", "Histórico", "Mercado"])

with tab_lnf:
    st.header(f"Liga Nacional de Futebol - {season_year}")
    
    if st.session_state.simulated_lnf:
        column_config = {
            "Logo": st.column_config.ImageColumn("Escudo", width="small"),
            "Time": st.column_config.TextColumn("Clube", width="medium"),
            "Pts": st.column_config.ProgressColumn("Pontos", format="%d", min_value=0, max_value=60),
        }

        # Exibir tabelas por Conferência
        lnf_teams = engine.get_teams_by_league("LNF")
        df = get_standings_df(lnf_teams)
        
        st.subheader("Classificação Oficial LNF")
        
        tab_br, tab_nac = st.tabs(["Conferência Brasileira", "Conferência Nacional"])
        
        with tab_br:
            df_br = df[df["Conf"] == "Brasileira"].drop(columns=["Conf"])
            st.dataframe(df_br, column_config=column_config, hide_index=True, use_container_width=True)
            
        with tab_nac:
            df_nac = df[df["Conf"] == "Nacional"].drop(columns=["Conf"])
            st.dataframe(df_nac, column_config=column_config, hide_index=True, use_container_width=True)
            
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
    st.header("Ecossistema de Copas & Bowls 2026")
    
    # Agora com 3 colunas!
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("🏆 Copa do Brasil")
        st.caption("CBF (LNF + College + Qualy)")
        if st.button("Simular Copa do Brasil"):
            if not st.session_state.simulated_lnf:
                st.error("Simule a LNF primeiro!")
            else:
                with st.spinner("Processando..."):
                    log_cdb, campeao_cdb = engine.run_copa_brasil()
                st.success(f"CAMPEÃO: {campeao_cdb.name}")
                with st.expander("Detalhes"):
                    for fase, jogos in log_cdb.items():
                        st.write(f"**{fase}**")
                        for jogo in jogos: st.text(jogo)
    
    with col2:
        st.subheader("🥣 Bowls Regionais")
        st.caption("Campeões de Conferência")
        if st.button("Simular Bowls"):
            bowls_res = engine.run_regional_bowls()
            for bowl in bowls_res:
                with st.expander(f"{bowl['Bowl']} ({bowl['Campeão']})"):
                    st.write(f"{bowl['Confronto']}")
                    st.write(f"Placar: {bowl['Placar']}")

    with col3:
        st.subheader("🥇 National Playoff")
        st.caption("Top 12 College (NCP)")
        st.markdown("O ápice da temporada universitária.")
        
        if st.button("Simular NCP"):
            with st.spinner("Definindo o Campeão Nacional..."):
                log_ncp, campeao_ncp = engine.run_ncp()
            
            st.balloons() # Efeito visual de festa!
            st.success(f"CAMPEÃO NACIONAL: {campeao_ncp.name}")
            
            for item in log_ncp:
                if "---" in item or "Top 4" in item:
                    st.markdown(f"**{item}**")
                else:
                    st.write(item)

with tab_draft:
    st.header("Draft UniFUT 2026")
    st.markdown("""
    O Draft ocorre em **7 Rodadas**. A ordem é inversa à classificação da LNF.
    Os jogadores são selecionados do sistema **College** (College 1 e 2).
    """)
    
    if st.session_state.simulated_lnf:
        # 1. Definir Ordem do Draft (Pior -> Melhor campanha LNF)
        lnf_teams = engine.get_teams_by_league("LNF")
        # Critério: Menos pontos primeiro. Desempate: Menor saldo.
        draft_order = sorted(lnf_teams, key=lambda x: (x.points, x.goal_diff))
        
        # 2. Listar Prospectos (Jogadores do College)
        college_teams = engine.get_teams_by_league("College")
        all_prospects = []
        for t in college_teams:
            all_prospects.extend(t.players)
        
        # Ordenar prospectos por Overall (Melhores disponíveis)
        all_prospects.sort(key=lambda x: x.overall, reverse=True)
        
        # UI: Mostrar Top Prospectos
        st.subheader("Top 5 Prospectos Disponíveis (Big Board)")
        top_prospects = all_prospects[:5]
        df_prospects = pd.DataFrame([{
            "Nome": p.name, "Pos": p.position, 
            "Idade": p.age, "Overall": p.overall, 
            "Origem": p.team_name
        } for p in top_prospects])
        st.table(df_prospects)
        
        # Botão para Realizar o Draft
        if st.button("Realizar Draft Completo (7 Rodadas)"):
            draft_results = []
            
            # Simulação do Draft
            prospect_index = 0
            for round_num in range(1, 8):
                for team in draft_order:
                    # Time pega o melhor jogador disponível
                    pick = all_prospects[prospect_index]

                    engine.process_draft_payment(team, pick.team_name, round_num)
                    # Transferência Lógica
                    # Remover do time antigo (College) e adicionar no novo (LNF) - Simplificado
                    pick.team_name = team.name # Atualiza a camisa
                    team.players.append(pick)
                    
                    draft_results.append({
                        "Rodada": round_num,
                        "Time LNF": team.name,
                        "Jogador Escolhido": pick.name,
                        "Pos": pick.position,
                        "Overall": pick.overall,
                        "Veio de": all_prospects[prospect_index].team_name # Hack para mostrar origem antiga
                    })
                    
                    prospect_index += 1
            
            st.success("Draft Concluído com Sucesso!")
            st.dataframe(pd.DataFrame(draft_results), height=500)
            
    else:
        st.warning("⚠️ Você precisa simular a Temporada Regular da LNF primeiro para definir a ordem das escolhas.")

with tab_finance:
    st.header("Painel Financeiro & Fair Play")
    
    # Métricas Gerais
    lnf_teams = engine.get_teams_by_league("LNF")
    avg_payroll = np.mean([t.payroll for t in lnf_teams])
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Teto Salarial LNF", "R$ 350.0M")
    m2.metric("Média de Folha LNF", f"R$ {avg_payroll/1e6:.1f}M")
    m3.metric("Pool de TV Estimado", "R$ 2.5B")
    
    st.divider()
    
    # Tabela Financeira LNF
    st.subheader("Saúde Financeira - LNF")
    fin_data = []
    for t in lnf_teams:
        cap_usage = (t.payroll / t.salary_cap) * 100
        status = "🟢 OK" if cap_usage <= 100 else "🔴 Multa"
        
        fin_data.append({
            "Time": t.name,
            "Orçamento (Caixa)": f"R$ {t.budget/1e6:.1f}M",
            "Folha Anual": f"R$ {t.payroll/1e6:.1f}M",
            "Uso do Cap": f"{cap_usage:.1f}%",
            "Status": status,
            "Receitas TV/Prêmios": f"R$ {t.revenue/1e6:.1f}M"
        })
    
    df_fin = pd.DataFrame(fin_data).sort_values("Uso do Cap", ascending=False)
    st.dataframe(df_fin, use_container_width=True)
    
    # Botão para Distribuir Dinheiro (Pós-Temporada)
    if st.button("💰 Processar Pagamentos de TV e Prêmios (Final de Temporada)"):
        if not st.session_state.simulated_lnf:
            st.error("Simule a temporada primeiro para calcular as cotas de performance!")
        else:
            engine.distribute_tv_rights()
            st.success("Receitas distribuídas! Confira a coluna 'Receitas' atualizada na tabela acima.")
            st.balloons()

with tab_clubs:
    st.header("Raio-X dos Clubes")
    
    all_teams = engine.teams
    team_names = sorted([t.name for t in all_teams])
    
    selected_team_name = st.selectbox("Escolha um clube para analisar:", team_names)
    
    # Buscar objeto do time
    team = next((t for t in all_teams if t.name == selected_team_name), None)
    
    if team:
        col_profile, col_stats = st.columns([1, 3])
        
        with col_profile:
            st.image(team.logo, width=150)
            st.markdown(f"**{team.name}**")
            st.caption(f"{team.league} - {team.division}")
            st.metric("Rating Geral", team.rating)
            st.metric("Orçamento", f"R$ {team.budget/1e6:.1f}M")
            
        with col_stats:
            st.subheader("Elenco Principal")
            if len(team.players) > 0:
                roster_data = [{
                    "Nome": p.name, 
                    "Pos": p.position, 
                    "Idade": p.age, 
                    "Ovr": p.overall, 
                    "Valor": f"R$ {p.market_value/1e6:.1f}M"
                } for p in team.players]
                st.dataframe(pd.DataFrame(roster_data), height=300, use_container_width=True)
            else:
                st.info("Elenco ainda não gerado.")
                
            st.subheader("Desempenho na Temporada")
            st.write(f"**Jogos:** {team.games_played} | **Vitórias:** {team.wins} | **Gols Pró:** {team.goals_for}")
            
            # Botão para Jogo de Exibição
            st.divider()
            opponent_name = st.selectbox("Escolha adversário para Amistoso:", [t for t in team_names if t != team.name])
            if st.button(f"Jogar Amistoso: {team.name} vs {opponent_name}"):
                opp = next((t for t in all_teams if t.name == opponent_name), None)
                
                # Simular com Narrativa!
                g1, g2, events = engine.simulate_match(team, opp, return_events=True)
                
                st.markdown(f"### Placar Final: {team.name} {g1} x {g2} {opp.name}")
                with st.expander("📺 Ver Melhores Momentos (Minuto a Minuto)", expanded=True):
                    for event in events:
                        st.write(event)

with tab_history:
    st.header("Observatório Nacional de Performance (ONP)")
    
    # Estatísticas Atuais
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"Artilharia LNF {engine.season_year}")
        lnf_teams = engine.get_teams_by_league("LNF")
        all_lnf_players = [p for t in lnf_teams for p in t.players]
        # Top 10 Artilheiros
        top_scorers = sorted(all_lnf_players, key=lambda x: x.goals, reverse=True)[:10]
        
        df_goals = pd.DataFrame([{
            "Jogador": p.name,
            "Time": p.team_name,
            "Gols": p.goals,
            "Overall": p.overall
        } for p in top_scorers])
        st.table(df_goals)
        
    with col2:
        st.subheader("Galeria de Troféus (Hall of Fame)")
        if len(engine.history) > 0:
            st.dataframe(pd.DataFrame(engine.history), use_container_width=True)
        else:
            st.info("Nenhuma temporada concluída ainda.")

    st.divider()
    
    # ZONA DE TRANSIÇÃO DE TEMPORADA
    st.subheader("⚙️ Gestão de Tempo")
    st.markdown("Ao encerrar a temporada, os jogadores envelhecem, estatísticas resetam e o ano vira.")
    
    if st.button("Avance para a Próxima Temporada ⏩"):
        # Precisamos saber quem foi o campeão para salvar no histórico
        # Vamos pegar quem tem mais pontos na LNF como "Campeão" se não houver playoff rodado
        # Idealmente, pegaríamos do estado do playoff, mas aqui faremos uma estimativa segura
        lnf_teams = engine.get_teams_by_league("LNF")
        champ_lnf = sorted(lnf_teams, key=lambda x: x.points, reverse=True)[0]
        
        college_teams = engine.get_teams_by_league("College")
        champ_college = sorted(college_teams, key=lambda x: x.rating, reverse=True)[0] # Proxy
        
        msg = engine.advance_season(champ_lnf, champ_college)
        
        # Resetar estados da UI
        st.session_state.simulated_lnf = False
        st.success(msg)
        st.balloons()

with tab_market:
    st.header("Mercado da Bola 🔁")
    st.markdown("Acompanhe as movimentações financeiras, contratações e o fluxo de atletas.")
    
    if st.button("💰 Abrir Janela de Transferências (Simular Negociações)"):
        if not st.session_state.simulated_lnf:
            st.warning("Recomendado simular a temporada antes para que os times tenham receitas.")
        
        with st.spinner("Negociando contratos... GM IA trabalhando..."):
            transfers = engine.run_transfer_window()
        
        if transfers:
            st.success(f"Janela Fechada! {len(transfers)} negociações realizadas.")
            
            # Exibir as Top 10 mais caras
            # Ordenar por valor (string parsing simples ou armazenar valor cru no log seria melhor, mas ok)
            st.subheader("🔥 Principais Transferências")
            df_transfers = pd.DataFrame(transfers)
            st.dataframe(df_transfers, use_container_width=True)
        else:
            st.info("O mercado estava morno. Nenhuma grande negociação ocorreu (talvez falta de orçamento?).")
