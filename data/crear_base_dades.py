import sqlite3
import os
from datetime import datetime

DB_PATH = "simulador.db"


def crear_base_dades(db_path=DB_PATH):
    """Crea la base de dades SQLite del simulador amb totes les taules."""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

    # -------------------------------------------------------------------------
    # TAULA: escenaris
    # -------------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS escenaris (
            id              INTEGER  PRIMARY KEY AUTOINCREMENT,
            nom             TEXT     NOT NULL,
            tema            TEXT     NOT NULL,
            descripcio      TEXT,
            conclusions     TEXT,
            unitat_temps    TEXT     NOT NULL DEFAULT 'any'
                                     CHECK(unitat_temps IN ('hora', 'dia', 'mes', 'any')),
            num_passos      INTEGER  NOT NULL DEFAULT 10,
            estat           TEXT     NOT NULL DEFAULT 'actiu'
                                     CHECK(estat IN ('actiu', 'pausat', 'finalitzat')),
            creat_el        DATETIME NOT NULL DEFAULT (datetime('now')),
            modificat_el    DATETIME NOT NULL DEFAULT (datetime('now'))
        );
    """)

    # -------------------------------------------------------------------------
    # TAULA: notes_escenari
    # -------------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes_escenari (
            id              INTEGER  PRIMARY KEY AUTOINCREMENT,
            escenari_id     INTEGER  NOT NULL REFERENCES escenaris(id) ON DELETE CASCADE,
            nota            TEXT     NOT NULL,
            registrat_el    DATETIME NOT NULL DEFAULT (datetime('now'))
        );
    """)

    # -------------------------------------------------------------------------
    # TAULA: variables
    # -------------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS variables (
            id              INTEGER  PRIMARY KEY AUTOINCREMENT,
            escenari_id     INTEGER  NOT NULL REFERENCES escenaris(id) ON DELETE CASCADE,
            nom             TEXT     NOT NULL,
            tipus_var       TEXT     NOT NULL
                                     CHECK(tipus_var IN ('fixa', 'dinamica')),
            unitat          TEXT,
            valor_inicial   REAL     NOT NULL,
            valor_min       REAL,
            valor_max       REAL,
            notes           TEXT
        );
    """)

    # -------------------------------------------------------------------------
    # TAULA: comportaments_variable
    # Regles de comportament pròpies de cada variable (opcional).
    # Especialment útil per mons ficticis amb variables exòtiques.
    # Exemple: "Fragment de meteorit → crema tot el que té a menys d'1m"
    # -------------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comportaments_variable (
            id                INTEGER  PRIMARY KEY AUTOINCREMENT,
            variable_id       INTEGER  NOT NULL REFERENCES variables(id) ON DELETE CASCADE,
            escenari_id       INTEGER  NOT NULL REFERENCES escenaris(id) ON DELETE CASCADE,
            condicio          TEXT     NOT NULL,   -- Ex: "distancia < 1", "valor > 50"
            efecte            TEXT     NOT NULL,   -- Ex: "crema = true", "llum += 0.8"
            intensitat        REAL     NOT NULL DEFAULT 1.0
                                       CHECK(intensitat BETWEEN 0 AND 1),
            prioritat         INTEGER  NOT NULL DEFAULT 1,
            actiu             INTEGER  NOT NULL DEFAULT 1
                                       CHECK(actiu IN (0, 1)),
            descripcio_lliure TEXT,                -- Text lliure de l'usuari
            generada_per_ia   INTEGER  NOT NULL DEFAULT 0
                                       CHECK(generada_per_ia IN (0, 1)),
            registrat_el      DATETIME NOT NULL DEFAULT (datetime('now'))
        );
    """)

    # -------------------------------------------------------------------------
    # TAULA: relacions
    # -------------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS relacions (
            id                  INTEGER  PRIMARY KEY AUTOINCREMENT,
            escenari_id         INTEGER  NOT NULL REFERENCES escenaris(id) ON DELETE CASCADE,
            variable_origen_id  INTEGER  NOT NULL REFERENCES variables(id) ON DELETE CASCADE,
            variable_desti_id   INTEGER  NOT NULL REFERENCES variables(id) ON DELETE CASCADE,
            pes                 REAL     NOT NULL DEFAULT 0
                                         CHECK(pes BETWEEN -1 AND 1),
            descripcio          TEXT,
            generada_per_ia     INTEGER  NOT NULL DEFAULT 0
                                         CHECK(generada_per_ia IN (0, 1))
        );
    """)

    # -------------------------------------------------------------------------
    # TAULA: historial_valors
    # -------------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historial_valors (
            id              INTEGER  PRIMARY KEY AUTOINCREMENT,
            escenari_id     INTEGER  NOT NULL REFERENCES escenaris(id) ON DELETE CASCADE,
            variable_id     INTEGER  NOT NULL REFERENCES variables(id) ON DELETE CASCADE,
            pas             INTEGER  NOT NULL,
            valor           REAL     NOT NULL,
            registrat_el    DATETIME NOT NULL DEFAULT (datetime('now'))
        );
    """)

    # -------------------------------------------------------------------------
    # ÍNDEXS
    # -------------------------------------------------------------------------
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_variables_escenari     ON variables(escenari_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_escenari         ON notes_escenari(escenari_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_comportaments_variable ON comportaments_variable(variable_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_comportaments_escenari ON comportaments_variable(escenari_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_relacions_escenari     ON relacions(escenari_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_historial_escenari     ON historial_valors(escenari_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_historial_variable     ON historial_valors(variable_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_historial_pas          ON historial_valors(pas);")

    conn.commit()
    conn.close()

    print(f"Base de dades creada correctament a: {os.path.abspath(db_path)}")
    print("Taules creades:")
    print("  - escenaris               (amb unitat_temps i num_passos configurables)")
    print("  - notes_escenari          (historial de notes amb data i hora)")
    print("  - variables               (fixes i dinàmiques, sense límit)")
    print("  - comportaments_variable  (regles de comportament per mons ficticis)")
    print("  - relacions               (com les variables s'afecten numèricament)")
    print("  - historial_valors        (evolució pas a pas de cada variable)")


# -------------------------------------------------------------------------
# FUNCIONS AUXILIARS
# -------------------------------------------------------------------------

def afegir_nota(escenari_id, nota, db_path=DB_PATH):
    """Afegeix una nota nova a l'historial d'un escenari."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO notes_escenari (escenari_id, nota) VALUES (?, ?)", (escenari_id, nota))
    conn.commit()
    conn.close()
    print(f"Nota afegida a l'escenari {escenari_id}.")


def actualitzar_conclusions(escenari_id, conclusions, db_path=DB_PATH):
    """Actualitza el resum fixe de conclusions d'un escenari."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE escenaris SET conclusions = ?, modificat_el = datetime('now') WHERE id = ?
    """, (conclusions, escenari_id))
    conn.commit()
    conn.close()
    print(f"Conclusions actualitzades a l'escenari {escenari_id}.")


def veure_notes(escenari_id, db_path=DB_PATH):
    """Mostra totes les notes d'un escenari ordenades per data."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT registrat_el, nota FROM notes_escenari
        WHERE escenari_id = ? ORDER BY registrat_el ASC
    """, (escenari_id,))
    notes = cursor.fetchall()
    conn.close()
    if not notes:
        print("Aquest escenari no té notes encara.")
    else:
        print(f"\n--- Notes de l'escenari {escenari_id} ---")
        for data, nota in notes:
            print(f"[{data}] {nota}")


def afegir_comportament(variable_id, escenari_id, condicio, efecte,
                        intensitat=1.0, prioritat=1, descripcio_lliure=None,
                        generada_per_ia=0, db_path=DB_PATH):
    """Afegeix una regla de comportament a una variable."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO comportaments_variable
            (variable_id, escenari_id, condicio, efecte, intensitat,
             prioritat, descripcio_lliure, generada_per_ia)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (variable_id, escenari_id, condicio, efecte, intensitat,
          prioritat, descripcio_lliure, generada_per_ia))
    conn.commit()
    conn.close()
    print(f"Comportament afegit a la variable {variable_id}.")


# -------------------------------------------------------------------------
# EXECUCIÓ PRINCIPAL
# -------------------------------------------------------------------------
if __name__ == "__main__":
    crear_base_dades()
