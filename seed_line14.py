"""Тестовые данные: руч. Тёплый, линия 14 (распознано из Л-14 С-0…С-8)."""
from database import Database

db = Database()
db.create_tables()

line_id = db.add_line({
    "line_number": "14",
    "river_name": "руч. Тёплый",
    "valley_type": "ручья",
    "valley_name": "Тёплый",
    "tributary_name": "Весенний",
    "distance_from_mouth": 1400.0,
    "ref_line": "12",
    "ref_line_distance": 180.0,
    "azimuth": "256°",
    "year": "2021",
    "note": "Линия пройдена в мерзлоте",
    "description": "ООО «Грин Лайн», участок «Весенний, Тёплый»",
})

if db.get_wells_by_line(line_id):
    print("ℹ️ Линия 14 уже содержит скважины — сид пропускаем")
else:
    # (№, x, отметка устья, глубина, дата, содержание в пласт, лимитность)
    WELLS = [
        ("0", 0.0,  324.5, 3.6, "22.01.2021", 240, "РБС"),
        ("2", 20.0, 324.4, 4.0, "23.01.2021", 360, "н/п"),
        ("4", 40.0, 324.5, 4.8, "23.01.2021", 615, "РБС"),
        ("6", 60.0, 324.6, 4.8, "23.01.2021", 163, "РБС"),
        ("8", 80.0, 324.8, 5.2, "24.01.2021", 102, "РБС"),
    ]

    for num, x, surf, depth, date, au, limit in WELLS:
        bed_top = round(depth - 0.8, 1)                    # коренные: щебень/дресва 0,8 м
        pay_top = round(bed_top - (1.2 if depth <= 4.0 else 2.0), 1)

        layers = [
            # (от, до, литология, содержание, описание)
            (0.0, 0.4, "Торф", None, "Инт. 0,0–0,4 м торф"),
            (0.4, pay_top, "Песок", None, "песок раз/зерн., редкий гравий, дресва"),
            (pay_top, bed_top, "Галька", au, "галька, дресва, щебень; золото"),
            (bed_top, depth, "Щебень", None, "коренные: мелкий щебень, дресва"),
        ]

        pay_th = round(bed_top - pay_top, 1)
        mass_th = round(depth - 0.4, 1)

        well_id = db.add_well({
            "well_number": num, "line_id": line_id,
            "x_coordinate": x, "surface_elevation": surf, "total_depth": depth,
            "started_date": date, "ended_date": date, "status": "остановлена",
            "bedrock_character": "Мелкий щебень, дресва", "bedrock_drilled": 0.8,
            "frozen_1_from": 0.0, "frozen_1_to": depth,
            "thaw_1_from": None, "thaw_1_to": None,
            "diam_start": 152.0, "diam_final": 133.0,
            "rig_name": "УРБ-50",
            "mass_thickness": mass_th,
            "avg_content_plast": float(au),
            "avg_content_massa": round(au * pay_th / mass_th),
            "limitnost": limit,
        })

        for d_from, d_to, lith, gold, desc in layers:
            db.add_layer({
                "well_id": well_id, "depth_from": d_from, "depth_to": d_to,
                "lithology": lith, "gold_content": gold, "description": desc,
                "frozen_note": "мерзлота",
            })
        print(f"✅ Скважина №{num}: глубина {depth} м, отметка {surf}")

    print("🎉 Линия 14 (руч. Тёплый) загружена")