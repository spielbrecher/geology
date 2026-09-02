import os
import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Геологическая ИС", page_icon="🌍", layout="wide")

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.markdown('<h1 style="text-align:center; color:#2c5282;">🌍 Геологическая информационная система</h1>',
            unsafe_allow_html=True)
st.markdown('<p style="text-align:center; color:#4a5568;">Оцифровка журналов бурения и построение литологических разрезов</p>',
            unsafe_allow_html=True)
st.markdown("""
<style>
/* компактные поля формы: высота ~2rem, шрифт мельче, влезают 5–6 знаков */
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input {
    font-size: .82rem !important;
    padding: .18rem .45rem !important;
    height: 2.0rem !important;
    min-height: 0 !important;
}
div[data-testid="stSelectbox"] div[role="combobox"] {
    font-size: .82rem !important;
    padding: .18rem .45rem !important;
    min-height: 2.0rem !important;
}
/* убираем стрелки у числовых полей — становятся узкими и табличными */
div[data-testid="stNumberInputSteps"] { display: none !important; }
</style>
""", unsafe_allow_html=True)
FALLBACK_REGISTRY = {
    "grass": "Почвенно-растительный слой", "vlines": "Торф (верт. линии)",
    "hdash_sparse": "Ил", "plus": "Лед", "tildes": "Глина (тильды)",
    "dots": "Песок (точки)", "ellipses_small": "Галька", "ellipses_large": "Валуны",
    "triangles": "Дресва", "rects": "Щебень", "x_dots": "Диорит-порфириты",
    "dots_rows": "Песчаники", "hdash_rows": "Алевролиты",
}


def _idx(options, value, default=0):
    try:
        return options.index(value)
    except (ValueError, TypeError):
        return default


def _v(x, d=0.0):
    return d if x is None else float(x)


# ================================================================
# БОКОВАЯ ПАНЕЛЬ
# ================================================================
with st.sidebar:
    st.header("📋 Управление данными")

    try:
        lines = requests.get(f"{API_URL}/api/lines", timeout=5).json()
        patterns = requests.get(f"{API_URL}/api/patterns", timeout=5).json()
    except Exception:
        st.error("❌ Не удалось подключиться к API (запустите uvicorn api:app)")
        st.stop()

    if lines:
        line_options = {f"Линия {l['line_number']} — {l.get('river_name') or ''}": l['line_number']
                        for l in lines}
        selected_label = st.selectbox("Выберите линию", list(line_options.keys()), key="sel_line")
        selected_line = line_options[selected_label]
    else:
        selected_line = None
        st.info("Нет созданных линий")

    st.divider()

    # ---------- НОВАЯ ЛИНИЯ (п.1–3 журнала) ----------
    with st.expander("➕ Новая линия"):
        with st.form("new_line_form"):
            new_line_num = st.text_input("Номер линии*", key="nl_num")
            new_year = st.text_input("Год операции (напр. 2021)", key="nl_year")
            new_river = st.text_input("Название для шапки разреза (напр. руч. Безымянный)", key="nl_river")
            new_valley_type = st.selectbox("Долина (п.1)", ["реки", "ручья"], key="nl_valley_type")
            new_valley_name = st.text_input("Долина — название", key="nl_valley_name")
            new_trib_side = st.selectbox("Притока", ["-", "правого", "левого"], key="nl_trib_side")
            new_trib_name = st.text_input("Приток — название (реки/ручья)", key="nl_trib_name")
            new_dist_mouth = st.number_input("Расстояние от устья, м (п.2)", 0.0, 100000.0, 0.0, 1.0, key="nl_dist_mouth")
            new_ref_line = st.text_input("От линии № (п.2)", key="nl_ref_line")
            new_ref_dist = st.number_input("Расстояние от линии, м", 0.0, 100000.0, 0.0, 1.0, key="nl_ref_dist")
            new_azimuth = st.text_input("Азимут буровой линии (п.3)", key="nl_azimuth")
            new_note = st.text_input("Примечание (напр. «Линия пройдена в мерзлоте»)", key="nl_note")
            new_otk_from = st.number_input("Отработка от, м (0 = нет)", 0.0, 100000.0, 0.0, 1.0, key="nl_otk_from")
            new_otk_to = st.number_input("Отработка до, м", 0.0, 100000.0, 0.0, 1.0, key="nl_otk_to")

            if st.form_submit_button("Создать линию"):
                if not new_line_num:
                    st.error("Укажите номер линии")
                else:
                    r = requests.post(f"{API_URL}/api/lines", json={
                        "line_number": new_line_num,
                        "river_name": new_river or None,
                        "azimuth": new_azimuth or None,
                        "note": new_note or None,
                        "year": new_year or None,
                        "valley_type": new_valley_type,
                        "valley_name": new_valley_name or None,
                        "tributary_side": new_trib_side if new_trib_side != "-" else None,
                        "tributary_name": new_trib_name or None,
                        "distance_from_mouth": new_dist_mouth or None,
                        "ref_line": new_ref_line or None,
                        "ref_line_distance": new_ref_dist or None,
                        "otk_x_from": new_otk_from if new_otk_to > new_otk_from else None,
                        "otk_x_to": new_otk_to if new_otk_to > new_otk_from else None,
                        "otk_label": "ОТРАБОТКА" if new_otk_to > new_otk_from else None,
                    })
                    if r.status_code == 200:
                        st.success(f"✅ Линия {new_line_num} создана")
                        st.rerun()
                    else:
                        st.error(f"❌ {r.json().get('detail')}")

    # ---------- РЕДАКТОР ШТРИХОВОК (Приложение 5) ----------
    with st.expander("⚙️ Условные обозначения (штриховки)"):
        try:
            reg = requests.get(f"{API_URL}/api/pattern-registry", timeout=5).json()
            registry = reg if isinstance(reg, dict) and "dots" in reg else FALLBACK_REGISTRY
        except Exception:
            registry = FALLBACK_REGISTRY

        full = requests.get(f"{API_URL}/api/patterns/full").json()
        codes = [c for c in registry if c != "img"]
        IMG_OPT = "🖼 Изображение из файла (img:...)"
        new_vals = {}

        for row in full:
            lith = row['lithology_type']
            current = row['hatch_pattern']
            is_img = current.startswith("img:")
            opts = codes + [IMG_OPT]
            default = len(codes) if is_img else _idx(codes, current, len(codes))
            choice = st.selectbox(lith, opts, index=default, key=f"pat_{lith}",
                                  format_func=lambda c: f"{c} — {registry.get(c, c)}")

            if choice == IMG_OPT:
                path = st.text_input(f"Код паттерна для «{lith}»",
                                     value=current if is_img else f"img:patterns/{lith.lower()}.png",
                                     key=f"imgpath_{lith}")
                upl = st.file_uploader(f"Или загрузите PNG для «{lith}»",
                                       type=["png"], key=f"upl_{lith}")
                if upl is not None and st.button(f"⬆️ Загрузить и присвоить «{lith}»",
                                                 key=f"uplbtn_{lith}"):
                    rr = requests.post(f"{API_URL}/api/patterns/image",
                                       params={"lithology": lith},
                                       files={"file": (upl.name, upl.getvalue(), "image/png")})
                    st.success(rr.json()["message"])
                    st.rerun()
                new_vals[lith] = path
            else:
                new_vals[lith] = choice

        if st.button("💾 Сохранить штриховки", key="btn_save_patterns"):
            changed = 0
            for row in full:
                lith = row['lithology_type']
                if new_vals[lith] != row['hatch_pattern']:
                    requests.put(f"{API_URL}/api/patterns",
                                 json={"lithology": lith, "hatch": new_vals[lith]})
                    changed += 1
            st.success(f"✅ Обновлено штриховок: {changed}")
            st.rerun()

    # ---------- МАСШТАБ ПЕЧАТИ И НАСЕЧКИ ----------
    with st.expander("📐 Масштаб печати и насечки"):
        st.caption("Типовые: гориз. 1:1000 (1 см = 10 м), верт. 1:100 (1 см = 1 м). "
                   "0 — автоматический размер листа.")
        sc_h = st.number_input("Горизонтальный, м в 1 см", 0.0, 100000.0, 0.0, 0.5, key="scale_h")
        sc_v = st.number_input("Вертикальный, м в 1 см", 0.0, 100000.0, 0.0, 0.5, key="scale_v")
        tick = st.number_input("Шаг насечек на скважинах, м", 0.1, 5.0, 0.4, 0.1, key="tick_int")
        st.session_state['scale_params'] = {
            **({"scale_h": sc_h} if sc_h > 0 else {}),
            **({"scale_v": sc_v} if sc_v > 0 else {}),
            "tick": tick,
        }

# ================================================================
# ОСНОВНОЙ КОНТЕНТ
# ================================================================
if not selected_line:
    st.info("👈 Создайте линию в боковой панели")
    st.stop()

line_num = selected_line
lith_names = list(patterns.keys())

tab1, tab2, tab3, tab4 = st.tabs(["📊 Данные", "📖 Журнал", "📈 Визуализация", "📥 Экспорт"])

# ================= ТАБ 1: ДАННЫЕ =================
with tab1:
    st.subheader(f"📊 Данные по линии {line_num}")
    wells = requests.get(f"{API_URL}/api/lines/{line_num}/wells").json()

    if wells:
        rename_map = {"well_number": "№ скв.", "x_coordinate": "X, м",
                      "surface_elevation": "Отметка устья, м", "total_depth": "Глубина, м",
                      "status": "Статус", "limitnost": "Лимитность", "rig_name": "Станок"}
        df = pd.DataFrame(wells)
        df = df[[c for c in rename_map.keys() if c in df.columns]]
        df = df.rename(columns=rename_map)
        st.dataframe(df, use_container_width=True)

        st.subheader("🔍 Детализация по скважинам")
        for well in wells:
            with st.expander(f"Скважина №{well['well_number']} "
                             f"(устье {_v(well['surface_elevation'])} м, "
                             f"глубина {_v(well['total_depth'])} м)"):
                layers = requests.get(f"{API_URL}/api/wells/{well['id']}/layers").json()
                if layers:
                    ldf = pd.DataFrame(layers)
                    lcols = ["depth_from", "depth_to", "lithology", "frozen_note",
                             "category", "gold_content", "volume", "description"]
                    ldf = ldf[[c for c in lcols if c in ldf.columns]]
                    st.dataframe(ldf, use_container_width=True)
                else:
                    st.info("Нет данных по слоям")
                if st.button(f"🗑️ Удалить скважину №{well['well_number']}",
                             key=f"del_{well['id']}"):
                    requests.delete(f"{API_URL}/api/wells/{well['id']}")
                    st.success("Скважина удалена")
                    st.rerun()
    else:
        st.info("Нет скважин. Перейдите на вкладку «Журнал».")

# ================= ТАБ 2: ЖУРНАЛ =================
with tab2:
    st.subheader("📖 Журнал документации скважины (как в бумажном бланке)")
    wells = requests.get(f"{API_URL}/api/lines/{line_num}/wells").json()
    opts = ["➕ Новая скважина"] + [f"№{w['well_number']} — редактировать" for w in wells]
    choice = st.selectbox("Скважина", opts, key="sel_well")
    ew = wells[opts.index(choice) - 1] if choice != opts[0] else None
    g = lambda k, d=None: (ew.get(k) if ew and ew.get(k) is not None else d)

    with st.form("journal_form"):
        st.markdown("**4.** Скважина расположена в русле / пойме / на террасе")
        c1, c2, c3, c4 = st.columns(4)
        well_number = c1.text_input("№ скважины*", value=g('well_number', ''), key="j_wellnum")
        loc_type = c2.selectbox("Расположение", ["-", "русло", "пойма", "терраса"],
                                index=_idx(["-", "русло", "пойма", "терраса"], g('location_type')),
                                key="j_loc")
        terr_side = c3.selectbox("Терраса (сторона)", ["-", "левой", "правой"],
                                 index=_idx(["-", "левой", "правой"], g('terrace_side')),
                                 key="j_terr")
        dist_river = c4.number_input("От русла, м", 0.0, 1000.0, _v(g('distance_from_riverbed')), 0.5,
                                     key="j_dist_river")

        st.markdown("**5–7.** Даты, отметка устья, глубина, статус")
        c1, c2, c3, c4 = st.columns(4)
        x_coord = c1.number_input("Расст. по линии, м*", 0.0, 10000.0, _v(g('x_coordinate')), 1.0,
                                  key="j_x")
        surface = c2.number_input("Отметка устья, м*", 0.0, 5000.0, _v(g('surface_elevation'), 100.0), 0.1,
                                  key="j_surf")
        total_depth = c3.number_input("Глубина, м*", 0.1, 500.0, _v(g('total_depth'), 10.0), 0.1,
                                      key="j_depth")
        status = c4.radio("**11.** Скважина", ["пройдена", "остановлена"],
                          index=0 if g('status', 'пройдена') == 'пройдена' else 1,
                          key="j_status")
        c1, c2 = st.columns(2)
        started = c1.text_input("Начата (дата)", value=g('started_date', ''), key="j_start")
        ended = c2.text_input("Окончена (дата)", value=g('ended_date', ''), key="j_end")

        st.markdown("**8–10.** Коренные породы / талый грунт / мерзлота")
        c1, c2 = st.columns(2)
        bedrock_char = c1.text_input("Характер коренных пород", value=g('bedrock_character', ''),
                                     key="j_bedrock_char")
        bedrock_dr = c2.number_input("Пройдено по ним, м", 0.0, 500.0, _v(g('bedrock_drilled')), 0.1,
                                     key="j_bedrock_dr")
        c1, c2, c3, c4 = st.columns(4)
        thaw1f = c1.number_input("Талый от, м", 0.0, 500.0, _v(g('thaw_1_from')), 0.1, key="j_thaw1f")
        thaw1t = c2.number_input("Талый до, м", 0.0, 500.0, _v(g('thaw_1_to')), 0.1, key="j_thaw1t")
        thaw2f = c3.number_input("Талый от, м (2)", 0.0, 500.0, _v(g('thaw_2_from')), 0.1, key="j_thaw2f")
        thaw2t = c4.number_input("Талый до, м (2)", 0.0, 500.0, _v(g('thaw_2_to')), 0.1, key="j_thaw2t")
        c1, c2, c3, c4 = st.columns(4)
        fr1f = c1.number_input("Мерзлота от, м", 0.0, 500.0, _v(g('frozen_1_from')), 0.1, key="j_fr1f")
        fr1t = c2.number_input("Мерзлота до, м", 0.0, 500.0, _v(g('frozen_1_to')), 0.1, key="j_fr1t")
        fr2f = c3.number_input("Мерзлота от, м (2)", 0.0, 500.0, _v(g('frozen_2_from')), 0.1, key="j_fr2f")
        fr2t = c4.number_input("Мерзлота до, м (2)", 0.0, 500.0, _v(g('frozen_2_to')), 0.1, key="j_fr2t")

        st.markdown("**12–16.** Вода, диаметры, станок")
        c1, c2, c3, c4 = st.columns(4)
        w_lev = c1.number_input("Уровень воды, м", 0.0, 100.0, _v(g('water_level')), 0.1, key="j_wlev")
        w_flow = c2.number_input("Дебит, л/сек", 0.0, 100.0, _v(g('water_flow')), 0.1, key="j_wflow")
        b_out = c3.number_input("Башмак наруж., мм", 0.0, 500.0, _v(g('bashmak_outer')), 1.0, key="j_bout")
        b_in = c4.number_input("Башмак внутр., мм", 0.0, 500.0, _v(g('bashmak_inner')), 1.0, key="j_bin")
        c1, c2, c3, c4 = st.columns(4)
        d_st = c1.number_input("Диам. начальный, мм", 0.0, 500.0, _v(g('diam_start')), 1.0, key="j_dst")
        d_fn = c2.number_input("Диам. по пласту, мм", 0.0, 500.0, _v(g('diam_final')), 1.0, key="j_dfn")
        d_cr = c3.number_input("Диам. керна, мм", 0.0, 500.0, _v(g('diam_core')), 1.0, key="j_dcr")
        cr_rec = c4.number_input("Выход керна, %", 0.0, 100.0, _v(g('core_recovery')), 1.0, key="j_crec")
        c1, c2, c3 = st.columns(3)
        rig = c1.text_input("Буровой станок", value=g('rig_name', ''), key="j_rig")
        zheln = c2.text_input("Желонки", value=g('zhelonka', ''), key="j_zheln")
        cav = c3.text_input("Каверномер", value=g('cavernomer', ''), key="j_cav")

        st.markdown("### Литологический разрез (проходы по 0,4 м)")
        old_layers = requests.get(f"{API_URL}/api/wells/{ew['id']}/layers").json() if ew else []
        n_pass = int(st.number_input("Число проходов", 1, 100,
                                     max(len(old_layers), int(round(total_depth / 0.4)) or 1),
                                     key="j_npass"))

        COLS = [0.9, 1.4, 2.4, 1.2, 0.7, 0.8, 0.9]
        # шапка таблицы
        h = st.columns(COLS)
        h[0].markdown("**Интервал, м**")
        h[1].markdown("**Литология**")
        h[2].markdown("**Описание (гр.5)**")
        h[3].markdown("**Талики/мерзл. (гр.6)**")
        h[4].markdown("**Кат.**")
        h[5].markdown("**Объем**")
        h[6].markdown("**Содерж.**")

        passes = []
        for i in range(n_pass):
            ol = old_layers[i] if i < len(old_layers) else {}
            d_from = round(i * 0.4, 1)
            d_to = min(round((i + 1) * 0.4, 1), total_depth)
            c = st.columns(COLS)
            c[0].markdown(f"{d_from}–{d_to}")
            lith = c[1].selectbox("Литология", lith_names,
                                  index=_idx(lith_names, ol.get('lithology'), _idx(lith_names, 'Песок')),
                                  key=f"jl_{i}", label_visibility="collapsed")
            desc = c[2].text_input("Описание разреза (гр.5)", value=ol.get('description') or '',
                                   key=f"jd_{i}", label_visibility="collapsed")
            fr_note = c[3].selectbox("Талики/мерзлота/водонос (гр.6)",
                                     ["-", "мерзлота", "талый", "водонос"],
                                     index=_idx(["-", "мерзлота", "талый", "водонос"], ol.get('frozen_note')),
                                     key=f"jf_{i}", label_visibility="collapsed")
            cat = c[4].selectbox("Катег. (гр.7)", ["-", "I", "II", "III"],
                                 index=_idx(["-", "I", "II", "III"], ol.get('category')),
                                 key=f"jc_{i}", label_visibility="collapsed")
            vol = c[5].number_input("Объем, см³ (гр.8)", 0.0, 100000.0, _v(ol.get('volume')), 1.0,
                                    key=f"jv_{i}", label_visibility="collapsed")
            au = c[6].number_input("Содерж., мг/м³", 0.0, 100000.0, _v(ol.get('gold_content')), 1.0,
                                   key=f"ja_{i}", label_visibility="collapsed")
            passes.append((d_from, d_to, lith, desc, fr_note, cat, vol, au))

        st.markdown("### Результаты подсчета")
        c1, c2, c3, c4 = st.columns(4)
        mass_th = c1.number_input("Мощность массы, м", 0.0, 500.0, _v(g('mass_thickness')), 0.1,
                                  key="j_mass_th")
        c_plast = c2.number_input("Сред. содерж. на пласт, мг/м³", 0.0, 100000.0, _v(g('avg_content_plast')), 1.0,
                                  key="j_c_plast")
        c_massa = c3.number_input("Сред. содерж. на массу, мг/м³", 0.0, 100000.0, _v(g('avg_content_massa')), 1.0,
                                  key="j_c_massa")
        limit = c4.selectbox("Лимитность", ["-", "РБС", "н/п"],
                             index=_idx(["-", "РБС", "н/п"], g('limitnost')),
                             key="j_limit")

        submitted = st.form_submit_button("💾 Сохранить журнал скважины")

    if submitted and well_number:
        payload = {
            "well_number": well_number,
            "line_id": next(l['id'] for l in lines if l['line_number'] == line_num),
            "x_coordinate": x_coord, "surface_elevation": surface, "total_depth": total_depth,
            "location_type": loc_type if loc_type != "-" else None,
            "terrace_side": terr_side if terr_side != "-" else None,
            "distance_from_riverbed": dist_river or None,
            "started_date": started or None, "ended_date": ended or None,
            "status": status,
            "bedrock_character": bedrock_char or None, "bedrock_drilled": bedrock_dr or None,
            "thaw_1_from": thaw1f or None, "thaw_1_to": thaw1t or None,
            "thaw_2_from": thaw2f or None, "thaw_2_to": thaw2t or None,
            "frozen_1_from": fr1f or None, "frozen_1_to": fr1t or None,
            "frozen_2_from": fr2f or None, "frozen_2_to": fr2t or None,
            "water_level": w_lev or None, "water_flow": w_flow or None,
            "bashmak_outer": b_out or None, "bashmak_inner": b_in or None,
            "diam_start": d_st or None, "diam_final": d_fn or None,
            "diam_core": d_cr or None, "core_recovery": cr_rec or None,
            "rig_name": rig or None, "zhelonka": zheln or None, "cavernomer": cav or None,
            "mass_thickness": mass_th or None, "avg_content_plast": c_plast or None,
            "avg_content_massa": c_massa or None,
            "limitnost": limit if limit != "-" else None,
        }
        if ew:
            r = requests.put(f"{API_URL}/api/wells/{ew['id']}", json=payload)
            well_id = ew['id']
        else:
            r = requests.post(f"{API_URL}/api/wells", json=payload)
            well_id = r.json()['id']

        if r.status_code == 200:
            requests.delete(f"{API_URL}/api/layers/well/{well_id}")
            for d_from, d_to, lith, desc, fr_note, cat, vol, au in passes:
                if d_to <= d_from:
                    continue
                requests.post(f"{API_URL}/api/layers", json={
                    "well_id": well_id, "depth_from": d_from, "depth_to": d_to,
                    "lithology": lith, "gold_content": au or None,
                    "description": desc or None,
                    "frozen_note": fr_note if fr_note != "-" else None,
                    "category": cat if cat != "-" else None,
                    "volume": vol or None,
                })
            st.success(f"✅ Журнал скважины №{well_number} сохранён")
            st.rerun()
        else:
            st.error(f"❌ {r.json().get('detail')}")

# ================= ТАБ 3: ВИЗУАЛИЗАЦИЯ =================
with tab3:
    st.subheader("📈 Литологический разрез")
    if st.button("🔄 Построить разрез", type="primary", key="btn_build"):
        with st.spinner("Генерация разреза..."):
            params = {"format": "png", **st.session_state.get('scale_params', {})}
            r = requests.get(f"{API_URL}/api/lines/{line_num}/cross-section/image", params=params)
            if r.status_code == 200:
                st.session_state['png_bytes'] = bytes.fromhex(r.json()['content'])
            else:
                st.error("❌ Ошибка генерации (нет скважин?)")
    if st.session_state.get('png_bytes'):
        st.image(st.session_state['png_bytes'], use_container_width=True)

# ================= ТАБ 4: ЭКСПОРТ =================
with tab4:
    st.subheader("📥 Экспорт / импорт")
    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("🖼 PNG", type="primary", key="btn_png"):
            params = {"format": "png", **st.session_state.get('scale_params', {})}
            r = requests.get(f"{API_URL}/api/lines/{line_num}/cross-section/image", params=params)
            st.session_state['dl_png'] = bytes.fromhex(r.json()['content'])
            st.session_state['dl_png_name'] = r.json()['filename']
        if st.session_state.get('dl_png'):
            st.download_button("💾 Сохранить PNG", st.session_state['dl_png'],
                               file_name=st.session_state['dl_png_name'], mime="image/png",
                               key="dl_png")

    with c2:
        if st.button("📄 PDF", type="primary", key="btn_pdf"):
            params = {"format": "pdf", **st.session_state.get('scale_params', {})}
            r = requests.get(f"{API_URL}/api/lines/{line_num}/cross-section/image", params=params)
            st.session_state['dl_pdf'] = bytes.fromhex(r.json()['content'])
            st.session_state['dl_pdf_name'] = r.json()['filename']
        if st.session_state.get('dl_pdf'):
            st.download_button("💾 Сохранить PDF", st.session_state['dl_pdf'],
                               file_name=st.session_state['dl_pdf_name'], mime="application/pdf",
                               key="dl_pdf")

    with c3:
        if st.button("📗 Excel", type="primary", key="btn_xlsx"):
            r = requests.get(f"{API_URL}/api/lines/{line_num}/excel")
            st.session_state['dl_xlsx'] = r.content
        if st.session_state.get('dl_xlsx'):
            st.download_button("💾 Сохранить Excel", st.session_state['dl_xlsx'],
                               file_name=f"line_{line_num}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               key="dl_xlsx")

    st.divider()
    uploaded = st.file_uploader("📤 Импорт из Excel", type=["xlsx"], key="upl_xlsx")
    if uploaded is not None:
        if st.button("⬆️ Загрузить в базу", key="btn_import_xlsx"):
            r = requests.post(f"{API_URL}/api/import/excel",
                              files={"file": (uploaded.name, uploaded.getvalue())})
            if r.status_code == 200:
                st.success(f"✅ Импортировано интервалов: {r.json()['imported_rows']}")
                st.rerun()
            else:
                st.error(f"❌ {r.json().get('detail')}")