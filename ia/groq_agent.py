import os
import json
from groq import Groq

# =============================================================================
# CONFIGURACIÓ
# =============================================================================

# La clau API es llegeix de la variable d'entorn GROQ_API_KEY
# Per configurar-la: set GROQ_API_KEY=la_teva_clau (Windows)
try:
    import streamlit as st
    GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
except Exception:
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

MODEL = "llama3-70b-8192"


# =============================================================================
# CLASSE PRINCIPAL: AgentIA
# =============================================================================

class AgentIA:
    """
    Agent IA basat en Groq que genera automàticament:
    - Variables fixes i dinàmiques per a un escenari
    - Relacions entre variables amb pesos científics
    - Comportaments especials per a variables exòtiques
    """

    def __init__(self, api_key=None):
        self.client = Groq(api_key=api_key or GROQ_API_KEY)

    # -------------------------------------------------------------------------
    # GENERAR ESCENARI COMPLET
    # -------------------------------------------------------------------------

    def generar_escenari(self, tema, context_addicional=""):
        """
        Donat un tema, genera un escenari complet amb variables i relacions.

        Retorna un diccionari amb:
        {
            "descripcio": "...",
            "unitat_temps": "any",
            "num_passos": 10,
            "variables_fixes": [
                {"nom": "...", "unitat": "...", "valor_inicial": 0, "valor_min": 0, "valor_max": 100, "notes": "..."}
            ],
            "variables_dinamiques": [
                {"nom": "...", "unitat": "...", "valor_inicial": 0, "valor_min": 0, "valor_max": 100, "notes": "..."}
            ],
            "relacions": [
                {"origen": "...", "desti": "...", "pes": 0.5, "descripcio": "..."}
            ]
        }
        """

        prompt = f"""Ets un científic expert en modelatge de sistemes complexos i simulació d'ecosistemes.

L'usuari vol simular: "{tema}"
{f'Context addicional: {context_addicional}' if context_addicional else ''}

La teva tasca és generar un escenari de simulació científicament rigorós.

Respon ÚNICAMENT amb un objecte JSON vàlid (sense cap text addicional, sense markdown, sense ```) amb aquesta estructura exacta:

{{
  "descripcio": "descripció clara de l'objectiu de la simulació",
  "unitat_temps": "any",
  "num_passos": 10,
  "variables_fixes": [
    {{
      "nom": "nom de la variable",
      "unitat": "unitat de mesura",
      "valor_inicial": 0,
      "valor_min": 0,
      "valor_max": 100,
      "notes": "per què és fixa i quin paper té"
    }}
  ],
  "variables_dinamiques": [
    {{
      "nom": "nom de la variable",
      "unitat": "unitat de mesura",
      "valor_inicial": 0,
      "valor_min": 0,
      "valor_max": 100,
      "notes": "com evoluciona i per què"
    }}
  ],
  "relacions": [
    {{
      "origen": "nom variable origen",
      "desti": "nom variable destí",
      "pes": 0.5,
      "descripcio": "explicació científica de la relació"
    }}
  ]
}}

Regles importants:
- El pes va de -1 (efecte invers màxim) a +1 (efecte directe màxim)
- Basa els pesos en coneixement científic real
- Inclou entre 3 i 5 variables fixes
- Inclou entre 5 i 10 variables dinàmiques
- Inclou totes les relacions rellevants entre variables
- Els valors inicials han de ser realistes per al tema
- La unitat_temps pot ser: hora, dia, mes, any
"""

        resposta = self.client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=3000,
        )

        contingut = resposta.choices[0].message.content.strip()

        try:
            escenari = json.loads(contingut)
            return escenari
        except json.JSONDecodeError as e:
            print(f"Error parsejant JSON de Groq: {e}")
            print(f"Resposta rebuda:\n{contingut}")
            return None

    # -------------------------------------------------------------------------
    # GENERAR COMPORTAMENTS PER A UNA VARIABLE EXÒTICA
    # -------------------------------------------------------------------------

    def generar_comportament(self, nom_variable, descripcio_lliure, variables_escenari):
        """
        Donat el nom d'una variable i una descripció lliure del seu comportament,
        genera les regles formals de comportament.

        Exemple:
          nom_variable: "Fragment de meteorit lluminiscent"
          descripcio_lliure: "crema tot el que té a menys d'1 metre"
        """

        noms_variables = [v['nom'] for v in variables_escenari]

        prompt = f"""Ets un expert en simulació científica.

Una variable del simulador es diu: "{nom_variable}"
El seu comportament descrit per l'usuari és: "{descripcio_lliure}"

Les altres variables del sistema són: {json.dumps(noms_variables, ensure_ascii=False)}

Genera les regles de comportament formals per aquesta variable.
Respon ÚNICAMENT amb un JSON vàlid (sense markdown ni text addicional):

[
  {{
    "condicio": "expressió Python avaluable, ex: valor > 70",
    "efecte": "codi Python executable, ex: nous_valors[vid] = valor_actual * 1.1",
    "intensitat": 0.8,
    "prioritat": 1,
    "descripcio_lliure": "explicació en llenguatge natural"
  }}
]
"""

        resposta = self.client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1000,
        )

        contingut = resposta.choices[0].message.content.strip()

        try:
            comportaments = json.loads(contingut)
            return comportaments
        except json.JSONDecodeError as e:
            print(f"Error parsejant comportaments: {e}")
            return []

    # -------------------------------------------------------------------------
    # EXPLICAR L'EVOLUCIÓ D'UN PAS
    # -------------------------------------------------------------------------

    def explicar_pas(self, escenari_nom, pas, valors_anteriors, valors_nous):
        """
        Genera una explicació científica en llenguatge natural
        dels canvis ocorreguts en un pas de simulació.
        """

        canvis = []
        for nom in valors_nous:
            if nom in valors_anteriors:
                diff = valors_nous[nom] - valors_anteriors[nom]
                if abs(diff) > 0.01:
                    canvis.append(f"{nom}: {valors_anteriors[nom]:.2f} → {valors_nous[nom]:.2f}")

        if not canvis:
            return "No hi ha canvis significatius en aquest pas."

        prompt = f"""Ets un científic expert. Explica breument (2-3 frases) en català
què ha passat en aquest pas de simulació de l'escenari "{escenari_nom}":

Pas {pas}. Canvis observats:
{chr(10).join(canvis)}

Explica les causes i efectes de manera clara i científica, sense tecnicismes innecessaris.
"""

        resposta = self.client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=300,
        )

        return resposta.choices[0].message.content.strip()


# =============================================================================
# PROVA RÀPIDA
# =============================================================================

if __name__ == "__main__":
    agent = AgentIA()

    print("Generant escenari: Bosc pirinenc afectat per la sequera...")
    escenari = agent.generar_escenari("Bosc pirinenc afectat per la sequera")

    if escenari:
        print(f"\nDescripció: {escenari['descripcio']}")
        print(f"Unitat de temps: {escenari['unitat_temps']}")
        print(f"\nVariables fixes ({len(escenari['variables_fixes'])}):")
        for v in escenari['variables_fixes']:
            print(f"  - {v['nom']} ({v['unitat']}): {v['valor_inicial']}")
        print(f"\nVariables dinàmiques ({len(escenari['variables_dinamiques'])}):")
        for v in escenari['variables_dinamiques']:
            print(f"  - {v['nom']} ({v['unitat']}): {v['valor_inicial']}")
        print(f"\nRelacions ({len(escenari['relacions'])}):")
        for r in escenari['relacions']:
            print(f"  - {r['origen']} → {r['desti']} (pes: {r['pes']}): {r['descripcio']}")
