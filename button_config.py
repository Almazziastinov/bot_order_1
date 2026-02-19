# button_config.py
from sqlalchemy.orm import sessionmaker
from db.engine import engine
from db.models import ButtonLink
from typing import Dict, Optional
import logging

Session = sessionmaker(bind=engine)

# Словарь с настройками кнопок по умолчанию
DEFAULT_BUTTONS = {
    'support': {
        'button_text': '📝 Написать в поддержку',
        'url': 'https://t.me/sam_soberu',
        'description': 'Ссылка на поддержку'
    },
    'contest': {
        'button_text': '🎁 Конкурс с крутыми призами',
        'url': 'https://gravtool.ru/contest',
        'description': 'Страница конкурса'
    },
    'videos': {
        'button_text': '🎬 Ролики по работе с гравером',
        'url': 'https://t.me/grav_tool/86',
        'description': 'Обучающие видео'
    },
    'catalog': {
        'button_text': '🛍 Каталог товаров',
        'url': 'https://gravtool.ru/catalog',
        'description': 'Каталог товаров'
    },
    'channel': {
        'button_text': '📢 Наш телеграм канал',
        'url': 'https://t.me/grav_tool',
        'description': 'Основной Telegram канал'
    }
}

def init_default_buttons():
    """Инициализация кнопок по умолчанию при первом запуске"""
    with Session() as session:
        for button_name, config in DEFAULT_BUTTONS.items():
            existing = session.query(ButtonLink).filter(ButtonLink.button_name == button_name).first()
            if not existing:
                new_button = ButtonLink(
                    button_name=button_name,
                    button_text=config['button_text'],
                    url=config['url'],
                    description=config['description'],
                    is_active=True
                )
                session.add(new_button)
                logging.info(f"Создана кнопка по умолчанию: {button_name}")
        session.commit()

def get_button_config(button_name: str) -> Optional[Dict]:
    """Получение конфигурации кнопки по имени"""
    with Session() as session:
        button = session.query(ButtonLink).filter(
            ButtonLink.button_name == button_name,
            ButtonLink.is_active == True
        ).first()

        if button:
            return {
                'button_text': button.button_text,
                'url': button.url,
                'description': button.description
            }
        # Если кнопка не найдена, возвращаем конфигурацию по умолчанию
        return DEFAULT_BUTTONS.get(button_name)

def update_button_config(button_name: str, new_url: str, admin_id: int, new_text: str = None) -> bool:
    """Обновление конфигурации кнопки"""
    with Session() as session:
        button = session.query(ButtonLink).filter(ButtonLink.button_name == button_name).first()
        if button:
            button.url = new_url
            if new_text:
                button.button_text = new_text
            button.updated_by = admin_id
            session.commit()
            logging.info(f"Кнопка {button_name} обновлена администратором {admin_id}")
            return True
    return False

def get_all_buttons() -> list:
    """Получение списка всех кнопок"""
    with Session() as session:
        return session.query(ButtonLink).all()

def get_buttons_summary() -> str:
    """Получение сводки по всем кнопкам для админ-панели"""
    with Session() as session:
        buttons = session.query(ButtonLink).all()
        if not buttons:
            return "❌ Нет настроенных кнопок"

        summary = "🔘 Настройки кнопок:\n\n"
        for btn in buttons:
            status = "✅" if btn.is_active else "❌"
            summary += f"{status} <b>{btn.button_text}</b>\n"
            summary += f"   📍 URL: `{btn.url}`\n"
            summary += f"   📝 Описание: {btn.description}\n"
            summary += f"   🕒 Обновлено: {btn.updated_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        return summary
