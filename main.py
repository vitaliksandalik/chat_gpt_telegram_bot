import os
import asyncio
import logging
import sys

from dotenv import load_dotenv

from openai import OpenAI
from openai import (APIConnectionError, APITimeoutError, AuthenticationError, BadRequestError,
                    ConflictError, InternalServerError, NotFoundError, PermissionDeniedError,
                    RateLimitError, UnprocessableEntityError)

from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder


from message_templates import message_templates

load_dotenv()
TOKEN = os.getenv("TOKEN")  # BOT TOKEN

bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
client = OpenAI()

# User data tracking
user_messages = {}
user_languages = {}

# Language selection keyboard setup
language_keyboard = InlineKeyboardBuilder()
language_keyboard.add(
    types.InlineKeyboardButton(text="English🇬🇧", callback_data='en'),
    types.InlineKeyboardButton(text="Український🇺🇦", callback_data='ua')
)


# Handlers
@dp.callback_query(F.data.in_({"ua", "en"}))
async def handle_language_change(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_languages[user_id] = callback.data
    await callback.message.answer(text=message_templates[callback.data]['language_confirmation'])


@dp.message(Command('language'))
async def handle_language_command(message: types.Message):
    user_id = message.from_user.id
    language = user_languages.get(user_id, 'en')
    await message.answer(text=message_templates[language]['language_selection'],
                         reply_markup=language_keyboard.as_markup())


@dp.message(Command('help'))
async def handle_help_command(message: types.Message):
    user_id = message.from_user.id
    language = user_languages.get(user_id, 'en')
    await message.answer(text=message_templates[language]['help'])


@dp.message(Command('image'))
async def handle_image_command(message: types.Message):
    user_id = message.from_user.id
    language = user_languages.get(user_id, 'en')
    prompt = message.text.replace('/image', '').strip()

    if not prompt:
        await message.reply(message_templates[language]['image_prompt'])
        return

    processing_message = await message.reply(message_templates[language]['processing'])
    try:
        image_url = await generate_image(prompt, user_id)
        await bot.send_photo(chat_id=message.chat.id, photo=image_url)

    except Exception as e:
        await message.reply(message_templates[language]['image_error'])
        logging.error(f"OpenAI API Error: {e}")

    finally:
        await bot.delete_message(chat_id=message.chat.id, message_id=processing_message.message_id)


async def generate_image(prompt: str, user_id: int) -> str:
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
            user=str(user_id)
        )
        return response.data[0].url
    except (APIConnectionError, APITimeoutError, AuthenticationError, BadRequestError,
            ConflictError, InternalServerError, NotFoundError, PermissionDeniedError,
            RateLimitError, UnprocessableEntityError) as e:
        logging.error(f"Error generating image: {e}")
        raise


@dp.message(CommandStart())
async def handle_start_command(message: Message):
    user_id = message.from_user.id
    user_messages[user_id] = []
    user_languages.setdefault(user_id, 'en')
    await message.reply(message_templates[user_languages[user_id]]['start'])


@dp.message()
async def handle_generic_message(message: Message):
    user_id = message.from_user.id
    user_input = message.text.strip()

    if user_id not in user_messages:
        user_messages[user_id] = []

    user_messages[user_id].append({"role": "user", "content": user_input})
    gpt_response = await ask_gpt(user_id)
    await message.answer(gpt_response)


async def ask_gpt(user_id: int) -> str:
    language = user_languages.get(user_id, 'en')
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=user_messages[user_id],
            temperature=0,
            user=str(user_id)
        )
        return response.choices[0].message.content
    except (APIConnectionError, APITimeoutError, AuthenticationError, BadRequestError,
            ConflictError, InternalServerError, NotFoundError, PermissionDeniedError,
            RateLimitError, UnprocessableEntityError) as e:
        logging.error(f"Error in GPT response: {e}")
        return message_templates[language]["error"]


async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
