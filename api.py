import io
import os
import re
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from database import Database
from visualization import CrossSectionPlotter
from patterns import PATTERN_REGISTRY
import excel_io

app = FastAPI(
    title="Geology Information System API",
    description="API для управления геологическими данными бурения",
    version="1.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = Database()
plotter = CrossSectionPlotter()


@app.on_event("startup")
def startup_event():
    db.create_tables()
    print("✅ База данных инициализирована")


def _clean(model) -> dict:
    return {k: v for k, v in model.model_dump().items() if v is not None}


# ================= МОДЕЛИ =================
class LineCreate(BaseModel):
    line_number: str
    river_name: Optional[str] = None
    azimuth: Optional[str] = None
    note: Optional[str] = None
    description: Optional[str] = None
    year: Optional[str] = None
    valley_type: Optional[str] = None
    valley_name: Optional[str] = None
    tributary_side: Optional[str] = None
    tributary_name: Optional[str] = None
    distance_from_mouth: Optional[float] = None
    ref_line: Optional[str] = None
    ref_line_distance: Optional[float] = None
    otk_x_from: Optional[float] = None
    otk_x_to: Optional[float] = None
    otk_label: Optional[str] = None


class WellCreate(BaseModel):
    well_number: str
    line_id: int
    x_coordinate: float
    surface_elevation: float
    total_depth: float
    visual_result: Optional[str] = None
    started_date: Optional[str] = None
    ended_date: Optional[str] = None
    location_type: Optional[str] = None
    terrace_side: Optional[str] = None
    distance_from_riverbed: Optional[float] = None
    bedrock_character: Optional[str] = None
    bedrock_drilled: Optional[float] = None
    thaw_1_from: Optional[float] = None
    thaw_1_to: Optional[float] = None
    thaw_2_from: Optional[float] = None
    thaw_2_to: Optional[float] = None
    frozen_1_from: Optional[float] = None
    frozen_1_to: Optional[float] = None
    frozen_2_from: Optional[float] = None
    frozen_2_to: Optional[float] = None
    status: Optional[str] = None
    water_level: Optional[float] = None
    water_flow: Optional[float] = None
    bashmak_outer: Optional[float] = None
    bashmak_inner: Optional[float] = None
    diam_start: Optional[float] = None
    diam_final: Optional[float] = None
    diam_core: Optional[float] = None
    core_recovery: Optional[float] = None
    rig_name: Optional[str] = None
    zhelonka: Optional[str] = None
    cavernomer: Optional[str] = None
    mass_thickness: Optional[float] = None
    avg_content_plast: Optional[float] = None
    avg_content_massa: Optional[float] = None
    limitnost: Optional[str] = None


class LayerCreate(BaseModel):
    well_id: int
    depth_from: float
    depth_to: float
    lithology: str
    hatch_pattern: Optional[str] = None
    gold_content: Optional[float] = None
    description: Optional[str] = None
    volume: Optional[float] = None
    category: Optional[str] = None
    frozen_note: Optional[str] = None


class PatternUpdate(BaseModel):
    lithology: str
    hatch: str


# ================= ОБЩЕЕ =================
@app.get("/")
def read_root():
    return {"message": "Geology API is running", "docs": "/docs"}


# ================= ЛИНИИ =================
@app.get("/api/lines")
def get_lines():
    return db.get_all_lines()


@app.post("/api/lines")
def create_line(line: LineCreate):
    try:
        data = _clean(line)
        return {"id": db.add_line(data), "message": f"Линия {line.line_number} создана"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ================= СКВАЖИНЫ =================
@app.get("/api/lines/{line_number}/wells")
def get_wells(line_number: str):
    line = db.get_line_by_number(line_number)
    if not line:
        raise HTTPException(status_code=404, detail="Линия не найдена")
    return db.get_wells_by_line(line['id'])


@app.post("/api/wells")
def create_well(well: WellCreate):
    try:
        data = _clean(well)
        # если скважина с таким номером уже есть в линии — обновляем, а не дублируем
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM wells WHERE well_number = ? AND line_id = ?",
                        (well.well_number, well.line_id))
            row = cur.fetchone()
        if row:
            existing_id = row["id"]
            db.update_well(existing_id, {k: v for k, v in data.items() if k != "line_id"})
            return {"id": existing_id, "message": f"Скважина {well.well_number} обновлена"}
        return {"id": db.add_well(data), "message": f"Скважина {well.well_number} создана"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/wells/{well_id}")
def update_well(well_id: int, well: WellCreate):
    try:
        data = {k: v for k, v in _clean(well).items() if k != "line_id"}
        db.update_well(well_id, data)
        return {"message": "Скважина обновлена"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/wells/{well_id}")
def delete_well(well_id: int):
    try:
        db.delete_well(well_id)
        return {"message": "Скважина удалена"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ================= СЛОИ =================
@app.get("/api/wells/{well_id}/layers")
def get_layers(well_id: int):
    return db.get_layers_by_well(well_id)


@app.post("/api/layers")
def create_layer(layer: LayerCreate):
    try:
        data = _clean(layer)
        layer_id = db.add_layer(data)
        return {"id": layer_id, "message": "Слой создан"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/layers/well/{well_id}")
def delete_well_layers(well_id: int):
    try:
        db.delete_layers_by_well(well_id)
        return {"message": "Слои удалены"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ================= ШТРИХОВКИ (Приложение 5) =================
@app.get("/api/patterns")
def get_patterns():
    return db.get_lithology_patterns()


@app.get("/api/patterns/full")
def get_patterns_full():
    return db.get_lithology_patterns_full()


@app.put("/api/patterns")
def update_pattern(p: PatternUpdate):
    db.upsert_pattern(p.lithology, p.hatch)
    return {"message": f"Штриховка «{p.lithology}» → {p.hatch}"}


@app.get("/api/pattern-registry")
def get_pattern_registry():
    return PATTERN_REGISTRY


@app.post("/api/patterns/image")
async def upload_pattern_image(lithology: str, file: UploadFile = File(...)):
    os.makedirs("patterns", exist_ok=True)
    safe = re.sub(r"[^\w-]", "_", lithology).strip("_").lower()
    filename = f"{safe or 'pattern'}.png"
    path = f"patterns/{filename}"
    with open(path, "wb") as f:
        f.write(await file.read())
    code = f"img:{path}"
    db.upsert_pattern(lithology, code)
    return {"message": f"Картинка сохранена, «{lithology}» присвоен код {code}", "code": code}


# ================= ВИЗУАЛИЗАЦИЯ =================
@app.get("/api/lines/{line_number}/cross-section")
def get_cross_section(line_number: str):
    data = db.get_line_cross_section(line_number)
    if not data:
        raise HTTPException(status_code=404, detail="Линия не найдена")
    return data


@app.get("/api/lines/{line_number}/cross-section/image")
def get_cross_section_image(line_number: str, format: str = "png",
                            scale_h: Optional[float] = None,
                            scale_v: Optional[float] = None,
                            tick: float = 0.4):
    data = db.get_line_cross_section(line_number)
    if not data:
        raise HTTPException(status_code=404, detail="Линия не найдена")

    png_bytes, pdf_bytes = plotter.plot_cross_section(
        data, patterns=db.get_lithology_patterns(),
        scale_h=scale_h, scale_v=scale_v, tick_interval=tick)

    if png_bytes is None:
        raise HTTPException(status_code=400, detail="Нет данных для построения")

    if format.lower() == "pdf":
        return {"content": pdf_bytes.hex(),
                "filename": f"line_{line_number}_cross_section.pdf", "format": "pdf"}
    return {"content": png_bytes.hex(),
            "filename": f"line_{line_number}_cross_section.png", "format": "png"}


@app.post("/api/lines/{line_number}/generate")
def generate_cross_section(line_number: str,
                           scale_h: Optional[float] = None,
                           scale_v: Optional[float] = None,
                           tick: float = 0.4):
    data = db.get_line_cross_section(line_number)
    if not data:
        raise HTTPException(status_code=404, detail="Линия не найдена")

    save_path = f"output/line_{line_number}_cross_section"
    plotter.plot_cross_section(data, patterns=db.get_lithology_patterns(),
                               save_path=save_path,
                               scale_h=scale_h, scale_v=scale_v, tick_interval=tick)
    return {"message": "Разрез сгенерирован",
            "files": [f"{save_path}.png", f"{save_path}.pdf"]}


# ================= EXCEL =================
@app.get("/api/lines/{line_number}/excel")
def export_excel(line_number: str):
    buf = excel_io.export_line_excel(db, line_number)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=line_{line_number}.xlsx"},
    )


@app.post("/api/import/excel")
async def import_excel(file: UploadFile = File(...)):
    try:
        n = excel_io.import_excel(db, io.BytesIO(await file.read()))
        return {"imported_rows": n}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))