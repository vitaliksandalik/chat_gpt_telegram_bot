import os
import asyncio
import logging
import sys

from openai import OpenAI

from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from dotenv import load_dotenv

from message_templates import message_templates


load_dotenv()  # This is new, to load the environment variables from .env file
TOKEN = os.getenv("TOKEN")  # Bot token

dp = Dispatcher()
client = OpenAI()
bot = Bot(TOKEN, parse_mode=ParseMode.HTML)

messages = {}
user_languages = {}   # Track of user's current language

language_keyboard = InlineKeyboardBuilder()
language_keyboard.add(types.InlineKeyboardButton(text="English🇬🇧", callback_data='en'),
                      types.InlineKeyboardButton(text="Український🇺🇦", callback_data='ua'))


@dp.callback_query(F.data.in_({"ua", "en"}))
async def process_callback(callback: CallbackQuery):
    user_languages[callback.from_user.id] = callback.data
    message_template = message_templates[callback.data]['language_confirmation']
    await callback.message.answer(text=message_template)


@dp.message(Command('language'))
async def language_cmd(message: types.Message):
    language = user_languages.get(message.from_user.id, 'en')
    await message.answer(text=message_templates[language]['language_selection'],
                         reply_markup=language_keyboard.as_markup())


async def ask_gpt(userid) -> str:
    # Function to ask GPT a question and get the response
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages[userid],
        temperature=0,
    )

    return response.choices[0].message.content


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """ This handler receives messages with `/start` command """
    userid = message.from_user.id
    messages[userid] = []
    language = user_languages.get(message.from_user.id, 'en')  # Get the selected language
    await message.reply(message_templates[language]['start'])  # Retrieve the correct message based on the language


@dp.message()
async def gpt_response_handler(message: Message) -> None:
    # GPT response handler
    user_message = message.text
    userid = message.from_user.id
    if userid not in messages:
        messages[userid] = []

    messages[userid].append({"role": "user", "content": user_message})
    gpt_response = await ask_gpt(userid)
    await message.answer(gpt_response)


async def main() -> None:
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
