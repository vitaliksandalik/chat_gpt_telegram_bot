import os
import asyncio
import logging
import traceback
import sys
from pathlib import Path

from dotenv import load_dotenv

from openai import OpenAI
from openai import (APIConnectionError, APITimeoutError, AuthenticationError, BadRequestError,
                    ConflictError, InternalServerError, NotFoundError, PermissionDeniedError,
                    RateLimitError, UnprocessableEntityError)

from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, FSInputFile
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
    """
    Handles language change callbacks when a user selects a new language.
    Updates the user's language preference in the user_languages dictionary.

    :param callback: The callback query from the user's action.
    """
    user_id = callback.from_user.id
    user_languages[user_id] = callback.data
    await callback.message.answer(text=message_templates[callback.data]['language_confirmation'])


@dp.message(Command('language'))
async def handle_language_command(message: types.Message):
    """
    Handles the '/language' command. It sends a message to the user with available language options.

    :param message: The message object containing the command.
    """
    user_id = message.from_user.id
    language = user_languages.get(user_id, 'en')
    await message.answer(text=message_templates[language]['language_selection'],
                         reply_markup=language_keyboard.as_markup())


@dp.message(Command('help'))
async def handle_help_command(message: types.Message):
    """
    Handles the '/help' command. Sends a help message to the user explaining how to interact with the bot.

    :param message: The message object containing the command.
    """
    user_id = message.from_user.id
    language = user_languages.get(user_id, 'en')
    await message.answer(text=message_templates[language]['help'])


@dp.message(Command('image'))
async def handle_image_command(message: types.Message):
    """
    Handles the '/image' command to generate and send an image based on the user's text prompt.

    :param message: The message object containing the command and the prompt.
    """
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
        await handle_errors(e, message, language)
    finally:
        await bot.delete_message(chat_id=message.chat.id, message_id=processing_message.message_id)


async def generate_image(prompt: str, user_id: int) -> str:
    """
    Generates an image URL based on a text prompt using a specified image generation model.

    :param prompt: The text prompt based on which the image is generated.
    :param user_id: The ID of the user requesting the image, used for tracking or customization.
    :return: The URL of the generated image.
    """
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
        user=str(user_id)
    )
    if not response.data:
        raise ValueError("No data received from image generation API")

    return response.data[0].url


@dp.message(Command('audio'))
async def handle_audio_command(message: types.Message):
    """
    Handles the '/audio' command to generate and send an audio file based on the user's text prompt.

    :param message: The message object containing the command and the prompt.
    """
    user_id = message.from_user.id
    language = user_languages.get(user_id, 'en')
    prompt = message.text.replace('/audio', '').strip()

    if not prompt:
        await message.reply(message_templates[language]['audio_prompt'])
        return

    processing_message = await message.reply(message_templates[language]['processing'])
    try:
        audio_path = await generate_audio(prompt)
        audio = FSInputFile(audio_path)
        await bot.send_audio(chat_id=message.chat.id, audio=audio)
    except Exception as e:
        await handle_errors(e, message, language)
    finally:
        await bot.delete_message(chat_id=message.chat.id, message_id=processing_message.message_id)


async def generate_audio(prompt: str) -> str:
    """
    Generates an audio file from a text prompt using a text-to-speech service and returns the file path.

    :param prompt: The text prompt to be converted into speech.
    :return: A string representing the file path of the generated audio file.
    """
    speech_file_path = Path(__file__).parent / "speech.mp3"
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=prompt,
    )
    response.stream_to_file(speech_file_path)

    if not speech_file_path.is_file():
        raise FileNotFoundError(f"Audio file not created at {speech_file_path}")

    return str(speech_file_path)


@dp.message(CommandStart())
async def handle_start_command(message: Message):
    """
    Handles the start command when a user first interacts with the bot. Sets up the user's language preference
    and sends a welcome message.

    :param message: The message object containing the start command.
    """
    user_id = message.from_user.id
    user_messages[user_id] = []
    user_languages.setdefault(user_id, 'en')
    await message.reply(message_templates[user_languages[user_id]]['start'])


@dp.message()
async def handle_generic_message(message: Message):
    """
    Handles any generic messages that are not commands. Stores user's messages and gets responses from GPT model.

    :param message: The message object containing the user's text.
    """
    user_id = message.from_user.id
    language = user_languages.get(user_id, 'en')
    user_input = message.text.strip()

    if user_id not in user_messages:
        user_messages[user_id] = []

    user_messages[user_id].append({"role": "user", "content": user_input})
    try:
        gpt_response = await ask_gpt(user_id)
    except Exception as e:
        await handle_errors(e, message, language)
    else:
        await message.answer(gpt_response)  # Only called if no exceptions are raised.


async def ask_gpt(user_id: int) -> str:
    """
    Generates a response from the GPT model based on the conversation history of the specified user.

    :param user_id: The user ID for whom the response is being generated.
    :return: A string containing the GPT model's response.
    """
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=user_messages[user_id],
        temperature=0,
        user=str(user_id)
    )
    return response.choices[0].message.content


async def handle_errors(exception, message, language):
    """
    Handles errors and sends an appropriate response to the user.

    :param exception: The caught exception.
    :param message: The message object to reply to.
    :param language: The user's selected language.
    """
    error_type = type(exception)
    error_message = {
        APIConnectionError: 'network_error',
        APITimeoutError: 'network_error',
        BadRequestError: 'request_error',
        NotFoundError: 'request_error',
        RateLimitError: 'limit_error',
        UnprocessableEntityError: 'client_error',
        ConflictError: 'client_error',
        AuthenticationError: 'auth_error',
        PermissionDeniedError: 'auth_error',
        InternalServerError: 'server_error',
        FileNotFoundError: 'sever_error',
        ValueError: 'server_error'
    }.get(error_type, 'error')

    logging.error(f"{error_type.__name__}: {exception}")
    if error_type is not Exception:
        logging.error(traceback.format_exc())

    await message.reply(message_templates[language][error_message])


async def main():
    """
    Main function to start the bot polling.
    """
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
