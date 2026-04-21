class MotorSimulacio:
    """
    Motor Stock & Flow per EcoSim.
    
    Tipus de variables:
    - stock: acumulador (ex: Conills, Llops, Volum gel)
    - constant: valor fix que no canvia (ex: Taxa creixement)
    
    Tipus de relacions:
    - lineal: efecte = pes * valor_origen
    - producte: efecte = pes * valor_origen * valor_desti (Lotka-Volterra)
    - proporcional: efecte = pes * (valor_origen / rang_origen)
    """

    def __init__(self, escenari_id, db=None):
        self.escenari_id = escenari_id
        self.db = db
        self.escenari = None
        self.variables = {}
        self.relacions = []
        self.pas_actual = 0

    def carregar(self):
        from database import get_escenari, get_variables, get_relacions
        self.escenari = get_escenari(self.escenari_id)

        vars_raw = get_variables(self.escenari_id)
        for v in vars_raw:
            self.variables[v['id']] = {
                'nom':        v['nom'],
                'tipus_var':  v['tipus_var'],
                'tipus_stock': v.get('tipus_stock', 'stock'),
                'unitat':     v.get('unitat', ''),
                'valor':      float(v['valor_inicial']),
                'valor_min':  float(v['valor_min']) if v['valor_min'] is not None else 0,
                'valor_max':  float(v['valor_max']) if v['valor_max'] is not None else 100,
            }

        rels_raw = get_relacions(self.escenari_id)
        for r in rels_raw:
            self.relacions.append({
                'origen_id':    r['origen_id'],
                'desti_id':     r['desti_id'],
                'pes':          float(r['pes']),
                'tipus_relacio': r.get('tipus_relacio', 'proporcional'),
                'equacio':      r.get('equacio', ''),
            })

        self._guardar_pas()

    def calcular_pas(self):
        if self.pas_actual >= self.escenari['num_passos']:
            return False

        self.pas_actual += 1
        # Copiem valors actuals per calcular tots els efectes simultàniament
        valors_actuals = {vid: v['valor'] for vid, v in self.variables.items()}
        nous_valors = {vid: v['valor'] for vid, v in self.variables.items()}

        for rel in self.relacions:
            origen_id = rel['origen_id']
            desti_id  = rel['desti_id']
            pes       = rel['pes']
            tipus     = rel.get('tipus_relacio', 'proporcional')

            if origen_id not in self.variables or desti_id not in self.variables:
                continue

            v_dest = self.variables[desti_id]
            # Només modifiquem stocks dinàmics
            if v_dest['tipus_var'] != 'dinamica':
                continue

            val_origen = valors_actuals[origen_id]
            val_desti  = valors_actuals[desti_id]

            v_orig = self.variables[origen_id]
            rang_orig = (v_orig['valor_max'] - v_orig['valor_min']) or 1
            rang_dest = (v_dest['valor_max'] - v_dest['valor_min']) or 1

            if tipus == 'producte':
                # Lotka-Volterra: efecte proporcional al producte de les dues poblacions
                # Normalitzem ambdues variables al seu rang
                norm_origen = (val_origen - v_orig['valor_min']) / rang_orig
                norm_desti  = (val_desti  - v_dest['valor_min']) / rang_dest
                efecte = pes * norm_origen * norm_desti * rang_dest
            elif tipus == 'lineal':
                # Efecte directament proporcional al valor absolut
                efecte = pes * val_origen * 0.01
            else:
                # proporcional (per defecte): normalitzat al rang
                norm_origen = (val_origen - v_orig['valor_min']) / rang_orig
                efecte = pes * norm_origen * rang_dest * 0.02

            nous_valors[desti_id] += efecte

        # Aplicar límits i actualitzar
        for vid in nous_valors:
            v   = self.variables[vid]
            val = nous_valors[vid]
            val = max(val, v['valor_min'])
            if v['valor_max']:
                val = min(val, v['valor_max'])
            self.variables[vid]['valor'] = val

        self._guardar_pas()
        return True

    def simular_tot(self):
        while self.calcular_pas():
            pass

    def _guardar_pas(self):
        sb = self.db()
        registres = [
            {
                'escenari_id': self.escenari_id,
                'variable_id': vid,
                'pas': self.pas_actual,
                'valor': v['valor']
            }
            for vid, v in self.variables.items()
        ]
        if registres:
            sb.table('historial_valors').insert(registres).execute()
