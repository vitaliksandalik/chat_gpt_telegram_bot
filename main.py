import os
import json
import asyncio
import logging
import traceback
import sys
from datetime import datetime
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
LIMITS = {
    "ask_limit": 10,
    "audio_limit": 2,
    "image_limit": 10
}

bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
client = OpenAI()


def load_user_data():
    try:
        with open("user_data.json", "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {"users": {}}


def save_user_data(data):
    with open("user_data.json", "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def get_user_info(user_id, info_type):
    return user_data["users"].get(str(user_id), {}).get(info_type, [])


def set_user_info(user_id, info_type, data):
    user_data["users"].setdefault(str(user_id), {})[info_type] = data
    save_user_data(user_data)


def add_user_usage(user_id, usage_type, data):
    user_usage = get_user_info(user_id, usage_type)
    user_usage.append(data)
    set_user_info(user_id, usage_type, user_usage)


def has_reached_daily_limit(user_id, limit):
    today = datetime.now().strftime("%Y-%m-%d")
    usage = {
        "ask_limit": "ask_usage",
        "image_limit": "image_usage",
        "audio_limit": "audio_usage"
    }
    daily_usage = [usage for usage in get_user_info(user_id, usage[limit]) if usage['date'] == today]
    return len(daily_usage) >= LIMITS[limit]


user_data = load_user_data()

# Language selection keyboard setup
language_keyboard = InlineKeyboardBuilder()
language_keyboard.add(
    types.InlineKeyboardButton(text="English🇬🇧", callback_data="en"),
    types.InlineKeyboardButton(text="Український🇺🇦", callback_data="ua")
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
    set_user_info(user_id, "language", callback.data)
    language = get_user_info(user_id, "language")
    await callback.message.answer(text=message_templates[language]["language_confirmation"])


@dp.message(Command("language"))
async def handle_language_command(message: types.Message):
    """
    Handles the '/language' command. It sends a message to the user with available language options.

    :param message: The message object containing the command.
    """
    user_id = message.from_user.id
    language = get_user_info(user_id, "language")
    await message.answer(text=message_templates[language]["language_selection"],
                         reply_markup=language_keyboard.as_markup())


@dp.message(Command("help"))
async def handle_help_command(message: types.Message):
    """
    Handles the '/help' command. Sends a help message to the user explaining how to interact with the bot.

    :param message: The message object containing the command.
    """
    user_id = message.from_user.id
    language = get_user_info(user_id, "language")
    await message.answer(text=message_templates[language]["help"])


@dp.message(Command("image"))
async def handle_image_command(message: types.Message):
    """
    Handles the '/image' command to generate and send an image based on the user's text prompt.

    :param message: The message object containing the command and the prompt.
    """
    user_id = message.from_user.id
    language = get_user_info(user_id, "language")

    if has_reached_daily_limit(user_id, "image_limit"):
        await message.reply(message_templates[language]['image_limit_reached'])
        return

    prompt = message.text.replace("/image", "").strip()

    if not prompt:
        await message.reply(message_templates[language]["image_prompt"])
        return

    processing_message = await message.reply(message_templates[language]["processing"])
    try:
        image_url = await generate_image(prompt, user_id)
        add_user_usage(user_id, "image_usage",
                       {
                           "prompt": prompt,
                           "image_url": image_url,
                           "date": datetime.now().strftime("%Y-%m-%d")
                            })
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
    print(response.data[0].url)
    return response.data[0].url


@dp.message(Command("audio"))
async def handle_audio_command(message: types.Message):
    """
    Handles the '/audio' command to generate and send an audio file based on the user's text prompt.

    :param message: The message object containing the command and the prompt.
    """
    user_id = message.from_user.id
    language = get_user_info(user_id, "language")

    if has_reached_daily_limit(user_id, "audio_limit"):
        await message.reply(message_templates[language]['audio_limit_reached'])
        return

    prompt = message.text.replace("/audio", "").strip()
    add_user_usage(user_id, "audio_usage",
                   {
                        "prompt": prompt,
                        "date": datetime.now().strftime("%Y-%m-%d")
                        })

    if not prompt:
        await message.reply(message_templates[language]["audio_prompt"])
        return

    processing_message = await message.reply(message_templates[language]["processing"])
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


@dp.message(F.content_type.in_({"voice", "audio"}))
async def handle_audio_message(message: Message):
    """
    Handles audio and voice messages by transcribing their content.

    :param message: The message object containing the voice or audio file.
    """
    user_id = message.from_user.id
    language = get_user_info(user_id, "language")

    file_id = message.voice.file_id if message.voice else message.audio.file_id

    file = await bot.get_file(file_id)
    file_path = file.file_path
    await bot.download_file(file_path, "audio.mp3")

    try:
        transcript = await transcript_audio("audio.mp3")
        await message.reply(transcript)
    except Exception as e:
        await handle_errors(e, message, language)


async def transcript_audio(audio) -> str:
    """
    Transcribes the audio content to text.

    :param audio: The file path of the audio file to be transcribed.
    :return: A string representing the transcription of the audio.
    """
    with open(f"{audio}", "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )
    return str(transcript)


@dp.message(CommandStart())
async def handle_start_command(message: Message):
    """
    Handles the start command when a user first interacts with the bot. Sets up the user's language preference
    and sends a welcome message.

    :param message: The message object containing the start command.
    """
    user_id = message.from_user.id
    username = message.from_user.username

    # Initialize user data if not existing
    if str(user_id) not in user_data["users"]:
        user_data["users"][str(user_id)] = {
            "username": username,
            "language": "en",
            "ask_usage": [],
            "image_usage": [],
            "audio_usage": []
        }
        save_user_data(user_data)

    language = get_user_info(user_id, "language")
    await message.reply(message_templates[language]["start"])


@dp.message(Command("ask"))
async def handle_generic_message(message: Message):
    """
    Handles ask command. Stores user's messages and gets responses from GPT model.

    :param message: The message object containing the user's text.
    """
    user_id = message.from_user.id
    language = get_user_info(user_id, "language")
    user_input = message.text.replace("/ask", "").strip()

    if has_reached_daily_limit(user_id, "ask_limit"):
        await message.reply(message_templates[language]['ask_limit_reached'])
        return

    if not user_input:
        await message.reply(message_templates[language]["ask"])
        return

    # Add user input to ask_usage and update user data
    add_user_usage(user_id, "ask_usage",
                   {
                           "role": "user",
                           "content": user_input,
                           "date": datetime.now().strftime("%Y-%m-%d")
                         })

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

    user_ask_history = get_user_info(user_id, "ask_usage")

    messages = [{key: value for key, value in ask.items() if key in ("role", "content")} for ask in user_ask_history]

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
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
        APIConnectionError: "network_error",
        APITimeoutError: "network_error",
        BadRequestError: "request_error",
        NotFoundError: "request_error",
        RateLimitError: "limit_error",
        UnprocessableEntityError: "client_error",
        ConflictError: "client_error",
        AuthenticationError: "auth_error",
        PermissionDeniedError: "auth_error",
        InternalServerError: "server_error",
        FileNotFoundError: "sever_error",
        ValueError: "server_error"
    }.get(error_type, "error")

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
