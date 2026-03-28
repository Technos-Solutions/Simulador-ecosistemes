import sqlite3
from datetime import datetime

DB_PATH = "simulador.db"


# =============================================================================
# CLASSE PRINCIPAL: MotorSimulacio
# =============================================================================

class MotorSimulacio:
    """
    Motor de simulació genèric.
    Carrega un escenari de la BD, calcula l'evolució pas a pas
    i guarda els resultats a historial_valors.
    """

    def __init__(self, escenari_id, db_path=DB_PATH):
        self.escenari_id = escenari_id
        self.db_path = db_path
        self.escenari = None
        self.variables = {}       # {id: {nom, valor, valor_min, valor_max, tipus_var, unitat}}
        self.relacions = []       # [{origen_id, desti_id, pes}]
        self.comportaments = []   # [{variable_id, condicio, efecte, intensitat, prioritat}]
        self.pas_actual = 0

    # -------------------------------------------------------------------------
    # CÀRREGA
    # -------------------------------------------------------------------------

    def carregar(self):
        """Carrega l'escenari, variables, relacions i comportaments de la BD."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Carregar escenari
        cursor.execute("SELECT * FROM escenaris WHERE id = ?", (self.escenari_id,))
        self.escenari = dict(cursor.fetchone())

        # Carregar variables dinàmiques
        cursor.execute("""
            SELECT * FROM variables
            WHERE escenari_id = ?
        """, (self.escenari_id,))
        for row in cursor.fetchall():
            self.variables[row['id']] = {
                'nom':         row['nom'],
                'tipus_var':   row['tipus_var'],
                'unitat':      row['unitat'],
                'valor':       row['valor_inicial'],
                'valor_min':   row['valor_min'],
                'valor_max':   row['valor_max'],
            }

        # Carregar relacions
        cursor.execute("""
            SELECT variable_origen_id, variable_desti_id, pes, descripcio
            FROM relacions WHERE escenari_id = ?
        """, (self.escenari_id,))
        for row in cursor.fetchall():
            self.relacions.append({
                'origen_id':  row['variable_origen_id'],
                'desti_id':   row['variable_desti_id'],
                'pes':        row['pes'],
                'descripcio': row['descripcio'],
            })

        # Carregar comportaments
        cursor.execute("""
            SELECT variable_id, condicio, efecte, intensitat, prioritat, descripcio_lliure
            FROM comportaments_variable
            WHERE escenari_id = ? AND actiu = 1
            ORDER BY prioritat ASC
        """, (self.escenari_id,))
        for row in cursor.fetchall():
            self.comportaments.append({
                'variable_id':       row['variable_id'],
                'condicio':          row['condicio'],
                'efecte':            row['efecte'],
                'intensitat':        row['intensitat'],
                'prioritat':         row['prioritat'],
                'descripcio_lliure': row['descripcio_lliure'],
            })

        conn.close()

        # Guardar l'estat inicial (pas 0)
        self._guardar_pas(conn_externa=None)

        print(f"Escenari '{self.escenari['nom']}' carregat.")
        print(f"  Variables: {len(self.variables)}")
        print(f"  Relacions: {len(self.relacions)}")
        print(f"  Comportaments: {len(self.comportaments)}")
        print(f"  Unitat de temps: {self.escenari['unitat_temps']}")
        print(f"  Passos totals: {self.escenari['num_passos']}")

    # -------------------------------------------------------------------------
    # CÀLCUL D'UN PAS
    # -------------------------------------------------------------------------

    def calcular_pas(self):
        """Calcula l'evolució d'un pas de temps i guarda els resultats."""

        if self.pas_actual >= self.escenari['num_passos']:
            print(f"Simulació finalitzada al pas {self.pas_actual}.")
            return False

        self.pas_actual += 1
        nous_valors = {vid: v['valor'] for vid, v in self.variables.items()}

        # 1. Aplicar relacions numèriques
        for rel in self.relacions:
            origen_id = rel['origen_id']
            desti_id  = rel['desti_id']
            pes       = rel['pes']

            if origen_id not in self.variables or desti_id not in self.variables:
                continue

            # Només les variables dinàmiques canvien
            if self.variables[desti_id]['tipus_var'] != 'dinamica':
                continue

            valor_origen = self.variables[origen_id]['valor']
            efecte = valor_origen * pes * 0.05
            nous_valors[desti_id] += efecte

        # 2. Aplicar comportaments especials (mons ficticis)
        for comp in self.comportaments:
            vid = comp['variable_id']
            if vid not in self.variables:
                continue
            try:
                # Avaluem la condició amb el valor actual de la variable
                valor_actual = self.variables[vid]['valor']
                # Preparem context per avaluar condicions
                context = {'valor': valor_actual}
                if eval(comp['condicio'], {"__builtins__": {}}, context):
                    # Apliquem l'efecte escalat per la intensitat
                    exec(comp['efecte'], {"__builtins__": {}},
                         {'nous_valors': nous_valors, 'vid': vid,
                          'intensitat': comp['intensitat']})
            except Exception as e:
                print(f"  Advertència comportament variable {vid}: {e}")

        # 3. Aplicar límits min/max i actualitzar valors
        for vid in nous_valors:
            v = self.variables[vid]
            val = nous_valors[vid]
            if v['valor_min'] is not None:
                val = max(val, v['valor_min'])
            if v['valor_max'] is not None:
                val = min(val, v['valor_max'])
            self.variables[vid]['valor'] = val

        # 4. Guardar pas a la BD
        self._guardar_pas()

        return True

    # -------------------------------------------------------------------------
    # SIMULAR TOTS ELS PASSOS D'UN COP
    # -------------------------------------------------------------------------

    def simular_tot(self):
        """Executa tots els passos de la simulació d'un cop."""
        print(f"\nIniciant simulació: '{self.escenari['nom']}'")
        print(f"Passos: {self.escenari['num_passos']} × 1 {self.escenari['unitat_temps']}\n")

        while self.calcular_pas():
            self._mostrar_resum_pas()

        print(f"\nSimulació completada! ({self.pas_actual} passos)")

    # -------------------------------------------------------------------------
    # GUARDAR PAS A LA BD
    # -------------------------------------------------------------------------

    def _guardar_pas(self, conn_externa=None):
        """Guarda els valors actuals de totes les variables al historial."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for vid, v in self.variables.items():
            cursor.execute("""
                INSERT INTO historial_valors (escenari_id, variable_id, pas, valor)
                VALUES (?, ?, ?, ?)
            """, (self.escenari_id, vid, self.pas_actual, v['valor']))
        conn.commit()
        conn.close()

    # -------------------------------------------------------------------------
    # MOSTRAR RESUM DEL PAS ACTUAL
    # -------------------------------------------------------------------------

    def _mostrar_resum_pas(self):
        """Mostra per consola el resum del pas actual."""
        print(f"--- Pas {self.pas_actual} ({self.escenari['unitat_temps']}) ---")
        for vid, v in self.variables.items():
            if v['tipus_var'] == 'dinamica':
                print(f"  {v['nom']}: {v['valor']:.2f} {v['unitat'] or ''}")

    # -------------------------------------------------------------------------
    # OBTENIR HISTORIAL
    # -------------------------------------------------------------------------

    def obtenir_historial(self):
        """Retorna l'historial de tots els valors com a llista de diccionaris."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT h.pas, v.nom, h.valor, v.unitat
            FROM historial_valors h
            JOIN variables v ON h.variable_id = v.id
            WHERE h.escenari_id = ?
            ORDER BY h.pas ASC, v.nom ASC
        """, (self.escenari_id,))
        historial = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return historial


# =============================================================================
# EXECUCIÓ DE PROVA
# =============================================================================

if __name__ == "__main__":
    # Aquest bloc és per provar el motor manualment.
    # Necessita que existeixi un escenari amb id=1 a la BD.
    motor = MotorSimulacio(escenari_id=1)
    motor.carregar()
    motor.simular_tot()
