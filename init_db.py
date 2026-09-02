import os
from database import Database

# ВНИМАНИЕ: демо-скрипт удаляет существующую БД и создаёт заново
if os.path.exists("geological_data.db"):
    os.remove("geological_data.db")

db = Database()
db.create_tables()

# ================= ЛИНИЯ 91 (р. Озёрный) =================
line91 = db.add_line("91", "р. Озёрный", azimuth=None, note=None,
                     description="Геоэксплуатационный разрез")

wells91 = {
    10: dict(x=10, surf=105, depth=50, visual="ЗНК", layers=[
        (0, 4, "Торф", None), (4, 22, "Песок", 1.2), (22, 48, "Галька", 4.5), (48, 50, "Глина", None)]),
    13: dict(x=25, surf=103, depth=48, visual="СЛ", layers=[
        (0, 5, "Торф", None), (5, 25, "Песок", 0.8), (25, 45, "Галька", 3.1), (45, 48, "Глина", None)]),
    16: dict(x=40, surf=107, depth=50, visual="РБС", layers=[
        (0, 6, "Торф", None), (6, 20, "Песок", 0.5), (20, 44, "Галька", 6.2), (44, 50, "Глина", None)]),
    19: dict(x=55, surf=104, depth=50, visual="Пыль", layers=[
        (0, 3, "Торф", None), (3, 18, "Песок", 1.5), (18, 48, "Галька", 2.8), (48, 50, "Глина", None)]),
    20: dict(x=68, surf=106, depth=50, visual="ЗНК", layers=[
        (0, 4, "Торф", None), (4, 21, "Песок", 1.1), (21, 47, "Галька", 3.7), (47, 50, "Глина", None)]),
    21: dict(x=80, surf=105, depth=50, visual="СЛ", layers=[
        (0, 5, "Торф", None), (5, 23, "Песок", 0.9), (23, 49, "Галька", 2.4), (49, 50, "Глина", None)]),
}

for num, wd in wells91.items():
    well_id = db.add_well(str(num), line91, wd["x"], wd["surf"], wd["depth"], wd["visual"],
                          "22.06.16", "22.06.16")
    for d_from, d_to, lith, au in wd["layers"]:
        db.add_layer(well_id, d_from, d_to, lith, None, au)
    print(f"✅ Скважина №{num}")

# ================= ЛИНИЯ 2 (руч. Безымянный, пример заказчика) =================
line2 = db.add_line("2", "руч. Безымянный", azimuth="154°",
                    note="Линия пройдена в мерзлоте")

wells2 = {
    0: dict(x=0,  surf=280.0, depth=8.0,  visual="СЛ"),
    2: dict(x=20, surf=279.0, depth=10.0, visual="ЗНК"),
    4: dict(x=40, surf=281.0, depth=12.0, visual="ЗНК"),
    6: dict(x=60, surf=278.0, depth=9.0,  visual="Пыль"),
    8: dict(x=80, surf=280.0, depth=8.0,  visual="СЛ"),
}

for num, wd in wells2.items():
    well_id = db.add_well(str(num), line2, wd["x"], wd["surf"], wd["depth"], wd["visual"])
    layers = [
        (0.0, 0.8, "Торф", None),
        (0.8, 4.0, "Песок", None),
        (4.0, 7.0, "Галька", 72 if num == 4 else None),  # «выносим 72 на глубине 4,0 м»
        (7.0, wd["depth"], "Глина", None),
    ]
    for d_from, d_to, lith, au in layers:
        db.add_layer(well_id, d_from, d_to, lith, None, au)
    print(f"✅ Скважина №{num}")

print("\n🎉 База данных готова: линии 91 и 2")