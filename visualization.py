import io, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from typing import Dict, List, Optional

from patterns import PatternFiller

LITH_ABBR = {
    "Почвенно-растительный слой": "почв", "Торф": "т", "Ил": "и", "Лед": "л",
    "Глина": "гл", "Песок": "пс", "Галька": "гк", "Валуны": "в",
    "Дресва": "др", "Щебень": "щб", "Диорит-порфириты": "дп",
    "Песчаники": "псч", "Алевролиты": "ал",
}


def _num_key(w):
    try: return (0, int(w))
    except (ValueError, TypeError):
        try: return (0, float(w))
        except (ValueError, TypeError): return (1, 0)


def _fmt(v, digits=1):
    if v in (None, ""): return ""
    return f"{float(v):.{digits}f}".replace(".", ",")


class CrossSectionPlotter:
    def __init__(self):
        self.filler = PatternFiller()

    # ================= КОРРЕЛЯЦИЯ СЛОЁВ МЕЖДУ ПАРОЙ СКВАЖИН =================
    def _correlate_pair(self, w1, w2):
        """
        Возвращает список спеков (kind, a, b):
        full          — одна литология, есть перекрытие → полигон через весь пролёт
        lateral_left/
        lateral_right — разная литология на одном уровне → обрыв на середине пролёта
        pinch_left/
        pinch_right   — слоя нет у соседа → выклинивание клином
        """
        specs = []
        L1, L2 = w1["layers"], w2["layers"]
        for l in L1:
            l["_t"], l["_b"] = w1["surface"] - l["z_from"], w1["surface"] - l["z_to"]
        for l in L2:
            l["_t"], l["_b"] = w2["surface"] - l["z_from"], w2["surface"] - l["z_to"]

        def ov(a, b):
            return min(a["_t"], b["_t"]) - max(a["_b"], b["_b"]) > 0

        used2 = set()
        for a in L1:
            # 1) та же литология с перекрытием
            hit = next((j for j, b in enumerate(L2)
                        if j not in used2 and b["lith"] == a["lith"] and ov(a, b)), None)
            if hit is not None:
                used2.add(hit)
                specs.append(("full", a, L2[hit]))
                continue
            # 2) другая литология на том же уровне → латеральная смена
            hit = next((j for j, b in enumerate(L2)
                        if j not in used2 and ov(a, b)), None)
            if hit is not None:
                used2.add(hit)
                specs.append(("lateral_left", a, L2[hit]))
                specs.append(("lateral_right", a, L2[hit]))
            else:
                # 3) выклинивание влево-направо
                specs.append(("pinch_left", a, None))
        for j, b in enumerate(L2):
            if j not in used2:
                specs.append(("pinch_right", None, b))
        return specs

    # ================= ПОСТРОЕНИЕ =================
    def plot_cross_section(self, data: Dict, patterns: Optional[Dict[str, str]] = None,
                           save_path: Optional[str] = None, spacing: float = 1.5,
                           tick_interval: float = 0.4,
                           scale_h: Optional[float] = None,
                           scale_v: Optional[float] = None):
        patterns = patterns or {}
        line = data['line']; wells_data = data['wells_data']
        if not wells_data: return None, None

        well_ids = sorted(wells_data.keys(), key=_num_key)
        xs = [wells_data[w]['x'] for w in well_ids]
        max_surf = max(wells_data[w]['surface'] for w in well_ids)
        min_elev = min(wells_data[w]['surface'] - wells_data[w]['depth'] for w in well_ids)
        min_x, max_x = min(xs), max(xs)

        x_lo, x_hi = min_x - 14, max_x + 8
        y_lo, y_hi = min_elev - 6, max_surf + 12
        x_span, y_span = x_hi - x_lo, y_hi - y_lo

        strict = bool(scale_h) and bool(scale_v)
        if strict:
            ax_w_cm = x_span / scale_h
            ax_h_cm = y_span / scale_v
            left, right, top = 1.2, 0.8, 0.6
            tbl_h, gap, bm = 6.0, 1.0, 0.6
            fig_w = left + ax_w_cm + right
            fig_h = top + ax_h_cm + gap + tbl_h + bm
            fig = plt.figure(figsize=(fig_w / 2.54, fig_h / 2.54))
            ax = fig.add_axes([left / fig_w, (bm + tbl_h + gap) / fig_h,
                               ax_w_cm / fig_w, ax_h_cm / fig_h])
            ax_t = fig.add_axes([left / fig_w, bm / fig_h, ax_w_cm / fig_w, tbl_h / fig_h])
        else:
            fig = plt.figure(figsize=(16, 12))
            gs = GridSpec(2, 1, height_ratios=[3, 1.15], hspace=0.22)
            ax = fig.add_subplot(gs[0])
            ax_t = fig.add_subplot(gs[1])

        ax.set_facecolor('white')
        for s in ax.spines.values(): s.set_visible(False)
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_xlim(x_lo, x_hi)
        ax.set_ylim(y_lo, y_hi)

        # ===== ШКАЛА-РЕЙКА СЛЕВА =====
        y0, y1 = int(np.floor(min_elev)), int(np.ceil(max_surf))
        bar_x = min_x - 10
        for e in range(y0, y1):
            ax.add_patch(mpatches.Rectangle((bar_x, e), 1.4, 1,
                         fc='k' if (e - y0) % 2 == 0 else 'w', ec='k', lw=0.6, zorder=4))
        lbl_step = max(1, round((y1 - y0) / 18))
        for e in range(y0, y1 + 1, lbl_step):
            ax.text(bar_x - 0.6, e, str(e), ha='right', va='center', fontsize=7)

        # ===== ШАПКА =====
        cx = (min_x + max_x) / 2
        ax.text(cx, max_surf + 7,
                f"{line.get('river_name') or ''}\nЛиния {line['line_number']} "
                f"({line.get('year') or '20__'} г)\nАзимут - {line.get('azimuth') or '—'}°",
                ha='center', va='bottom', fontsize=11)
        ax.annotate("", xy=(cx + 14, max_surf + 10.5), xytext=(cx + 4, max_surf + 10.5),
                    arrowprops=dict(arrowstyle="->", lw=1))

        # ===== СЛОИ С ВЫКЛИНИВАНИЕМ И СМЕНОЙ ЛИТОЛОГИИ =====
        for i in range(len(well_ids) - 1):
            w1 = wells_data[well_ids[i]]
            w2 = wells_data[well_ids[i + 1]]
            x1, x2 = w1["x"], w2["x"]
            xm = (x1 + x2) / 2
            for kind, a, b in self._correlate_pair(w1, w2):
                if kind == "full":
                    poly = [(x1, a["_t"]), (x2, b["_t"]), (x2, b["_b"]), (x1, a["_b"])]
                    src = a
                elif kind == "lateral_left":
                    poly = [(x1, a["_t"]), (xm, a["_t"]), (xm, a["_b"]), (x1, a["_b"])]
                    src = a
                elif kind == "lateral_right":
                    poly = [(xm, b["_t"]), (x2, b["_t"]), (x2, b["_b"]), (xm, b["_b"])]
                    src = b
                elif kind == "pinch_left":
                    mid = (a["_t"] + a["_b"]) / 2
                    poly = [(x1, a["_t"]), (xm, mid), (x1, a["_b"])]
                    src = a
                else:  # pinch_right
                    mid = (b["_t"] + b["_b"]) / 2
                    poly = [(x2, b["_t"]), (xm, mid), (x2, b["_b"])]
                    src = b
                code = src.get("hatch") or patterns.get(src["lith"], "dots")
                self.filler.fill(ax, poly, code, spacing=spacing)

        # ===== ОТРАБОТКА =====
        if line.get('otk_x_from') is not None and line.get('otk_x_to') is not None:
            for xx in (line['otk_x_from'], line['otk_x_to']):
                ax.plot([xx, xx], [min_elev + 1, max_surf - 1], 'r-', lw=0.8, zorder=5)
                self._flag(ax, xx, max_surf + 0.5)
            ax.text(line['otk_x_from'] - 2.5, (y0 + y1) / 2,
                    line.get('otk_label') or 'ОТРАБОТКА',
                    rotation=90, va='center', ha='center', fontsize=8)

        # ===== СКВАЖИНЫ + НАСЕЧКИ 0,4 м =====
        tw = x_span * 0.004
        pay_xs, pay_t, pay_b = [], [], []
        for i, wid in enumerate(well_ids):
            w = wells_data[wid]; x, surf = w["x"], w["surface"]
            if i > 0:
                pw = wells_data[well_ids[i - 1]]
                ax.plot([pw["x"], x], [pw["surface"], surf], 'k-', lw=1.2, zorder=4)
            ax.plot([x, x], [surf, surf - w["depth"]], 'k-', lw=0.9, zorder=4)

            d, k = 0.0, 0
            while d <= w["depth"] + 1e-9:
                wl = tw * 2 if k % 5 == 0 else tw
                ax.plot([x - wl, x + wl], [surf - d, surf - d], 'k-', lw=0.5, zorder=4)
                d += tick_interval; k += 1

            ax.text(x, surf + 0.6, str(wid), ha='center', va='bottom', fontsize=9, zorder=6)
            ax.text(x, surf - w["depth"] - 0.6, _fmt(w["depth"]),
                    ha='center', va='top', fontsize=7, zorder=6)

            for l in w["layers"]:
                mid = surf - (l["z_from"] + l["z_to"]) / 2
                if l["z_to"] - l["z_from"] > 0.7:
                    ax.text(x + 0.7, mid, LITH_ABBR.get(l["lith"], l["lith"][:2].lower()),
                            fontsize=7, va='center', zorder=6)
                if l.get("au") is not None:
                    ax.text(x + 1.8, surf - l["z_from"], f"{l['au']:g}/{_fmt(l['z_from'])}",
                            color='r', fontsize=7, va='center', zorder=6)

            pays = [l for l in w["layers"] if l.get("au") is not None]
            if pays:
                pay_xs.append(x)
                pay_t.append(surf - pays[0]["z_from"])
                pay_b.append(surf - pays[-1]["z_to"])

        # ===== КРАСНЫЙ КОНТУР =====
        if len(pay_xs) >= 2:
            ax.plot(pay_xs, pay_t, 'r-', lw=1, zorder=5)
            ax.plot(pay_xs, pay_b, 'r-', lw=1, zorder=5)
            ax.plot([pay_xs[0], pay_xs[0]], [pay_t[0], pay_b[0]], 'r-', lw=1, zorder=5)
            ax.plot([pay_xs[-1], pay_xs[-1]], [pay_t[-1], pay_b[-1]], 'r-', lw=1, zorder=5)

        # ===== ТАБЛИЦА-ЛЕГЕНДА =====
        ax_t.axis('off')
        rows = self._table_rows(wells_data, well_ids)
        t = ax_t.table(cellText=[r[1:] for r in rows], rowLabels=[r[0] for r in rows],
                       colLabels=[str(w) for w in well_ids], loc='center', cellLoc='center')
        t.auto_set_font_size(False); t.set_fontsize(8); t.scale(1, 1.6)
        for (r, c), cell in t.get_celld().items():
            cell.set_edgecolor('k'); cell.set_linewidth(0.6)
            if r == 0: cell.set_text_props(fontweight='bold')

        if strict:
            fig.text(0.5, 0.005,
                     f"Масштаб: горизонтальный 1 см = {scale_h:g} м (1:{int(scale_h * 100)}); "
                     f"вертикальный 1 см = {scale_v:g} м (1:{int(scale_v * 100)})",
                     ha='center', fontsize=8)

        png_buf, pdf_buf = io.BytesIO(), io.BytesIO()
        bbox = None if strict else 'tight'
        fig.savefig(png_buf, format='png', dpi=300, bbox_inches=bbox)
        fig.savefig(pdf_buf, format='pdf', bbox_inches=bbox)
        plt.close(fig)

        if save_path:
            os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
            open(f"{save_path}.png", 'wb').write(png_buf.getvalue())
            open(f"{save_path}.pdf", 'wb').write(pdf_buf.getvalue())
        return png_buf.getvalue(), pdf_buf.getvalue()

    def _flag(self, ax, x, y):
        ax.plot([x, x], [y, y + 2.6], 'r-', lw=0.8, zorder=5)
        ax.add_patch(mpatches.Polygon([(x, y + 2.6), (x + 1.8, y + 2.1), (x, y + 1.6)],
                                      fc='w', ec='r', lw=0.8, zorder=5))

    def _th(self, w, lith):
        return sum(l["z_to"] - l["z_from"] for l in w["layers"] if l["lith"] == lith)

    def _table_rows(self, wd, ids):
        get = lambda w, k: w.get(k)
        rows = [["Номера скважин"] + [str(w) for w in ids]]
        rows.append(["Расстояния между скважинами, м"] + [""] +
                    [f"{int(wd[ids[i]]['x'] - wd[ids[i-1]]['x'])}" for i in range(1, len(ids))])
        rows.append(["Отметки устья скважин, м"] + [_fmt(wd[w]['surface']) for w in ids])
        rows.append(["Глубина скважин, м"] + [_fmt(wd[w]['depth']) for w in ids])
        rows.append(["Мощность торфов, м"] + [_fmt(self._th(wd[w], 'Торф')) for w in ids])
        rows.append(["Мощность песков, м"] + [_fmt(self._th(wd[w], 'Песок')) for w in ids])
        rows.append(["Среднее содержание на пласт, мг/м³"] +
                    [(f"{get(w,'plast'):g}" if get(w, 'plast') else "") for w in [wd[i] for i in ids]])
        rows.append(["Мощность массы, м"] +
                    [_fmt(get(w, 'mass') or (w['depth'] - self._th(w, 'Торф'))) for w in [wd[i] for i in ids]])
        rows.append(["Среднее содержание на массу, мг/м³"] +
                    [(f"{get(w,'massa_content'):g}" if get(w, 'massa_content') else "") for w in [wd[i] for i in ids]])
        rows.append(["Лимитность"] + [(get(w, 'limitnost') or "") for w in [wd[i] for i in ids]])
        return rows