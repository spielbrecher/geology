import sqlite3
from typing import List, Dict, Optional
from contextlib import contextmanager


class Database:
    def __init__(self, db_path: str = "geological_data.db"):
        self.db_path = db_path

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    # ================= СХЕМА =================
    def create_tables(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    line_number TEXT NOT NULL UNIQUE,
                    river_name TEXT,
                    azimuth TEXT,
                    note TEXT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wells (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    well_number TEXT NOT NULL,
                    line_id INTEGER NOT NULL,
                    x_coordinate REAL NOT NULL,
                    surface_elevation REAL NOT NULL,
                    total_depth REAL NOT NULL,
                    visual_result TEXT,
                    started_date TEXT,
                    ended_date TEXT,
                    FOREIGN KEY (line_id) REFERENCES lines(id),
                    UNIQUE(well_number, line_id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS layers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    well_id INTEGER NOT NULL,
                    depth_from REAL NOT NULL,
                    depth_to REAL NOT NULL,
                    lithology TEXT NOT NULL,
                    hatch_pattern TEXT,
                    gold_content REAL,
                    description TEXT,
                    FOREIGN KEY (well_id) REFERENCES wells(id)
                )
            """)

            # Условные обозначения согласно Приложению 5
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lithology_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lithology_type TEXT NOT NULL UNIQUE,
                    hatch_pattern TEXT NOT NULL,
                    description TEXT
                )
            """)

            default_patterns = [
                ("Торф",       "||",  "Вертикальная штриховка"),
                ("Песок",      "...", "Точки"),
                ("Галька",     "oo",  "Мелкие кружки"),
                ("Валуны",     "OO",  "Крупные кружки"),
                ("Дресва",     "**",  "Мелкие угловатые знаки"),
                ("Щебень",     "xx",  "Угловатые знаки"),
                ("Порфириты",  "++",  "Кресты"),
                ("Песчаники",  "..",  "Редкие точки"),
                ("Алевролиты", "--",  "Горизонтальные штрихи"),
                ("Глина",      "---", "Горизонтальные линии"),
                ("Мерзлота",   "//",  "Диагональная штриховка"),
            ]
            cursor.executemany("""
                INSERT OR IGNORE INTO lithology_patterns
                (lithology_type, hatch_pattern, description)
                VALUES (?, ?, ?)
            """, default_patterns)

    # ================= ЛИНИИ =================
    def add_line(self, line_number: str, river_name: str = None,
                 azimuth: str = None, note: str = None,
                 description: str = None) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO lines
                (line_number, river_name, azimuth, note, description)
                VALUES (?, ?, ?, ?, ?)
            """, (line_number, river_name, azimuth, note, description))
            cursor.execute("SELECT id FROM lines WHERE line_number = ?", (line_number,))
            return cursor.fetchone()['id']

    def get_all_lines(self) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM lines ORDER BY line_number")
            return [dict(row) for row in cursor.fetchall()]

    def get_line_by_number(self, line_number: str) -> Optional[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM lines WHERE line_number = ?", (line_number,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # ================= СКВАЖИНЫ =================
    def add_well(self, data: Dict) -> int:
        """data — словарь колонка->значение (well_number и line_id обязательны)"""
        with self.get_connection() as conn:
            cols = list(data.keys())
            cur = conn.cursor()
            cur.execute(f"INSERT INTO wells ({','.join(cols)}) VALUES ({','.join('?'*len(cols))})",
                        [data[c] for c in cols])
            return cur.lastrowid

    def update_well(self, well_id: int, data: Dict):
        with self.get_connection() as conn:
            sets = ",".join(f"{k}=?" for k in data)
            conn.cursor().execute(f"UPDATE wells SET {sets} WHERE id=?",
                                  [*data.values(), well_id])

    def get_wells_by_line(self, line_id: int) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM wells WHERE line_id = ? ORDER BY x_coordinate",
                           (line_id,))
            return [dict(row) for row in cursor.fetchall()]

    def delete_well(self, well_id: int):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM layers WHERE well_id = ?", (well_id,))
            cursor.execute("DELETE FROM wells WHERE id = ?", (well_id,))

    # ================= СЛОИ / КОНТАКТЫ =================
    def add_layer(self, well_id: int, depth_from: float, depth_to: float,
                  lithology: str, hatch_pattern: str = None,
                  gold_content: float = None, description: str = None) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO layers (well_id, depth_from, depth_to, lithology,
                                    hatch_pattern, gold_content, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (well_id, depth_from, depth_to, lithology, hatch_pattern,
                  gold_content, description))
            return cursor.lastrowid

    def get_layers_by_well(self, well_id: int) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM layers WHERE well_id = ? ORDER BY depth_from",
                           (well_id,))
            return [dict(row) for row in cursor.fetchall()]

    def delete_layers_by_well(self, well_id: int):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM layers WHERE well_id = ?", (well_id,))

    # ================= ШТРИХОВКИ (Приложение 5) =================
    def get_lithology_patterns(self) -> Dict[str, str]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT lithology_type, hatch_pattern FROM lithology_patterns")
            return {row[0]: row[1] for row in cursor.fetchall()}

    def get_lithology_patterns_full(self) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT lithology_type, hatch_pattern, description "
                           "FROM lithology_patterns ORDER BY id")
            return [dict(row) for row in cursor.fetchall()]

    def upsert_pattern(self, lithology: str, hatch: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO lithology_patterns (lithology_type, hatch_pattern)
                VALUES (?, ?)
                ON CONFLICT(lithology_type) DO UPDATE SET hatch_pattern = excluded.hatch_pattern
            """, (lithology, hatch))

    # ================= ДАННЫЕ ДЛЯ РАЗРЕЗА =================
    def get_line_cross_section(self, line_number: str) -> Optional[Dict]:
        line = self.get_line_by_number(line_number)
        if not line:
            return None

        wells = self.get_wells_by_line(line['id'])
        wells_data = {}
        for well in wells:
            layers = self.get_layers_by_well(well['id'])
            wells_data[str(well['well_number'])] = {
                "x": well['x_coordinate'],
                "surface": well['surface_elevation'],
                "depth": well['total_depth'],
                "visual": well['visual_result'],
                "mass": well.get('mass_thickness'),
                "plast": well.get('avg_content_plast'),
                "massa_content": well.get('avg_content_massa'),
                "limitnost": well.get('limitnost'),
                "layers": [
                    {
                        "z_from": layer['depth_from'],
                        "z_to": layer['depth_to'],
                        "lith": layer['lithology'],
                        "hatch": layer['hatch_pattern'],
                        "au": layer['gold_content'],
                    }
                    for layer in layers

                ]
            }
        return {"line": line, "wells_data": wells_data}

    def add_line(self, data: Dict) -> int:
        with self.get_connection() as conn:
            cols = list(data.keys())
            cur = conn.cursor()
            cur.execute(f"INSERT OR IGNORE INTO lines ({','.join(cols)}) VALUES ({','.join('?'*len(cols))})",
                        [data[c] for c in cols])
            cur.execute("SELECT id FROM lines WHERE line_number = ?", (data['line_number'],))
            return cur.fetchone()['id']

    def add_layer(self, data: Dict) -> int:
        with self.get_connection() as conn:
            cols = list(data.keys())
            cur = conn.cursor()
            cur.execute(f"INSERT INTO layers ({','.join(cols)}) VALUES ({','.join('?'*len(cols))})",
                        [data[c] for c in cols])
            return cur.lastrowid