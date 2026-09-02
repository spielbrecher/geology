"""Самоинициализация БД: полная схема + демо-данные при первом старте."""
import sqlite3
from database import Database

db = Database()
db.create_tables()

# ========== достройка новых колонок (идемпотентно, заменяет migrate_db.py) ==========
conn = sqlite3.connect(db.db_path)
cur = conn.cursor()

def add_col(table, col, ctype):
    try:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {ctype}")
    except sqlite3.OperationalError:
        pass

for c, t in [
    ("valley_type", "TEXT"), ("valley_name", "TEXT"),
    ("tributary_side", "TEXT"), ("tributary_name", "TEXT"),
    ("distance_from_mouth", "REAL"), ("ref_line", "TEXT"), ("ref_line_distance", "REAL"),
    ("year", "TEXT"), ("otk_x_from", "REAL"), ("otk_x_to", "REAL"), ("otk_label", "TEXT"),
]:
    add_col("lines", c, t)

for c, t in [
    ("location_type", "TEXT"), ("terrace_side", "TEXT"), ("distance_from_riverbed", "REAL"),
    ("bedrock_character", "TEXT"), ("bedrock_drilled", "REAL"),
    ("thaw_1_from", "REAL"), ("thaw_1_to", "REAL"), ("thaw_2_from", "REAL"), ("thaw_2_to", "REAL"),
    ("frozen_1_from", "REAL"), ("frozen_1_to", "REAL"), ("frozen_2_from", "REAL"), ("frozen_2_to", "REAL"),
    ("status", "TEXT"), ("water_level", "REAL"), ("water_flow", "REAL"),
    ("bashmak_outer", "REAL"), ("bashmak_inner", "REAL"),
    ("diam_start", "REAL"), ("diam_final", "REAL"), ("diam_core", "REAL"), ("core_recovery", "REAL"),
    ("rig_name", "TEXT"), ("zhelonka", "TEXT"), ("cavernomer", "TEXT"),
    ("mass_thickness", "REAL"), ("avg_content_plast", "REAL"),
    ("avg_content_massa", "REAL"), ("limitnost", "TEXT"),
]:
    add_col("wells", c, t)

for c, t in [("volume", "REAL"), ("category", "TEXT"), ("frozen_note", "TEXT")]:
    add_col("layers", c, t)

conn.commit()
conn.close()

# ========== демо-данные только при пустой БД ==========
if db.get_all_lines():
    print("ℹ️ БД уже содержит данные — сид пропускаем")
else:
    # ---------- Линия 91 (р. Озёрный) ----------
    line91 = db.add_line({"line_number": "91", "river_name": "р. Озёрный"})
    W91 = {
        10: (10, 105, 50, "ЗНК", [(0, 4, "Торф", None), (4, 22, "Песок", 1.2), (22, 48, "Галька", 4.5), (48, 50, "Глина", None)]),
        13: (25, 103, 48, "СЛ", [(0, 5, "Торф", None), (5, 25, "Песок", 0.8), (25, 45, "Галька", 3.1), (45, 48, "Глина", None)]),
        16: (40, 107, 50, "РБС", [(0, 6, "Торф", None), (6, 20, "Песок", 0.5), (20, 44, "Галька", 6.2), (44, 50, "Глина", None)]),
        19: (55, 104, 50, "Пыль", [(0, 3, "Торф", None), (3, 18, "Песок", 1.5), (18, 48, "Галька", 2.8), (48, 50, "Глина", None)]),
        20: (68, 106, 50, "ЗНК", [(0, 4, "Торф", None), (4, 21, "Песок", 1.1), (21, 47, "Галька", 3.7), (47, 50, "Глина", None)]),
        21: (80, 105, 50, "СЛ", [(0, 5, "Торф", None), (5, 23, "Песок", 0.9), (23, 49, "Галька", 2.4), (49, 50, "Глина", None)]),
    }
    for num, (x, s, d, v, layers) in W91.items():
        wid = db.add_well({"well_number": str(num), "line_id": line91, "x_coordinate": x,
                           "surface_elevation": s, "total_depth": d, "visual_result": v})
        for f, t, l, a in layers:
            db.add_layer({"well_id": wid, "depth_from": f, "depth_to": t, "lithology": l, "gold_content": a})

    # ---------- Линия 2 (руч. Безымянный) ----------
    line2 = db.add_line({"line_number": "2", "river_name": "руч. Безымянный",
                         "azimuth": "154°", "note": "Линия пройдена в мерзлоте", "year": "2021"})
    W2 = {0: (0, 280.0, 8.0, "СЛ"), 2: (20, 279.0, 10.0, "ЗНК"), 4: (40, 281.0, 12.0, "ЗНК"),
          6: (60, 278.0, 9.0, "Пыль"), 8: (80, 280.0, 8.0, "СЛ")}
    for num, (x, s, d, v) in W2.items():
        wid = db.add_well({"well_number": str(num), "line_id": line2, "x_coordinate": x,
                           "surface_elevation": s, "total_depth": d, "visual_result": v})
        for f, t, l, a in [(0.0, 0.8, "Торф", None), (0.8, 4.0, "Песок", None),
                           (4.0, 7.0, "Галька", 72 if num == 4 else None), (7.0, d, "Глина", None)]:
            db.add_layer({"well_id": wid, "depth_from": f, "depth_to": t, "lithology": l, "gold_content": a})

    # ---------- Линия 14 (руч. Тёплый, распознано из Л-14 С-0…С-8) ----------
    line14 = db.add_line({
        "line_number": "14", "river_name": "руч. Тёплый",
        "valley_type": "ручья", "valley_name": "Тёплый", "tributary_name": "Весенний",
        "distance_from_mouth": 1400.0, "ref_line": "12", "ref_line_distance": 180.0,
        "azimuth": "256°", "year": "2021", "note": "Линия пройдена в мерзлоте",
        "description": "ООО «Грин Лайн», участок «Весенний, Тёплый»",
    })
    W14 = [
        ("0", 0.0,  324.5, 3.6, "22.01.2021", 240, "РБС"),
        ("2", 20.0, 324.4, 4.0, "23.01.2021", 360, "н/п"),
        ("4", 40.0, 324.5, 4.8, "23.01.2021", 615, "РБС"),
        ("6", 60.0, 324.6, 4.8, "23.01.2021", 163, "РБС"),
        ("8", 80.0, 324.8, 5.2, "24.01.2021", 102, "РБС"),
    ]
    for num, x, surf, depth, date, au, limit in W14:
        bed_top = round(depth - 0.8, 1)
        pay_top = round(bed_top - (1.2 if depth <= 4.0 else 2.0), 1)
        pay_th = round(bed_top - pay_top, 1)
        mass_th = round(depth - 0.4, 1)
        wid = db.add_well({
            "well_number": num, "line_id": line14, "x_coordinate": x,
            "surface_elevation": surf, "total_depth": depth,
            "started_date": date, "ended_date": date, "status": "остановлена",
            "bedrock_character": "Мелкий щебень, дресва", "bedrock_drilled": 0.8,
            "frozen_1_from": 0.0, "frozen_1_to": depth,
            "diam_start": 152.0, "diam_final": 133.0, "rig_name": "УРБ-50",
            "mass_thickness": mass_th, "avg_content_plast": float(au),
            "avg_content_massa": round(au * pay_th / mass_th), "limitnost": limit,
        })
        for f, t, l, a, desc in [
            (0.0, 0.4, "Торф", None, "Инт. 0,0–0,4 м торф"),
            (0.4, pay_top, "Песок", None, "песок раз/зерн., редкий гравий, дресва"),
            (pay_top, bed_top, "Галька", au, "галька, дресва, щебень; золото"),
            (bed_top, depth, "Щебень", None, "коренные: мелкий щебень, дресва"),
        ]:
            db.add_layer({"well_id": wid, "depth_from": f, "depth_to": t, "lithology": l,
                          "gold_content": a, "description": desc, "frozen_note": "мерзлота"})

    print("🎉 Демо-данные загружены: линии 91, 2, 14")