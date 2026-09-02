import pandas as pd
from io import BytesIO


def export_line_excel(db, line_number: str) -> BytesIO:
    """Экспорт данных линии в Excel (плоская таблица интервалов)"""
    data = db.get_line_cross_section(line_number)
    rows = []
    if data:
        for wid, w in sorted(data["wells_data"].items(), key=lambda kv: kv[1]["x"]):
            for l in w["layers"]:
                rows.append({
                    "line": line_number,
                    "well": wid,
                    "x": w["x"],
                    "mouth_elevation": w["surface"],
                    "total_depth": w["depth"],
                    "visual": w.get("visual") or "",
                    "depth_from": l["z_from"],
                    "depth_to": l["z_to"],
                    "lithology": l["lith"],
                    "gold": l["au"] if l["au"] is not None else "",
                })
    buf = BytesIO()
    pd.DataFrame(rows).to_excel(buf, index=False)
    buf.seek(0)
    return buf


def import_excel(db, buf) -> int:
    """Импорт плоской таблицы Excel в БД. Возвращает число импортированных интервалов."""
    df = pd.read_excel(buf)
    required = {"line", "well", "x", "mouth_elevation", "total_depth",
                "depth_from", "depth_to", "lithology"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"В файле нет колонок: {', '.join(sorted(missing))}")

    count = 0
    for (line_num, well_num), grp in df.groupby(["line", "well"], sort=True):
        line_id = db.add_line(str(line_num))
        first = grp.iloc[0]
        well_id = db.add_well(
            well_number=str(well_num),
            line_id=line_id,
            x_coordinate=float(first["x"]),
            surface_elevation=float(first["mouth_elevation"]),
            total_depth=float(first["total_depth"]),
            visual_result=str(first["visual"]) if str(first["visual"]) not in ("", "nan") else None,
        )
        for _, r in grp.sort_values("depth_from").iterrows():
            gold = r["gold"]
            gold_val = float(gold) if str(gold) not in ("", "nan") else None
            db.add_layer(
                well_id=well_id,
                depth_from=float(r["depth_from"]),
                depth_to=float(r["depth_to"]),
                lithology=str(r["lithology"]),
                hatch_pattern=None,
                gold_content=gold_val,
            )
            count += 1
    return count