import sqlite3
import sys
import os

# Afegim el path del projecte per poder importar els mòduls
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.crear_base_dades import crear_base_dades
from core.motor import MotorSimulacio

DB_PATH = "simulador_prova.db"


def crear_escenari_bosc():
    """Crea un escenari de prova: Bosc pirinenc."""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Crear escenari
    cursor.execute("""
        INSERT INTO escenaris (nom, tema, descripcio, unitat_temps, num_passos)
        VALUES (?, ?, ?, ?, ?)
    """, (
        "Bosc pirinenc - prova",
        "Evolució d'un bosc",
        "Estudi de com evoluciona un bosc pirinenc al llarg de 10 anys "
        "en funció de la temperatura, la pluja i el risc d'incendi.",
        "any",
        10
    ))
    escenari_id = cursor.lastrowid

    # 2. Variables fixes
    fixes = [
        ("Altitud",    "m",    1200, 0,    4000),
        ("Tipus sòl",  "codi",    1, 0,       5),
    ]
    for nom, unitat, valor, vmin, vmax in fixes:
        cursor.execute("""
            INSERT INTO variables (escenari_id, nom, tipus_var, unitat, valor_inicial, valor_min, valor_max)
            VALUES (?, ?, 'fixa', ?, ?, ?, ?)
        """, (escenari_id, nom, unitat, valor, vmin, vmax))

    # 3. Variables dinàmiques
    dinamiques = [
        ("Temperatura",      "°C",          12,  -20,   50),
        ("Pluja",            "mm/any",      600,   0, 2000),
        ("Humitat sòl",      "%",            55,   0,  100),
        ("Densitat arbres",  "arbres/ha",   300,   0,  800),
        ("Fauna herbívors",  "ind/km²",      40,   0,  200),
        ("Risc incendi",     "%",            20,   0,  100),
    ]
    var_ids = {}
    for nom, unitat, valor, vmin, vmax in dinamiques:
        cursor.execute("""
            INSERT INTO variables (escenari_id, nom, tipus_var, unitat, valor_inicial, valor_min, valor_max)
            VALUES (?, ?, 'dinamica', ?, ?, ?, ?)
        """, (escenari_id, nom, unitat, valor, vmin, vmax))
        var_ids[nom] = cursor.lastrowid

    # 4. Relacions entre variables
    relacions = [
        ("Pluja",           "Humitat sòl",      0.6,  "Més pluja → més humitat al sòl"),
        ("Temperatura",     "Risc incendi",     0.5,  "Més calor → més risc d'incendi"),
        ("Humitat sòl",     "Densitat arbres",  0.4,  "Més humitat → més arbres"),
        ("Densitat arbres", "Fauna herbívors",  0.3,  "Més arbres → més fauna"),
        ("Risc incendi",    "Densitat arbres", -0.7,  "Incendi → destrueix arbres"),
        ("Temperatura",     "Humitat sòl",     -0.3,  "Més calor → menys humitat"),
        ("Temperatura",     "Pluja",           -0.2,  "Més calor → menys pluja"),
    ]
    for origen, desti, pes, desc in relacions:
        cursor.execute("""
            INSERT INTO relacions (escenari_id, variable_origen_id, variable_desti_id, pes, descripcio)
            VALUES (?, ?, ?, ?, ?)
        """, (escenari_id, var_ids[origen], var_ids[desti], pes, desc))

    # 5. Comportament especial: risc d'incendi crític
    cursor.execute("""
        INSERT INTO comportaments_variable
            (variable_id, escenari_id, condicio, efecte, intensitat, prioritat, descripcio_lliure)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        var_ids["Risc incendi"],
        escenari_id,
        "valor > 70",
        "nous_valors[vid] = valor_actual * (1 + 0.1 * intensitat)",
        0.8,
        1,
        "Quan el risc d'incendi supera el 70%, s'accelera exponencialment"
    ))

    conn.commit()
    conn.close()

    print(f"Escenari creat amb id={escenari_id}")
    return escenari_id


# =============================================================================
# EXECUCIÓ PRINCIPAL
# =============================================================================

if __name__ == "__main__":

    print("=" * 50)
    print("PROVA DEL MOTOR DE SIMULACIÓ")
    print("Escenari: Bosc pirinenc")
    print("=" * 50)

    # 1. Crear la BD de prova
    crear_base_dades(DB_PATH)

    # 2. Crear l'escenari
    escenari_id = crear_escenari_bosc()

    # 3. Executar el motor
    motor = MotorSimulacio(escenari_id=escenari_id, db_path=DB_PATH)
    motor.carregar()
    motor.simular_tot()

    # 4. Mostrar historial final
    print("\n" + "=" * 50)
    print("HISTORIAL FINAL DE VALORS")
    print("=" * 50)
    historial = motor.obtenir_historial()
    pas_actual = -1
    for reg in historial:
        if reg['pas'] != pas_actual:
            pas_actual = reg['pas']
            print(f"\nPas {pas_actual}:")
        print(f"  {reg['nom']}: {reg['valor']:.2f} {reg['unitat'] or ''}")
