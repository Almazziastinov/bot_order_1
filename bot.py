import asyncio
import logging
import os
from typing import List
from pydantic_settings import BaseSettings
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardButton, Message, FSInputFile, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from sqlalchemy.orm import sessionmaker
from db.engine import engine, create_db
from db.models import User, Linktr
from export_to_excel import export_full_data_to_excel   # Убедитесь, что этот модуль существует
from datetime import datetime



class Settings(BaseSettings):
    bot_token: str
    admin_ids: List[int]

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'


settings = Settings()
bot = Bot(token=settings.bot_token)
dp = Dispatcher()

Session = sessionmaker(bind=engine)


def add_user_to_db(user_id: int, username: str | None, first_name: str | None, last_name: str | None):
    """Добавление или обновление пользователя в БД"""
    with Session() as session:
        user = session.query(User).filter(User.user_id == user_id).first()
        if not user:
            new_user = User(
                user_id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            session.add(new_user)
            logging.info(f"Новый пользователь добавлен: {user_id}")
        else:
            # Обновляем данные пользователя
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            logging.info(f"Данные пользователя обновлены: {user_id}")
        session.commit()

def add_link_click(user_id: int, link: str):
    """
    Добавляет запись о переходе по ссылке в таблицу linktr
    """
    with Session() as session:
        new_click = Linktr(
            user_id=user_id,
            link=link,
            created_at=datetime.now()
        )
        session.add(new_click)
        session.commit()
        logging.info(f"Сохранен переход пользователя {user_id} по ссылке: {link}")


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """Обработчик команды /start"""
    user = message.from_user

    add_user_to_db(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )

    # Создаем клавиатуру
    kb = [
        [KeyboardButton(text="📝 Написать в поддержку")],
        [KeyboardButton(text="🎁 Конкурс с крутыми призами")],
        [KeyboardButton(text="🎬 Ролики по работе с гравером")],
        [KeyboardButton(text="🛍 Каталог товаров")],
        [KeyboardButton(text="📢 Наш телеграм канал")]
    ]

    if user.id in settings.admin_ids:
        kb.append([KeyboardButton(text="👨‍💻 Админ-панель")])

    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Выберите пункт меню"
    )

    await message.answer(
        f"👋 Привет, {user.full_name}!\n\n"
        f"Добро пожаловать! Выберите интересующий вас раздел:",
        reply_markup=keyboard
    )


@dp.message(lambda message: message.text in ["📝 Написать в поддержку", "Написать в поддержку"])
async def support_handler(message: Message):
    user = message.from_user.id
    link = "https://t.me/sam_soberu"

    add_link_click(user, link)
    """Обработчик для поддержки"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="✍️ Написать в поддержку",
        url=link
    ))
    await message.answer(
        "📞 **Служба поддержки**\n\n"
        "Если у вас возникли вопросы или проблемы, "
        "напишите нашему специалисту. Мы постараемся помочь как можно скорее!",
        reply_markup=builder.as_markup()
    )


@dp.message(lambda message: message.text in ["🎁 Конкурс с крутыми призами", "Конкурс с крутыми призами"])
async def contest_handler(message: Message):
    user = message.from_user.id
    link = "https://gravtool.ru/contest"

    add_link_click(user, link)
    """Обработчик для конкурса"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🎲 Участвовать в конкурсе",
        url=link
    ))
    await message.answer(
        "🎁 **КОНКУРС С КРУТЫМИ ПРИЗАМИ!**\n\n"
        "Участвуйте и выигрывайте ценные призы!\n\n"
        "👉 Переходите по ссылке и узнайте условия участия:",
        reply_markup=builder.as_markup()
    )


@dp.message(lambda message: message.text in ["🎬 Ролики по работе с гравером", "Ролики по работе с гравером"])
async def videos_handler(message: Message):
    user = message.from_user.id
    link = "https://t.me/grav_tool/86"

    add_link_click(user, link)
    """Обработчик для видео"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="📺 Смотреть видео",
        url=link
    ))
    await message.answer(
        "🎬 **Обучающие ролики**\n\n"
        "Здесь вы найдете полезные видео по работе с гравером:\n"
        "• Советы по использованию\n"
        "• Обзоры насадок\n"
        "• Техники работы\n\n"
        "👉 Переходите и смотрите:",
        reply_markup=builder.as_markup()
    )


@dp.message(lambda message: message.text in ["🛍 Каталог товаров", "Каталог товаров"])
async def catalog_handler(message: Message):
    user = message.from_user.id
    link = "https://gravtool.ru/catalog"

    add_link_click(user, link)
    """Обработчик для каталога"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🔍 Смотреть каталог",
        url=link
    ))
    await message.answer(
        "🛍 **Каталог товаров**\n\n"
        "В нашем каталоге вы найдете:\n"
        "• Граверы и комплектующие\n"
        "• Наборы насадок\n"
        "• Аксессуары и расходники\n\n"
        "👉 Переходите по ссылке:",
        reply_markup=builder.as_markup()
    )


@dp.message(lambda message: message.text in ["📢 Наш телеграм канал", "Наш телеграм канал"])
async def telegram_channel_handler(message: Message):
    user = message.from_user.id
    link = "https://t.me/grav_tool"

    add_link_click(user, link)
    """Обработчик для Telegram канала"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="📢 Подписаться на канал",
        url=link
    ))
    await message.answer(
        "📢 **Наш Telegram канал**\n\n"
        "Подпишитесь, чтобы быть в курсе:\n"
        "• Новинок и акций\n"
        "• Полезных советов\n"
        "• Новостей и обновлений\n\n"
        "👉 Жмите кнопку ниже, чтобы подписаться:",
        reply_markup=builder.as_markup()
    )


@dp.message(lambda message: message.text in ["👨‍💻 Админ-панель", "Админ-панель"])
async def admin_panel_handler(message: Message):
    """Админ-панель"""
    if message.from_user.id not in settings.admin_ids:
        await message.answer("⛔ У вас нет прав для доступа к админ-панели.")
        return

    # Создаем клавиатуру для админа
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="📊 Экспорт данных (Excel)",
        callback_data="export_data"
    ))
    builder.row(InlineKeyboardButton(
        text="📈 Статистика",
        callback_data="stats"
    ))
    builder.row(InlineKeyboardButton(
        text="📈 Статистика переходов",
        callback_data="link_stats"
    ))

    await message.answer(
        "👨‍💻 **Административная панель**\n\n"
        "Доступные команды:\n"
        "• Экспорт пользователей в Excel\n"
        "• Просмотр статистики\n\n"
        "Выберите действие:",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(lambda c: c.data == "export_data")
async def export_users_callback(callback_query: types.CallbackQuery):
    """Обработчик для экспорта данных"""
    if callback_query.from_user.id not in settings.admin_ids:
        await callback_query.answer("⛔ Нет доступа", show_alert=True)
        return

    await callback_query.answer()
    await callback_query.message.answer("⏳ Начинаю выгрузку данных...")

    filename = export_full_data_to_excel()

    if filename and os.path.exists(filename):
        try:
            await bot.send_document(
                callback_query.from_user.id,
                document=FSInputFile(filename),
                caption="📊 Выгрузка данных завершена"
            )
        except Exception as e:
            await callback_query.message.answer(f"❌ Не удалось отправить файл: {e}")
        finally:
            # Удаляем файл после отправки
            try:
                os.remove(filename)
                logging.info(f"Файл {filename} удален")
            except:
                pass
    else:
        await callback_query.message.answer("❌ Не удалось создать файл для выгрузки.")


@dp.callback_query(lambda c: c.data == "link_stats")
async def link_stats_callback(callback_query: types.CallbackQuery):
    """Обработчик для статистики переходов по ссылкам"""
    if callback_query.from_user.id not in settings.admin_ids:
        await callback_query.answer("⛔ Нет доступа", show_alert=True)
        return

    await callback_query.answer()

    # Получаем статистику из БД
    with Session() as session:
        total_users = session.query(User).count()
        total_clicks = session.query(Linktr).count()

        # Статистика по каждой ссылке
        from sqlalchemy import func
        link_stats = session.query(
            Linktr.link,
            func.count(Linktr.id).label('click_count'),
            func.count(func.distinct(Linktr.user_id)).label('unique_users')
        ).group_by(Linktr.link).all()

    stats_text = "📊 **Статистика переходов:**\n\n"
    stats_text += f"👥 Всего пользователей: {total_users}\n"
    stats_text += f"🖱 Всего переходов: {total_clicks}\n\n"
    stats_text += "**По ссылкам:**\n"

    for link, clicks, unique_users in link_stats:
        stats_text += f"• {link}: {clicks} переходов (уникальных: {unique_users})\n"

    await callback_query.message.answer(stats_text)

@dp.callback_query(lambda c: c.data == "stats")
async def stats_callback(callback_query: types.CallbackQuery):
    """Обработчик для статистики"""
    if callback_query.from_user.id not in settings.admin_ids:
        await callback_query.answer("⛔ Нет доступа", show_alert=True)
        return

    await callback_query.answer()

    # Получаем статистику из БД
    with Session() as session:
        total_users = session.query(User).count()

    await callback_query.message.answer(
        f"📈 **Статистика бота**\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"🆔 Ваш ID: {callback_query.from_user.id}\n"
        f"⚡️ Бот активен"
    )


async def main() -> None:
    """Главная функция"""
    # Создаем базу данных
    create_db()
    logging.info("База данных инициализирована")

    # Запускаем бота
    logging.info("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())
