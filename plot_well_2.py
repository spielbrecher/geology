import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from matplotlib.gridspec import GridSpec

# 1. ДАННЫЕ (Линия 91)
wells_data = {
    10: {
        "x": 10, "surface": 105, "depth": 50, "visual": "ЗНК",
        "layers": [
            {"z_from": 0, "z_to": 4, "lith": "Торф", "hatch": "///", "au": None},
            {"z_from": 4, "z_to": 22, "lith": "Песок", "hatch": "...", "au": 1.2},
            {"z_from": 22, "z_to": 48, "lith": "Гравий", "hatch": "xxx", "au": 4.5},
            {"z_from": 48, "z_to": 50, "lith": "Глина", "hatch": "---", "au": None}
        ]
    },
    13: {
        "x": 25, "surface": 103, "depth": 48, "visual": "СЛ",
        "layers": [
            {"z_from": 0, "z_to": 5, "lith": "Торф", "hatch": "///", "au": None},
            {"z_from": 5, "z_to": 25, "lith": "Песок", "hatch": "...", "au": 0.8},
            {"z_from": 25, "z_to": 45, "lith": "Гравий", "hatch": "xxx", "au": 3.1},
            {"z_from": 45, "z_to": 48, "lith": "Глина", "hatch": "---", "au": None}
        ]
    },
    16: {
        "x": 40, "surface": 107, "depth": 50, "visual": "РБС",
        "layers": [
            {"z_from": 0, "z_to": 6, "lith": "Торф", "hatch": "///", "au": None},
            {"z_from": 6, "z_to": 20, "lith": "Песок", "hatch": "...", "au": 0.5},
            {"z_from": 20, "z_to": 44, "lith": "Гравий", "hatch": "xxx", "au": 6.2},
            {"z_from": 44, "z_to": 50, "lith": "Глина", "hatch": "---", "au": None}
        ]
    },
    19: {
        "x": 55, "surface": 104, "depth": 50, "visual": "Пыль",
        "layers": [
            {"z_from": 0, "z_to": 3, "lith": "Торф", "hatch": "///", "au": None},
            {"z_from": 3, "z_to": 18, "lith": "Песок", "hatch": "...", "au": 1.5},
            {"z_from": 18, "z_to": 48, "lith": "Гравий", "hatch": "xxx", "au": 2.8},
            {"z_from": 48, "z_to": 50, "lith": "Глина", "hatch": "---", "au": None}
        ]
    },
    20: {
        "x": 68, "surface": 106, "depth": 50, "visual": "ЗНК",
        "layers": [
            {"z_from": 0, "z_to": 4, "lith": "Торф", "hatch": "///", "au": None},
            {"z_from": 4, "z_to": 21, "lith": "Песок", "hatch": "...", "au": 1.1},
            {"z_from": 21, "z_to": 47, "lith": "Гравий", "hatch": "xxx", "au": 3.7},
            {"z_from": 47, "z_to": 50, "lith": "Глина", "hatch": "---", "au": None}
        ]
    },
    21: {
        "x": 80, "surface": 105, "depth": 50, "visual": "СЛ",
        "layers": [
            {"z_from": 0, "z_to": 5, "lith": "Торф", "hatch": "///", "au": None},
            {"z_from": 5, "z_to": 23, "lith": "Песок", "hatch": "...", "au": 0.9},
            {"z_from": 23, "z_to": 49, "lith": "Гравий", "hatch": "xxx", "au": 2.4},
            {"z_from": 49, "z_to": 50, "lith": "Глина", "hatch": "---", "au": None}
        ]
    }
}

# 2. СОЗДАНИЕ ГРАФИКА - УВЕЛИЧИЛИ ДОЛЮ ГРАФИКА
fig = plt.figure(figsize=(16, 10))  # Чуть меньше высота
gs = GridSpec(5, 1, figure=fig, height_ratios=[3.5, 0.3, 0.4, 0.4, 0.4])  # График занимает 3.5 из 5

# Основная область для графика (БОЛЬШЕ МЕСТА)
ax = fig.add_subplot(gs[0])
ax.set_facecolor('#fffef5')
ax.grid(True, which='both', color='orange', alpha=0.3, linestyle='-', linewidth=0.5)
ax.minorticks_on()
ax.grid(which='minor', color='orange', alpha=0.1, linestyle='-', linewidth=0.5)

ax.set_xlim(0, 90)
ax.set_ylim(115, 40)
ax.set_xlabel("Расстояние по линии, м", fontsize=12, fontweight='bold', labelpad=10)
ax.set_ylabel("Отметка, м", fontsize=12, fontweight='bold', labelpad=10)
ax.set_title("Геоэксплуатационный разрез р. Озерный Линия 91", fontsize=14, fontweight='bold', pad=15)

# 3. ОТРИСОВКА РЕЛЬЕФА И КОЛОНОК
well_ids = sorted(wells_data.keys())

for i, wid in enumerate(well_ids):
    w = wells_data[wid]
    x = w["x"]
    surf = w["surface"]
    
    # Подпись номера скважины сверху
    ax.text(x, surf + 2, f"{wid}", ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    # Рисуем рельеф
    if i > 0:
        prev_x = wells_data[well_ids[i-1]]["x"]
        prev_surf = wells_data[well_ids[i-1]]["surface"]
        ax.plot([prev_x, x], [prev_surf, surf], 'k-', linewidth=1.5)
        ax.fill_between([prev_x, x], [prev_surf, surf], [min(prev_surf, surf)-2, min(prev_surf, surf)-2], 
                       color='#d4c9a8', hatch='\\\\\\', alpha=0.5)

    # Рисуем колонку скважины
    for layer in w["layers"]:
        rect = patches.Rectangle((x - 1.5, surf - layer["z_to"]), 3, layer["z_to"] - layer["z_from"],
                                 linewidth=1, edgecolor='black', facecolor='white', hatch=layer["hatch"])
        ax.add_patch(rect)
        
        # Подпись литологии
        mid_depth = surf - (layer["z_from"] + layer["z_to"])/2
        if layer["z_to"] - layer["z_from"] > 6:
            ax.text(x, mid_depth, layer["lith"], ha='center', va='center', fontsize=8, rotation=90)
        
        # Подписи содержания золота
        if layer["au"] is not None:
            ax.text(x + 2.5, mid_depth, f"{layer['au']}", ha='left', va='center', fontsize=9, color='red')

    # Соединяем слои между скважинами
    if i > 0:
        prev_w = wells_data[well_ids[i-1]]
        prev_x = prev_w["x"]
        prev_surf = prev_w["surface"]
        
        for l_idx in range(min(len(w["layers"]), len(prev_w["layers"]))):
            curr_layer = w["layers"][l_idx]
            prev_layer = prev_w["layers"][l_idx]
            
            y_curr_top = surf - curr_layer["z_from"]
            y_curr_bot = surf - curr_layer["z_to"]
            y_prev_top = prev_surf - prev_layer["z_from"]
            y_prev_bot = prev_surf - prev_layer["z_to"]
            
            ax.plot([prev_x, x], [y_prev_top, y_curr_top], 'k-', linewidth=1, alpha=0.7)
            ax.plot([prev_x, x], [y_prev_bot, y_curr_bot], 'k-', linewidth=1, alpha=0.7)

# Вертикальные линии скважин
for wid in well_ids:
    w = wells_data[wid]
    ax.plot([w["x"], w["x"]], [w["surface"], w["surface"] - w["depth"]], 'k-', linewidth=2)

ax.invert_yaxis()

# 4. КОМПАКТНАЯ ЛЕГЕНДА
ax_legend = fig.add_subplot(gs[1])
ax_legend.axis('off')
legend_elements = [
    patches.Patch(facecolor='white', edgecolor='black', hatch='///', label='/// Торф'),
    patches.Patch(facecolor='white', edgecolor='black', hatch='...', label='... Песок'),
    patches.Patch(facecolor='white', edgecolor='black', hatch='xxx', label='xxx Гравий'),
    patches.Patch(facecolor='white', edgecolor='black', hatch='---', label='--- Глина'),
]
ax_legend.legend(handles=legend_elements, loc='center', ncol=4, fontsize=9, frameon=True, borderpad=0.5)
ax_legend.set_title("Условные обозначения", fontsize=10, fontweight='bold', pad=5)

# 5. КОМПАКТНАЯ ТАБЛИЦА (уменьшили шрифт и высоту ячеек)
table_rows = []
well_ids_sorted = sorted(wells_data.keys())

# Заголовок таблицы
table_rows.append(["№ скважины"] + [f"{wid}" for wid in well_ids_sorted])

# Расстояние между скважинами
distances = []
for i in range(len(well_ids_sorted)):
    if i == 0:
        distances.append("-")
    else:
        prev_x = wells_data[well_ids_sorted[i-1]]["x"]
        curr_x = wells_data[well_ids_sorted[i]]["x"]
        distances.append(f"{curr_x - prev_x} м")
table_rows.append(["Расст. между скважин"] + distances)

# Глубина скважин
depths = [f"{wells_data[wid]['depth']} м" for wid in well_ids_sorted]
table_rows.append(["Глубина скважин"] + depths)

# Визуальный результат
visuals = [wells_data[wid]['visual'] for wid in well_ids_sorted]
table_rows.append(["Визуальный результат"] + visuals)

# Создаем таблицу (компактнее)
ax_table = fig.add_subplot(gs[2:])
ax_table.axis('off')

table = ax_table.table(cellText=table_rows[1:], colLabels=table_rows[0], 
                       loc='center', cellLoc='center', colColours=['#f0f0f0'] * (len(well_ids_sorted) + 1))
table.auto_set_font_size(False)
table.set_fontsize(9)  # Уменьшили шрифт
table.scale(1.1, 1.5)  # Уменьшили масштаб ячеек

# Выделяем заголовки столбцов
for i, wid in enumerate(well_ids_sorted):
    table[(0, i+1)].set_facecolor('#d4e5f7')
    table[(0, i+1)].set_text_props(fontweight='bold')

# Выделяем строку визуального результата
for i in range(len(well_ids_sorted) + 1):
    table[(3, i)].set_facecolor('#fff3cd')

plt.tight_layout(pad=2.0, h_pad=1.0)  # Уменьшили отступы
plt.show()

# Сохранение в файл
plt.savefig("geological_cross_section_line91.png", dpi=300, bbox_inches='tight')
plt.savefig("geological_cross_section_line91.pdf", bbox_inches='tight')