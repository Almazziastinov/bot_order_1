import asyncio
import logging
import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import ConfigDict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardButton, Message, FSInputFile, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from sqlalchemy.orm import sessionmaker
from db.engine import engine, create_db
from db.models import User, Linktr
from export_to_excel import export_full_data_to_excel   # Убедитесь, что этот модуль существует
from datetime import datetime
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from button_config import get_button_config, init_default_buttons, get_buttons_summary, update_button_config


class EditLinkStates(StatesGroup):
    choosing_button = State()
    entering_new_url = State()
    entering_new_text = State()
    confirming = State()


class Settings(BaseSettings):
    bot_token: str   # Значение по умолчанию
    admin_ids: List[int] = [635124229, 8199226208]  # Значение по умолчанию

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
bot = Bot(
    token=settings.bot_token,
    default=DefaultBotProperties(parse_mode="HTML")
)
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

async def answer_html(message: Message, text: str, reply_markup=None):
    """Ответ с HTML разметкой"""
    try:
        return await message.answer(
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Ошибка HTML: {e}")
        # Отправляем без форматирования
        return await message.answer(
            text=text.replace('<b>', '').replace('</b>', ''),
            reply_markup=reply_markup
        )

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


    support_config = get_button_config('support')
    contest_config = get_button_config('contest')
    videos_config = get_button_config('videos')
    catalog_config = get_button_config('catalog')
    channel_config = get_button_config('channel')

    # Создаем клавиатуру
    kb = [
        [KeyboardButton(text=support_config['button_text'] if support_config else "📝 Написать в поддержку")],
        [KeyboardButton(text=contest_config['button_text'] if contest_config else "🎁 Конкурс с крутыми призами")],
        [KeyboardButton(text=videos_config['button_text'] if videos_config else "🎬 Ролики по работе с гравером")],
        [KeyboardButton(text=catalog_config['button_text'] if catalog_config else "🛍 Каталог товаров")],
        [KeyboardButton(text=channel_config['button_text'] if channel_config else "📢 Наш телеграм канал")]
    ]

    if user.id in settings.admin_ids:
        kb.append([KeyboardButton(text="👨‍💻 Админ-панель")])

    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Выберите пункт меню"
    )

    await answer_html(
        message,
        f"👋 Привет, {user.full_name}!\n\n"
        f"Добро пожаловать! Выберите интересующий вас раздел:",
        reply_markup=keyboard
    )

@dp.message(lambda message: message.text in ["📝 Написать в поддержку", "Написать в поддержку"])
async def support_handler(message: Message):
    user = message.from_user.id
    config = get_button_config('support')
    link = config['url']

    if not config:
        await message.answer("❌ Ссылка временно недоступна")
        return

    add_link_click(user, link)
    """Обработчик для поддержки"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="✍️ Написать в поддержку",
        url=link
    ))
    await answer_html(
        message,
        "📞 <b>Служба поддержки</b>\n\n"
        "Если у вас возникли вопросы или проблемы, "
        "напишите нашему специалисту. Мы постараемся помочь как можно скорее!",
        reply_markup=builder.as_markup()
    )


@dp.message(lambda message: message.text in ["🎁 Конкурс с крутыми призами", "Конкурс с крутыми призами"])
async def contest_handler(message: Message):
    user = message.from_user.id
    config = get_button_config('contest')
    link = config['url']

    add_link_click(user, link)
    """Обработчик для конкурса"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🎲 Участвовать в конкурсе",
        url=link
    ))
    await answer_html(
        message,
        "🎁 <b>КОНКУРС С КРУТЫМИ ПРИЗАМИ!</b>\n\n"
        "Участвуйте и выигрывайте ценные призы!\n\n"
        "👉 Переходите по ссылке и узнайте условия участия:",
        reply_markup=builder.as_markup()
    )


@dp.message(lambda message: message.text in ["🎬 Ролики по работе с гравером", "Ролики по работе с гравером"])
async def videos_handler(message: Message):
    user = message.from_user.id
    config = get_button_config('videos')
    link = config['url']

    add_link_click(user, link)
    """Обработчик для видео"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="📺 Смотреть видео",
        url=link
    ))
    await answer_html(
        message,
        "🎬 <b>Обучающие ролики</b>\n\n"
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
    config = get_button_config('catalog')
    link = config['url']

    add_link_click(user, link)
    """Обработчик для каталога"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🔍 Смотреть каталог",
        url=link
    ))
    await answer_html(
        message,
        "🛍 <b>Каталог товаров</b>\n\n"
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
    config = get_button_config('channel')
    link = config['url']

    add_link_click(user, link)
    """Обработчик для Telegram канала"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="📢 Подписаться на канал",
        url=link
    ))
    await answer_html(
        message,
        "📢 <b>Наш Telegram канал</b>\n\n"
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
    builder.row(InlineKeyboardButton(
        text="🔗 Управление ссылками",
        callback_data="manage_links"
    ))

    await answer_html(
        message,
        "👨‍💻 <b>Административная панель</b>\n\n"
        "<b>Доступные команды:</b>\n"
        "• Экспорт данных в Excel\n"
        "• Просмотр статистики\n"
        "• Управление ссылками\n\n"
        "<i>Выберите действие:</i>",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(lambda c: c.data == "manage_links")
async def manage_links_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Управление ссылками"""
    if callback_query.from_user.id not in settings.admin_ids:
        await callback_query.answer("⛔ Нет доступа", show_alert=True)
        return

    await callback_query.answer()

    # Показываем текущие настройки
    summary = get_buttons_summary()

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="✏️ Изменить ссылку поддержки",
        callback_data="edit_support"
    ))
    builder.row(InlineKeyboardButton(
        text="✏️ Изменить ссылку конкурса",
        callback_data="edit_contest"
    ))
    builder.row(InlineKeyboardButton(
        text="✏️ Изменить ссылку видео",
        callback_data="edit_videos"
    ))
    builder.row(InlineKeyboardButton(
        text="✏️ Изменить ссылку каталога",
        callback_data="edit_catalog"
    ))
    builder.row(InlineKeyboardButton(
        text="✏️ Изменить ссылку канала",
        callback_data="edit_channel"
    ))
    builder.row(InlineKeyboardButton(
        text="◀️ Назад",
        callback_data="back_to_admin"
    ))

    await callback_query.message.answer(
        f"{summary}\n\n"
        "<b>Выберите какую ссылку хотите изменить:</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@dp.callback_query(lambda c: c.data.startswith("edit_"))
async def edit_link_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Начало процесса редактирования ссылки"""
    if callback_query.from_user.id not in settings.admin_ids:
        await callback_query.answer("⛔ Нет доступа", show_alert=True)
        return

    button_name = callback_query.data.replace("edit_", "")
    await state.update_data(button_name=button_name)

    await callback_query.answer()
    await callback_query.message.answer(
        "✏️ <b>Введите новый URL для кнопки:</b>\n\n"
        "(можно отправить ссылку или 'отмена' для выхода)",
        parse_mode="HTML"
    )
    await state.set_state(EditLinkStates.entering_new_url)


@dp.message(EditLinkStates.entering_new_url)
async def process_new_url(message: Message, state: FSMContext):
    """Обработка нового URL"""
    if message.text.lower() == 'отмена':
        await state.clear()
        await message.answer("❌ Редактирование отменено")
        return

    # Простая валидация URL
    if not message.text.startswith(('http://', 'https://', 't.me/')):
        await message.answer("❌ Пожалуйста, отправьте корректную ссылку (начинается с http://, https:// или t.me/)")
        return

    await state.update_data(new_url=message.text)

    data = await state.get_data()
    button_name = data.get('button_name')

    # Получаем текущую конфигурацию для показа
    config = get_button_config(button_name)

    await message.answer(
        f"Текущий текст кнопки: {config['button_text'] if config else 'Не найден'}\n"
        f"Хотите изменить текст кнопки? (да/нет)"
    )
    await state.set_state(EditLinkStates.entering_new_text)


@dp.message(EditLinkStates.entering_new_text)
async def process_new_text(message: Message, state: FSMContext):
    """Обработка нового текста кнопки"""
    data = await state.get_data()
    button_name = data.get('button_name')
    new_url = data.get('new_url')

    if message.text.lower() == 'да':
        await message.answer("✏️ Введите новый текст для кнопки:")
        await state.set_state(EditLinkStates.confirming)
    else:
        # Сохраняем изменения без изменения текста
        admin_id = message.from_user.id
        success = update_button_config(button_name, new_url, admin_id)

        if success:
            await message.answer("✅ Ссылка успешно обновлена!")
        else:
            await message.answer("❌ Не удалось обновить ссылку")

        await state.clear()


@dp.message(EditLinkStates.confirming)
async def confirm_new_text(message: Message, state: FSMContext):
    """Подтверждение нового текста"""
    data = await state.get_data()
    button_name = data.get('button_name')
    new_url = data.get('new_url')
    new_text = message.text

    admin_id = message.from_user.id
    success = update_button_config(button_name, new_url, admin_id, new_text)

    if success:
        await message.answer("✅ Ссылка и текст кнопки успешно обновлены!")
    else:
        await message.answer("❌ Не удалось обновить настройки")

    await state.clear()


@dp.callback_query(lambda c: c.data == "back_to_admin")
async def back_to_admin_callback(callback_query: types.CallbackQuery):
    """Возврат в админ-панель"""
    if callback_query.from_user.id not in settings.admin_ids:
        await callback_query.answer("⛔ Нет доступа", show_alert=True)
        return

    await callback_query.answer()

    # Показываем админ-панель
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
        text="📊 Статистика переходов",
        callback_data="link_stats"
    ))
    builder.row(InlineKeyboardButton(
        text="🔗 Управление ссылками",
        callback_data="manage_links"
    ))

    await callback_query.message.answer(
        "👨‍💻 <b>Административная панель</b>\n\n"
        "Выберите действие:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
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

    stats_text = "📊 <b>Статистика переходов:</b>\n\n"
    stats_text += f"👥 Всего пользователей: {total_users}\n"
    stats_text += f"🖱 Всего переходов: {total_clicks}\n\n"
    stats_text += "<b>По ссылкам:</b>\n"

    for link, clicks, unique_users in link_stats:
        stats_text += f"• {link}: {clicks} переходов (уникальных: {unique_users})\n"

    await callback_query.message.answer(
        stats_text,
        parse_mode="HTML"
    )

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
        f"📈 <b>Статистика бота</b>\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"🆔 Ваш ID: {callback_query.from_user.id}\n"
        f"⚡️ Бот активен",
        parse_mode="HTML"
    )


async def main() -> None:
    """Главная функция"""
    # Создаем базу данных
    create_db()

    init_default_buttons()

    logging.info("База данных инициализирована")
    logging.info("Кнопки по умолчанию настроены")


    # Запускаем бота
    logging.info("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())
