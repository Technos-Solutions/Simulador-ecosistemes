import sqlite3
import os
from datetime import datetime

DB_PATH = "simulador.db"


def crear_base_dades(db_path=DB_PATH):
    """Crea la base de dades SQLite del simulador amb totes les taules."""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Activar claus foranes
    cursor.execute("PRAGMA foreign_keys = ON;")

    # -------------------------------------------------------------------------
    # TAULA: escenaris
    # -------------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS escenaris (
            id              INTEGER  PRIMARY KEY AUTOINCREMENT,
            nom             TEXT     NOT NULL,
            tema            TEXT     NOT NULL,
            descripcio      TEXT,               -- Objectiu i context del simulador (sense límit)
            conclusions     TEXT,               -- Resum fixe sempre editable: on ets i per on continues
            estat           TEXT     NOT NULL DEFAULT 'actiu'
                                     CHECK(estat IN ('actiu', 'pausat', 'finalitzat')),
            creat_el        DATETIME NOT NULL DEFAULT (datetime('now')),
            modificat_el    DATETIME NOT NULL DEFAULT (datetime('now'))
        );
    """)

    # -------------------------------------------------------------------------
    # TAULA: notes_escenari
    # Historial de notes amb data i hora. Mai s'esborra cap entrada.
    # -------------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes_escenari (
            id              INTEGER  PRIMARY KEY AUTOINCREMENT,
            escenari_id     INTEGER  NOT NULL REFERENCES escenaris(id) ON DELETE CASCADE,
            nota            TEXT     NOT NULL,  -- Sense límit de caràcters
            registrat_el    DATETIME NOT NULL DEFAULT (datetime('now'))
        );
    """)

    # -------------------------------------------------------------------------
    # TAULA: variables
    # Cada fila és una variable (fixa o dinàmica) d'un escenari.
    # No hi ha límit de variables per escenari.
    # -------------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS variables (
            id              INTEGER  PRIMARY KEY AUTOINCREMENT,
            escenari_id     INTEGER  NOT NULL REFERENCES escenaris(id) ON DELETE CASCADE,
            nom             TEXT     NOT NULL,
            tipus_var       TEXT     NOT NULL
                                     CHECK(tipus_var IN ('fixa', 'dinamica')),
            unitat          TEXT,               -- Ex: "°C", "mm/any", "%", "individus/km²"
            valor_inicial   REAL     NOT NULL,
            valor_min       REAL,               -- Límit inferior possible
            valor_max       REAL,               -- Límit superior possible
            notes           TEXT                -- Observacions addicionals sobre la variable
        );
    """)

    # -------------------------------------------------------------------------
    # TAULA: relacions
    # Defineix com una variable afecta una altra.
    # El pes va de -1 (efecte invers màxim) a +1 (efecte directe màxim).
    # -------------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS relacions (
            id                  INTEGER  PRIMARY KEY AUTOINCREMENT,
            escenari_id         INTEGER  NOT NULL REFERENCES escenaris(id) ON DELETE CASCADE,
            variable_origen_id  INTEGER  NOT NULL REFERENCES variables(id) ON DELETE CASCADE,
            variable_desti_id   INTEGER  NOT NULL REFERENCES variables(id) ON DELETE CASCADE,
            pes                 REAL     NOT NULL DEFAULT 0
                                         CHECK(pes BETWEEN -1 AND 1),
            descripcio          TEXT,           -- Ex: "pluja+ → humitat del sòl+"
            generada_per_ia     INTEGER  NOT NULL DEFAULT 0
                                         CHECK(generada_per_ia IN (0, 1))
        );
    """)

    # -------------------------------------------------------------------------
    # TAULA: historial_valors
    # Registra el valor de cada variable a cada pas de temps.
    # -------------------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historial_valors (
            id              INTEGER  PRIMARY KEY AUTOINCREMENT,
            escenari_id     INTEGER  NOT NULL REFERENCES escenaris(id) ON DELETE CASCADE,
            variable_id     INTEGER  NOT NULL REFERENCES variables(id) ON DELETE CASCADE,
            pas             INTEGER  NOT NULL,  -- 0, 1, 2, 3...
            valor           REAL     NOT NULL,
            registrat_el    DATETIME NOT NULL DEFAULT (datetime('now'))
        );
    """)

    # -------------------------------------------------------------------------
    # ÍNDEXS per agilitzar les consultes
    # -------------------------------------------------------------------------
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_variables_escenari ON variables(escenari_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_escenari     ON notes_escenari(escenari_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_relacions_escenari ON relacions(escenari_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_historial_escenari ON historial_valors(escenari_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_historial_variable ON historial_valors(variable_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_historial_pas      ON historial_valors(pas);")

    conn.commit()
    conn.close()

    print(f"Base de dades creada correctament a: {os.path.abspath(db_path)}")
    print("Taules creades:")
    print("  - escenaris        (resum fixe + conclusions sempre editables)")
    print("  - notes_escenari   (historial de notes amb data i hora, mai s'esborra)")
    print("  - variables        (fixes i dinàmiques, sense límit)")
    print("  - relacions        (com les variables s'afecten entre elles)")
    print("  - historial_valors (evolució pas a pas de cada variable)")


# -------------------------------------------------------------------------
# FUNCIONS AUXILIARS
# -------------------------------------------------------------------------

def afegir_nota(escenari_id, nota, db_path=DB_PATH):
    """Afegeix una nota nova a l'historial d'un escenari."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO notes_escenari (escenari_id, nota)
        VALUES (?, ?)
    """, (escenari_id, nota))
    conn.commit()
    conn.close()
    print(f"Nota afegida a l'escenari {escenari_id}.")


def actualitzar_conclusions(escenari_id, conclusions, db_path=DB_PATH):
    """Actualitza el resum fixe de conclusions d'un escenari."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE escenaris
        SET conclusions = ?, modificat_el = datetime('now')
        WHERE id = ?
    """, (conclusions, escenari_id))
    conn.commit()
    conn.close()
    print(f"Conclusions actualitzades a l'escenari {escenari_id}.")


def veure_notes(escenari_id, db_path=DB_PATH):
    """Mostra totes les notes d'un escenari ordenades per data."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT registrat_el, nota
        FROM notes_escenari
        WHERE escenari_id = ?
        ORDER BY registrat_el ASC
    """, (escenari_id,))
    notes = cursor.fetchall()
    conn.close()

    if not notes:
        print("Aquest escenari no té notes encara.")
    else:
        print(f"\n--- Notes de l'escenari {escenari_id} ---")
        for data, nota in notes:
            print(f"[{data}] {nota}")


# -------------------------------------------------------------------------
# EXECUCIÓ PRINCIPAL
# -------------------------------------------------------------------------
if __name__ == "__main__":
    crear_base_dades()
