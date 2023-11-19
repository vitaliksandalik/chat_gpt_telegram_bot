message_templates = {
    'en': {
        'start': "Hello, I'm bot your GPT assistant. Enter /help or just start asking questions",
        'ask': 'Please add a description of the image after the /ask command. '
               'For example, /ask 10 facts about coffee',
        'image_prompt': 'Please add a description of the image after the /image command. '
                        'For example, /image Neon City.',
        'audio_prompt': 'Please add a text after the /audio command. For example, /audio My name is Vitalii.',
        'audio_error': 'An error occurred during audio generation',
        'image_error': 'An error occurred during image generation',
        'network_error': 'A network error occurred. Please check your connection and try again.',
        'request_error': 'There was an error in processing your request. Your prompt may contain text that is not '
                         'allowed by our safety system.',
        'limit_error': 'Limit error. Try again later.',
        'client_error': 'A client-side error occurred. Please check your request and try again.',
        'auth_error': 'Authentication or authorization error. Please check your credentials or permissions.',
        'server_error': 'A server-side error occurred. Please try again later.',
        'help': 'You can interact with this bot using commands like /ask, /language, /image, /audio and /help.',
        'language_confirmation': "Language has been set to English.",
        'language_selection': "Available in 2 languages:",
        'processing': "Your request is being processed, please wait.",
        'error': "An error occurred during processing:"
    },
    'ua': {
        'start': "Привіт, я твій GPT помічник. Введіть /help",
        'ask': 'Будь ласка, додайте опис запиту після команди  /ask. Наприклад,  /ask 10 фактів про Київ',
        'image_prompt': 'Будь ласка, додайте опис зображення після команди  /image. Наприклад,  /image Неонове місто',
        'audio_prompt': 'Будь ласка, додайте текст після команди  /audio. Наприклад,  /audio Мене звати Віталій',
        'audio_error': 'Під час створення аудіо сталася помилка',
        'image_error': 'Під час створення зображення сталася помилка',
        'network_error': 'Сталася помилка мережі. Будь ласка, перевірте ваше з\'єднання та спробуйте ще раз.',
        'request_error': 'Під час обробки вашого запиту виникла помилка. Моливо, ваш запит містить текст, '
                         'який заборонено системою безпеки.',
        'limit_error': 'Ліміт досягнутий, спробуйте трошки пізніше.',
        'client_error': 'Сталася помилка на стороні клієнта. Будь ласка, перевірте ваш запит і спробуйте знову.',
        'auth_error': 'Помилка аутентифікації або авторизації. Будь ласка, перевірте ваші дані або дозволи.',
        'server_error': 'Сталася помилка на сервері. Будь ласка, спробуйте пізніше.',
        'help': 'Ви можете взаємодіяти з цим ботом за допомогою таких команд, як /ask, /language, /image, /audio та /help.',
        'language_confirmation': "Обрана українська мова",
        'language_selection': "В наявності 2 мови",
        'processing': "Ваш запит обробляється, зачекайте.",
        'error': "Під час обробки сталася помилка:"
    }
}
