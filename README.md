
# ChatGPT Telegram Bot

## Sneak Peeks

![sneek-peek](https://github.com/vitaliksandalik/chat_gpt_telegram_bot/assets/102806612/3ffb5ff6-9620-4689-a9c6-aa97cdfc4f42)

## Introduction

This guide provides step-by-step instructions on how to set up and run the ChatGPT Telegram Bot. This bot is designed to interact with users via Telegram, leveraging the power of GPT models to provide informative and engaging responses.

## Prerequisites

Before you begin, ensure you have Python 3.8 or newer installed on your system. You can download Python [here](https://www.python.org/downloads/).

## Setup Instructions

1. **Clone or Download the Bot**

   First, you need to have the bot's code on your local machine. If you're familiar with `git`, you can clone this repository. Otherwise, download the provided files to a directory on your computer.

2. **Install Dependencies**

   Open a terminal or command prompt in the directory where you've placed the bot's files. Then, install the required Python packages with the following command:
   ```
   pip install -r requirements.txt
   ```
Note: Some users may encounter an issue where the command pip is not recognized. In such cases, please try using pip3 instead. Similarly, if you encounter issues with the python command, use python3 as an alternative.

3. **Telegram Bot Token**

   You will need a Telegram Bot Token. If you don't have one, you can create a bot and obtain a token by chatting with [BotFather](https://t.me/botfather) on Telegram.

4. **Open AI API key**
 
    You will also need an Open AI API KEY. [You can get it here](https://platform.openai.com/api-keys)
    

5. **Configure the `.env` File**

   Rename `.env.example` to `.env` and open it in a text editor. Replace `YOUR_TELEGRAM_BOT_TOKEN_HERE` with your actual Telegram Bot Token and `OPENAI_API_KEY` with your actual OPEN AI API Key.

   Example `.env` content:
   ```
    TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
    OPENAI_API_KEY=ab-CDEFGH5cjXnvxQmoJ1HgT3BlbkFJocmlAempDWyVQpY3XsJm
   
   ```

6. **Start the Bot**

   With everything set up, you can now start the bot by running the following command in your terminal or command prompt:
   ```
   python main.py
   ```


## Usage

Once the bot is running, you can interact with it by sending commands and messages through the Telegram app. Here are the commands the bot can process and examples of how to use them:

- `/start`: Initializes interaction with the bot and sets up user preferences.

- `/language`: Changes the user's preferred language.

- `/help`: Provides information on how to interact with the bot and the features it offers.

- `/image`: Generates and sends an image based on a text prompt you provide.

  ```
  /image your prompt here
  ```

- `/audio`: Generates and sends an audio file based on a text prompt. 

  ```
  /audio your prompt here
  ```

- `/ask`: Interacts with the bot's GPT model to get responses to queries or engage in conversation.

  ```
  /ask your question or message here
  ```
  
Remember, the bot's ability to respond effectively depends on the prompts you provide, so be clear and specific with your requests.


## Files Description

- `main.py`: The main script that runs the bot.
- `message_templates.py`: Contains message templates for the bot's responses.
- `requirements.txt`: Lists all the Python packages that need to be installed.
- `user_data.json`: An example file showing how user data can be stored.

## Support

If you encounter any issues or have questions, feel free to open an issue in the repository (if available) or contact the developer directly on Telegram.
