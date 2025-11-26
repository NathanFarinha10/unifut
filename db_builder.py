import json
import random

def build_database():
    # Estrutura baseada no PDF - 8 Conferências Regionais
    # LNF já tem 32 times. Aqui alocamos o restante do ecossistema.
    
    # COLLEGE 1 (Nível Série B/C fortes + Estaduais fortes)
    # Lista curada manualmente para garantir realismo nas conferências
    college1_teams = {
        "Amazônica": [
            "Amazonas FC", "Manaus", "Nacional-AM", "São Raimundo-RR", 
            "Rio Branco-AC", "Humaitá", "Porto Velho", "Genus", 
            "Trem", "Santos-AP", "Águia de Marabá", "Tuna Luso"
        ],
        "Nordeste Atlântico": [
            "Sampaio Corrêa", "Moto Club", "River-PI", "Altos", 
            "América-RN", "ABC", "Potiguar", "Botafogo-PB", 
            "Treze", "Campinense", "Sousa", "Ferroviário-CE"
        ],
        "Nordeste Sul": [
            "Náutico", "Santa Cruz", "Retrô", "Petrolina",
            "CRB", "CSA", "ASA", "CSE",
            "Confiança", "Sergipe", "Itabaiana", "Juazeirense"
        ],
        "Centro-Oeste": [
            "Vila Nova", "Aparecidense", "Anápolis", "Goianésia",
            "Brasiliense", "Gama", "Real Brasília", "Ceilândia",
            "Luverdense", "Mixto", "União Rondonópolis", "Operário-VG"
        ],
        "Sudeste Norte": [
            "Tombense", "Athletic Club", "Caldense", "Villa Nova-MG",
            "Pouso Alegre", "Patrocinense", "Democrata-GV", "Ipatinga",
            "Rio Branco-ES", "Desportiva", "Vitória-ES", "Serra"
        ],
        "Sudeste Sul": [
            "Volta Redonda", "Nova Iguaçu", "Portuguesa-RJ", "Madureira",
            "Bangu", "Boavista", "Audax-RJ", "Resende",
            "São José-SP", "Taubaté", "XV de Piracicaba", "Noroeste"
        ],
        "Paulista": [
            "Novorizontino", "Mirassol", "Ituano", "Botafogo-SP",
            "Ferroviária", "Inter de Limeira", "Santo André", "São Bernardo FC",
            "Portuguesa", "Oeste", "Juventus-SP", "São Bento"
        ],
        "Sul": [
            "Figueirense", "Brusque", "Joinville", "Marcílio Dias",
            "Londrina", "Operário-PR", "Paraná Clube", "Maringá",
            "Brasil de Pelotas", "Ypiranga", "Caxias", "São José-RS"
        ]
    }

    # COLLEGE 2 (Nível Série D + Estaduais médios)
    # Geramos nomes baseados em cidades reais/times menores para preencher
    college2_teams = {
        "Amazônica": ["Princesa do Solimões", "Fast Clube", "Galvez", "Plácido de Castro", "Real Ariquemes", "Ji-Paraná", "Ypiranga-AP", "Oratório", "Castanhal", "Cametá", "Bragantino-PA", "Tapajós"],
        "Nordeste Atlântico": ["Maranhão", "Imperatriz", "Parnahyba", "4 de Julho", "Globo", "Santa Cruz-RN", "Nacional de Patos", "Atlético-PB", "Iguatu", "Pacajus", "Caucaia", "Barbalha"],
        "Nordeste Sul": ["Central", "Maguary", "Afogados", "Salgueiro", "Murici", "Coruripe", "Cruzeiro-AL", "Lagarto", "Falcon", "Jacuipense", "Bahia de Feira", "Atlético-BA"],
        "Centro-Oeste": ["Iporá", "Crac", "Morrinhos", "Goianésia", "Paranoá", "Capital-DF", "Santa Maria", "Samambaia", "Operário-MS", "Costa Rica-MS", "Dourados", "Ivinhema"],
        "Sudeste Norte": ["Uberlândia", "URT", "Boa Esporte", "Tupi", "Betim", "Aymorés", "Nova Venécia", "Real Noroeste", "Estrela do Norte", "Linhares", "Valeriodoce", "Mamoré"],
        "Sudeste Sul": ["Olaria", "Americano", "Friburguense", "Cabofriense", "Maricá", "Sampaio Corrêa-RJ", "Comercial-SP", "Marília", "Rio Claro", "Velo Clube", "Primavera", "Capivariano"],
        "Paulista": ["Água Santa", "Linense", "Monte Azul", "Rio Preto", "Votuporanguense", "Sertãozinho", "Nacional-SP", "São Caetano", "Osasco Audax", "EC São Bernardo", "Desportivo Brasil", "União Suzano"],
        "Sul": ["Hercílio Luz", "Camboriú", "Concórdia", "Barra-SC", "FC Cascavel", "Cianorte", "Azuriz", "Rio Branco-PR", "Avenida", "Novo Hamburgo", "Aimoré", "Esportivo"]
    }

    database = {
        "college1": [],
        "college2": []
    }

    # Processar College 1
    for conf_name, teams in college1_teams.items():
        for team_name in teams:
            # Rating para College 1: entre 68 e 78 (Forte)
            rating = random.randint(68, 78)
            # Boost em times tradicionais
            if team_name in ["Santa Cruz", "Náutico", "Paraná Clube", "Vila Nova", "Figueirense", "Novorizontino"]:
                rating += 3
            
            database["college1"].append({
                "name": team_name,
                "conference": conf_name,
                "rating": rating
            })

    # Processar College 2
    for conf_name, teams in college2_teams.items():
        for team_name in teams:
            # Rating para College 2: entre 55 e 65 (Médio/Fraco)
            rating = random.randint(55, 65)
            
            database["college2"].append({
                "name": team_name,
                "conference": conf_name,
                "rating": rating
            })

    # Salvar em JSON
    with open("teams_db.json", "w", encoding="utf-8") as f:
        json.dump(database, f, indent=4, ensure_ascii=False)
    
    print("Banco de dados 'teams_db.json' criado com sucesso com 192 times do College!")

if __name__ == "__main__":
    build_database()
