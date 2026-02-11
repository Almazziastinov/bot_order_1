import pandas as pd
from db.engine import engine

def export_users_to_excel():
    """
    Выгружает данные из таблицы 'users' в Excel-файл и возвращает имя файла.
    """
    try:
        df = pd.read_sql("SELECT * FROM users", engine)
        output_filename = 'users_export.xlsx'
        df.to_excel(output_filename, index=False)
        return output_filename
    except Exception as e:
        print(f"Произошла ошибка при выгрузке данных: {e}")
        return None

if __name__ == "__main__":
    filename = export_users_to_excel()
    if filename:
        print(f"Данные успешно выгружены в файл: {filename}")
