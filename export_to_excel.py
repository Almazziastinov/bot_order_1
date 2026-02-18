import pandas as pd
from db.engine import engine
from datetime import datetime
import logging

def export_full_data_to_excel():
    """
    Выгружает данные из таблиц 'users' и 'linktrs' в Excel-файл с двумя листами.
    Возвращает имя файла.
    """
    try:
        # Читаем данные пользователей
        users_df = pd.read_sql("SELECT * FROM users", engine)

        # Читаем данные переходов с дополнительной информацией о пользователях
        linktrs_df = pd.read_sql("""
            SELECT
                linktrs.id,
                linktrs.user_id,
                users.username,
                users.first_name,
                users.last_name,
                linktrs.link,
                linktrs.created_at
            FROM linktrs
            LEFT JOIN users ON linktrs.user_id = users.user_id
            ORDER BY linktrs.created_at DESC
        """, engine)

        # Генерируем имя файла с датой
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f'export_full_{timestamp}.xlsx'

        # Создаем Excel файл с двумя листами
        with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
            # Лист с пользователями
            users_df.to_excel(writer, sheet_name='Пользователи', index=False)

            # Лист с переходами
            linktrs_df.to_excel(writer, sheet_name='Переходы по ссылкам', index=False)

            # Автоматически подгоняем ширину колонок
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width

        # Добавляем статистику
        add_stats_to_excel(output_filename, users_df, linktrs_df)

        logging.info(f"Данные успешно выгружены в файл: {output_filename}")
        logging.info(f"  - Пользователей: {len(users_df)}")
        logging.info(f"  - Переходов: {len(linktrs_df)}")

        return output_filename

    except Exception as e:
        logging.error(f"Произошла ошибка при выгрузке данных: {e}")
        return None

def export_users_only_to_excel():
    """
    Выгружает только пользователей (для обратной совместимости)
    """
    try:
        df = pd.read_sql("SELECT * FROM users", engine)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f'export_users_{timestamp}.xlsx'
        df.to_excel(output_filename, index=False)
        return output_filename
    except Exception as e:
        logging.error(f"Ошибка при выгрузке пользователей: {e}")
        return None

def export_links_only_to_excel():
    """
    Выгружает только переходы по ссылкам
    """
    try:
        df = pd.read_sql("""
            SELECT
                linktrs.*,
                users.username
            FROM linktrs
            LEFT JOIN users ON linktrs.user_id = users.user_id
            ORDER BY linktrs.created_at DESC
        """, engine)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f'export_links_{timestamp}.xlsx'
        df.to_excel(output_filename, index=False)
        return output_filename
    except Exception as e:
        logging.error(f"Ошибка при выгрузке переходов: {e}")
        return None

def add_stats_to_excel(filename, users_df, linktrs_df):
    """
    Добавляет лист со статистикой в Excel файл
    """
    try:
        # Создаем статистику
        stats_data = []

        # Общая статистика
        stats_data.append(['Общая статистика', ''])
        stats_data.append(['Всего пользователей', len(users_df)])
        stats_data.append(['Всего переходов', len(linktrs_df)])
        stats_data.append(['Дата выгрузки', datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        stats_data.append([])

        # Статистика по ссылкам
        if not linktrs_df.empty:
            stats_data.append(['Статистика по ссылкам', 'Количество переходов'])
            link_stats = linktrs_df['link'].value_counts()
            for link, count in link_stats.items():
                stats_data.append([f'Ссылка: {link}', count])

            stats_data.append([])

            # Статистика по дням
            stats_data.append(['Переходы по дням', ''])
            linktrs_df['created_at'] = pd.to_datetime(linktrs_df['created_at'])
            daily_stats = linktrs_df['created_at'].dt.date.value_counts().sort_index()

            for date, count in daily_stats.items():
                stats_data.append([str(date), count])

        # Создаем DataFrame со статистикой
        stats_df = pd.DataFrame(stats_data, columns=['Показатель', 'Значение'])

        # Добавляем лист со статистикой в существующий файл
        with pd.ExcelWriter(filename, engine='openpyxl', mode='a') as writer:
            stats_df.to_excel(writer, sheet_name='Статистика', index=False)

            # Настраиваем ширину колонок
            worksheet = writer.sheets['Статистика']
            worksheet.column_dimensions['A'].width = 30
            worksheet.column_dimensions['B'].width = 20

    except Exception as e:
        logging.error(f"Ошибка при добавлении статистики: {e}")

# Для обратной совместимости оставляем старую функцию
export_users_to_excel = export_full_data_to_excel

if __name__ == "__main__":
    # Настраиваем логирование для тестирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("1. Полный экспорт (пользователи + переходы)")
    print("2. Только пользователи")
    print("3. Только переходы")
    choice = input("Выберите тип экспорта (1-3): ")

    if choice == "1":
        filename = export_full_data_to_excel()
    elif choice == "2":
        filename = export_users_only_to_excel()
    elif choice == "3":
        filename = export_links_only_to_excel()
    else:
        print("Неверный выбор")
        filename = None

    if filename:
        print(f"✅ Данные успешно выгружены в файл: {filename}")
    else:
        print("❌ Не удалось выгрузить данные")
