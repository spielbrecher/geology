import os
import numpy as np
import matplotlib.image as mpimg
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from matplotlib.path import Path as MplPath

# Реестр кодов паттернов согласно Приложению 5
PATTERN_REGISTRY = {
    "grass":         "Почвенно-растительный слой (наклонная штриховка)",
    "vlines":        "Торф (вертикальные линии)",
    "hdash_sparse":  "Ил (редкие горизонтальные штрихи)",
    "plus":          "Лед (кресты)",
    "tildes":        "Глина (тильды ~)",
    "dots":          "Песок (точки)",
    "ellipses_small":"Галька (мелкие эллипсы)",
    "ellipses_large":"Валуны (крупные эллипсы)",
    "triangles":     "Дресва (треугольники)",
    "rects":         "Щебень (угловатые обломки)",
    "x_dots":        "Диорит-порфириты (крестики с точками)",
    "dots_rows":     "Песчаники (ряды точек)",
    "hdash_rows":    "Алевролиты (горизонтальный пунктир)",
    "img":           "Свой паттерн из изображения (код: img:путь.png@масштаб)",
}

# Совместимость со старыми символьными штриховками из прежних версий БД
LEGACY_HATCH = {
    "|": "vlines", "||": "vlines",
    ".": "dots", "...": "dots", "..": "dots_rows",
    "o": "ellipses_small", "oo": "ellipses_small",
    "O": "ellipses_large", "OO": "ellipses_large",
    "*": "triangles", "**": "triangles",
    "x": "rects", "xx": "rects",
    "+": "plus", "++": "plus",
    "--": "hdash_sparse", "---": "hdash_rows",
    "//": "grass", "~~~": "tildes",
}

TILDE = MplPath(
    [(0, 0), (0.25, 0.6), (0.5, 0), (0.75, -0.6), (1, 0)],
    [MplPath.MOVETO, MplPath.CURVE3, MplPath.CURVE3, MplPath.CURVE3, MplPath.CURVE3],
)


class PatternFiller:
    def __init__(self, seed=42):
        self.rng = np.random.default_rng(seed)

    # ================= ОСНОВНОЙ МЕТОД =================
    def fill(self, ax, xy, code, spacing=2.0, color='black'):
        xy = np.asarray(xy, float)
        (xmin, ymin), (xmax, ymax) = xy.min(axis=0), xy.max(axis=0)

        border = mpatches.Polygon(xy, closed=True, fc='white', ec='black',
                                  lw=1.0, zorder=2)
        ax.add_patch(border)
        clip = MplPath(xy)

        # совместимость со старыми кодами
        code = LEGACY_HATCH.get(code, code)

        arts = []
        if code and code.startswith("img:"):
            spec = code[4:]
            tile = spacing
            if "@" in spec:                      # img:patterns/glina.png@4
                spec, t = spec.rsplit("@", 1)
                try:
                    tile = float(t)
                except ValueError:
                    pass
            if os.path.exists(spec):
                arts += self._image(ax, xy, spec, tile)
            else:
                print(f"⚠️ Файл паттерна не найден: {spec} → fallback 'dots'")
                pts = self._points(xmin, xmax, ymin, ymax, spacing, True, True)
                pts = pts[clip.contains_points(pts)]
                arts += self._p_dots(ax, pts, spacing, color, xmin, xmax, ymin, ymax)
        else:
            s = spacing
            stagger = code not in ("dots_rows",)
            jitter = code in ("dots", "ellipses_small", "ellipses_large", "triangles")
            pts = self._points(xmin, xmax, ymin, ymax, s, stagger, jitter)
            pts = pts[clip.contains_points(pts)]
            fn = getattr(self, f"_p_{code}", self._p_dots)
            arts += fn(ax, pts, s, color, xmin, xmax, ymin, ymax)

        # Явный клип (Path, transData) — надёжно во всех версиях matplotlib
        for a in arts:
            a.set_clip_path(clip, ax.transData)
            a.set_zorder(3)
        return border

    # ================= ЛЕГЕНДА =================
    def draw_legend(self, ax, items, ncols=4):
        ax.axis('off')
        items = list(items)
        rows = int(np.ceil(len(items) / ncols))
        W, H = 3.4, 1.0
        ax.set_xlim(0, ncols * W)
        ax.set_ylim(0, rows * H)
        for i, (name, code) in enumerate(items):
            r, c = divmod(i, ncols)
            x0, y0 = c * W, (rows - 1 - r) * H
            box = [(x0 + 0.05, y0 + 0.15), (x0 + 1.0, y0 + 0.15),
                   (x0 + 1.0, y0 + 0.85), (x0 + 0.05, y0 + 0.85)]
            self.fill(ax, box, code, spacing=0.15)
            ax.text(x0 + 1.1, y0 + 0.5, name, va='center', ha='left', fontsize=9)

    # ================= СЛУЖЕБНОЕ =================
    def _points(self, xmin, xmax, ymin, ymax, s, stagger, jitter):
        sx, sy = s, s * 0.7
        pts = []
        for j, y in enumerate(np.arange(ymin, ymax + sy, sy)):
            off = sx / 2 if stagger and j % 2 else 0
            for x in np.arange(xmin, xmax + sx, sx):
                px, py = x + off, y
                if jitter:
                    px += self.rng.uniform(-0.2, 0.2) * s
                    py += self.rng.uniform(-0.2, 0.2) * s
                pts.append((px, py))
        return np.array(pts)

    def _image(self, ax, xy, filepath, tile):
        img = mpimg.imread(filepath)
        if img.ndim == 2:
            img = np.stack([img] * 3, axis=-1)
        elif img.shape[2] == 4:
            img = img[..., :3]
        (xmin, ymin), (xmax, ymax) = xy.min(axis=0), xy.max(axis=0)
        nx = max(1, int(np.ceil((xmax - xmin) / tile)))
        ny = max(1, int(np.ceil((ymax - ymin) / tile)))
        big = np.tile(img, (ny, nx, 1))
        im = ax.imshow(big, extent=(xmin, xmin + nx * tile, ymin, ymin + ny * tile),
                       aspect='auto', interpolation='nearest')
        return [im]

    # ================= ВЕКТОРНЫЕ ПАТТЕРНЫ =================
    def _p_grass(self, ax, pts, s, color, *bb):
        return [ax.add_line(Line2D([x, x + 0.5 * s], [y, y + 0.5 * s], color=color, lw=0.8))
                for x, y in pts]

    def _p_vlines(self, ax, pts, s, color, xmin, xmax, ymin, ymax):
        arts, x = [], xmin
        while x <= xmax:
            arts.append(ax.add_line(Line2D([x, x], [ymin, ymax], color=color, lw=0.8)))
            x += s * 0.45
        return arts

    def _p_hdash_sparse(self, ax, pts, s, color, *bb):
        return [ax.add_line(Line2D([x - 0.3 * s, x + 0.3 * s], [y, y], color=color, lw=0.8))
                for x, y in pts]

    def _p_plus(self, ax, pts, s, color, *bb):
        arts = []
        for x, y in pts:
            arts.append(ax.add_line(Line2D([x - 0.2 * s, x + 0.2 * s], [y, y], color=color, lw=0.8)))
            arts.append(ax.add_line(Line2D([x, x], [y - 0.2 * s, y + 0.2 * s], color=color, lw=0.8)))
        return arts

    def _p_tildes(self, ax, pts, s, color, *bb):
        arts = []
        for x, y in pts:
            verts = np.array(TILDE.vertices) * s * 0.6 + (x - s * 0.3, y)
            arts.append(ax.add_patch(mpatches.PathPatch(
                MplPath(verts, TILDE.codes), fill=False, ec=color, lw=0.8)))
        return arts

    def _p_dots(self, ax, pts, s, color, *bb):
        return [ax.add_patch(mpatches.Circle((x, y), s * 0.06, fc=color, ec='none'))
                for x, y in pts]

    _p_dots_rows = _p_dots

    def _p_ellipses_small(self, ax, pts, s, color, *bb):
        return [ax.add_patch(mpatches.Ellipse((x, y), s * 0.5, s * 0.25,
                angle=self.rng.uniform(0, 180), fill=False, ec=color, lw=0.8))
                for x, y in pts]

    def _p_ellipses_large(self, ax, pts, s, color, *bb):
        return [ax.add_patch(mpatches.Ellipse((x, y), s * 0.9, s * 0.45,
                angle=self.rng.uniform(0, 180), fill=False, ec=color, lw=0.9))
                for x, y in pts]

    def _p_triangles(self, ax, pts, s, color, *bb):
        return [ax.add_patch(mpatches.Polygon(
                [(x, y + 0.15 * s), (x - 0.15 * s, y - 0.12 * s), (x + 0.15 * s, y - 0.12 * s)],
                closed=True, fill=False, ec=color, lw=0.8))
                for x, y in pts]

    def _p_rects(self, ax, pts, s, color, *bb):
        return [ax.add_patch(mpatches.Rectangle(
                (x - 0.3 * s, y - 0.15 * s), s * 0.6, s * 0.3,
                angle=self.rng.uniform(-30, 30), fill=False, ec=color, lw=0.8))
                for x, y in pts]

    def _p_x_dots(self, ax, pts, s, color, *bb):
        arts = []
        for x, y in pts:
            arts.append(ax.add_line(Line2D([x - 0.15 * s, x + 0.15 * s],
                                           [y - 0.15 * s, y + 0.15 * s], color=color, lw=0.8)))
            arts.append(ax.add_line(Line2D([x - 0.15 * s, x + 0.15 * s],
                                           [y + 0.15 * s, y - 0.15 * s], color=color, lw=0.8)))
            arts.append(ax.add_patch(mpatches.Circle((x + 0.4 * s, y + 0.3 * s),
                                                     s * 0.05, fc=color, ec='none')))
        return arts

    def _p_hdash_rows(self, ax, pts, s, color, xmin, xmax, ymin, ymax):
        arts, y = [], ymin
        while y <= ymax:
            arts.append(ax.add_line(Line2D([xmin, xmax], [y, y], color=color,
                                           lw=0.8, linestyle=(0, (5, 4)))))
            y += s * 0.5
        return arts