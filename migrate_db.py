import sqlite3

conn = sqlite3.connect("geological_data.db")
cur = conn.cursor()

def add_col(table, col, ctype):
    try:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {ctype}")
    except sqlite3.OperationalError:
        pass

for c, t in [
    ("valley_type", "TEXT"), ("valley_name", "TEXT"),          # 1. Долина реки/ручья
    ("tributary_side", "TEXT"), ("tributary_name", "TEXT"),    # приток правого/левого
    ("distance_from_mouth", "REAL"),                           # 2. от устья, м
    ("ref_line", "TEXT"), ("ref_line_distance", "REAL"),       # от линии № … вниз/вверх
    ("year", "TEXT"),
    ("otk_x_from", "REAL"), ("otk_x_to", "REAL"), ("otk_label", "TEXT"),  # отработка
]:
    add_col("lines", c, t)

for c, t in [
    ("location_type", "TEXT"), ("terrace_side", "TEXT"), ("distance_from_riverbed", "REAL"),  # 4
    ("bedrock_character", "TEXT"), ("bedrock_drilled", "REAL"),                               # 8
    ("thaw_1_from", "REAL"), ("thaw_1_to", "REAL"), ("thaw_2_from", "REAL"), ("thaw_2_to", "REAL"),   # 9
    ("frozen_1_from", "REAL"), ("frozen_1_to", "REAL"), ("frozen_2_from", "REAL"), ("frozen_2_to", "REAL"),  # 10
    ("status", "TEXT"),                      # 11 пройдена/остановлена
    ("water_level", "REAL"), ("water_flow", "REAL"),                      # 12–13
    ("bashmak_outer", "REAL"), ("bashmak_inner", "REAL"),                 # 14
    ("diam_start", "REAL"), ("diam_final", "REAL"),
    ("diam_core", "REAL"), ("core_recovery", "REAL"),                     # 15
    ("rig_name", "TEXT"), ("zhelonka", "TEXT"), ("cavernomer", "TEXT"),   # 16
    ("mass_thickness", "REAL"), ("avg_content_plast", "REAL"),
    ("avg_content_massa", "REAL"), ("limitnost", "TEXT"),                 # результаты подсчета
]:
    add_col("wells", c, t)

for c, t in [("volume", "REAL"), ("category", "TEXT"), ("frozen_note", "TEXT")]:
    add_col("layers", c, t)

conn.commit()
print("✅ Миграция выполнена")