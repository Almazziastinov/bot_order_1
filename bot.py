import asyncio
import logging
import os
from typing import List
from pydantic_settings import BaseSettings
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardButton, Message, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.orm import sessionmaker
from db.engine import engine, create_db
from db.models import User
from export_to_excel import export_users_to_excel


class Settings(BaseSettings):
    bot_token: str
    admin_ids: List[int]

    class Config:
        env_file = ".env"


settings = Settings()
bot = Bot(token=settings.bot_token)
dp = Dispatcher()

Session = sessionmaker(bind=engine)


def add_user_to_db(user_id: int, username: str, first_name: str, last_name: str):
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
        else:
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
        session.commit()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    add_user_to_db(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Ссылка 1", url="https://google.com"))
    builder.row(InlineKeyboardButton(text="Ссылка 2", url="https://youtube.com"))
    builder.row(InlineKeyboardButton(text="Ссылка 3", url="https://telegram.org"))

    await message.answer(f"Привет, {message.from_user.full_name}!", reply_markup=builder.as_markup())


@dp.message(Command("export"))
async def export_command_handler(message: Message):
    if message.from_user.id not in settings.admin_ids:
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    await message.answer("Начинаю выгрузку...")
    
    filename = export_users_to_excel()
    
    if filename:
        try:
            await bot.send_document(message.from_user.id, document=FSInputFile(filename))
        except Exception as e:
            await message.answer(f"Не удалось отправить файл: {e}")
        finally:
            os.remove(filename) # Удаляем файл после отправки
    else:
        await message.answer("Не удалось создать файл для выгрузки.")


async def main() -> None:
    create_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
