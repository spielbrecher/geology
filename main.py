from database import Database
from visualization import CrossSectionPlotter

def main():
    """Демонстрация работы системы"""
    print("=" * 60)
    print("   ГЕОЛОГИЧЕСКАЯ ИНФОРМАЦИОННАЯ СИСТЕМА")
    print("=" * 60)
    
    # Инициализация
    print("\n1️⃣ Инициализация базы данных...")
    db = Database()
    
    # Получаем данные для линии 91
    print("\n2️⃣ Загрузка данных для Линии 91...")
    data = db.get_line_cross_section("91")
    
    if data:
        line = data['line']
        wells_count = len(data['wells_data'])
        
        print(f"   📋 Линия: {line['line_number']}")
        print(f"   🌊 Река: {line['river_name']}")
        print(f"   ⛏️  Скважин: {wells_count}")
        
        # Построение графика
        print("\n3️⃣ Построение геологического разреза...")
        plotter = CrossSectionPlotter(output_dir="output")
        plotter.plot_cross_section(data, save_formats=['png', 'pdf'])
        
        print("\n✅ Готово! Файлы сохранены в папку 'output/'")
        print("\n📁 Созданные файлы:")
        print("   - output/line_91_cross_section.png")
        print("   - output/line_91_cross_section.pdf")
        
    else:
        print("❌ Ошибка: Линия 91 не найдена в базе данных")
        print("💡 Запустите сначала: python init_db.py")

if __name__ == "__main__":
    main()