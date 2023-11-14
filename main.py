import os
import asyncio
import logging
import sys
import json

from openai import OpenAI


from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.markdown import hbold

from dotenv import load_dotenv

load_dotenv()  # This is new, to load the environment variables from .env file

TOKEN = os.getenv("TOKEN")  # Bot token

dp = Dispatcher()
client = OpenAI()


def show_json(obj):
    print(json.loads(obj.model_dump_json()))


async def ask_gpt(question: str) -> str:
    # Function to ask GPT a question and get the response
    messages = [
        {"role": "system", "content": 'You answer question about Web  services.'},
        {"role": "user", "content": question},
    ]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0,
    )

    return response.choices[0].message.content


@dp.message()
async def gpt_response_handler(message: types.Message) -> None:
    # GPT response handler
    gpt_response = await ask_gpt(message.text)
    await message.answer(gpt_response)


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """ This handler receives messages with `/start` command """
    await message.answer(f"Hello, {hbold(message.from_user.full_name)}!")


async def main() -> None:
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
