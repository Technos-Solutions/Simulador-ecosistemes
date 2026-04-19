from datetime import datetime

class MotorSimulacio:
    """Motor de simulació genèric amb Supabase."""

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
                'nom':       v['nom'],
                'tipus_var': v['tipus_var'],
                'unitat':    v.get('unitat', ''),
                'valor':     float(v['valor_inicial']),
                'valor_min': float(v['valor_min']) if v['valor_min'] is not None else 0,
                'valor_max': float(v['valor_max']) if v['valor_max'] is not None else 100,
            }
        rels_raw = get_relacions(self.escenari_id)
        for r in rels_raw:
            self.relacions.append({
                'origen_id': r['origen_id'],
                'desti_id':  r['desti_id'],
                'pes':       float(r['pes']),
            })
        self._guardar_pas()

    def calcular_pas(self):
        if self.pas_actual >= self.escenari['num_passos']:
            return False
        self.pas_actual += 1
        nous_valors = {vid: v['valor'] for vid, v in self.variables.items()}

        for rel in self.relacions:
            origen_id = rel['origen_id']
            desti_id  = rel['desti_id']
            pes       = rel['pes']
            if origen_id not in self.variables or desti_id not in self.variables:
                continue
            if self.variables[desti_id]['tipus_var'] != 'dinamica':
                continue
            v_orig = self.variables[origen_id]
            v_dest = self.variables[desti_id]
            v_min  = v_orig['valor_min'] or 0
            v_max  = v_orig['valor_max'] or 100
            rang   = v_max - v_min if v_max != v_min else 1
            valor_normalitzat = (v_orig['valor'] - v_min) / rang
            d_min  = v_dest['valor_min'] or 0
            d_max  = v_dest['valor_max'] or 100
            rang_dest = d_max - d_min if d_max != d_min else 1
            efecte = pes * valor_normalitzat * rang_dest * 0.02
            nous_valors[desti_id] += efecte

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
            {'escenari_id': self.escenari_id, 'variable_id': vid,
             'pas': self.pas_actual, 'valor': v['valor']}
            for vid, v in self.variables.items()
        ]
        if registres:
            sb.table('historial_valors').insert(registres).execute()
