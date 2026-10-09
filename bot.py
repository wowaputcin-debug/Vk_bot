import os
import random
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

# --- НАСТРОЙКИ ---
TOKEN = os.getenv('VK_TOKEN')

# --- ПОДКЛЮЧЕНИЕ ---
print("Бот запускается...")
vk_session = vk_api.VkApi(token=TOKEN)
longpoll = VkLongPoll(vk_session)
print("Бот готов и ждет сообщений!")

# --- ФУНКЦИЯ ДЛЯ КЛАВИАТУРЫ ---
def get_main_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('🛒 Где заказать', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('😋 Что вкуснее?', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('🔥 Что чаще берут?', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('🌐 Наш сайт', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('✍️ Оставить отзыв', color=VkKeyboardColor.NEGATIVE)
    return keyboard.get_keyboard()

# --- БАЗА ЗНАНИЙ (УМНЫЕ ОТВЕТЫ) ---
HELLO_PHRASES = [
    'Здарова! 👋 Голоден? Я помогу выбрать, что заказать. Жми кнопки ниже!',
    'Привет! 👋 Я бот-помощник «Курочка рядом». Что будем кушать сегодня? 😋',
    'О, привет! 👋 Соскучился по вкусняшкам? Выбирай, что тебе по душе!',
    'Курочка рядом на связи! 🐔 Чем могу помочь? Жми кнопки!'
]

UNKNOWN_PHRASES = [
    'Я тебя не совсем понял. 😔 Давай по кнопкам? 👇',
    'Хм, сложный вопрос! 🤔 Лучше выбери что-то из меню:',
    'Я пока еще учусь понимать людей. 😅 Тыкни на кнопку, я все покажу!',
    'Не, ну я конечно умный, но не настолько. 😂 Давай лучше закажем что-нибудь вкусное!'
]

# --- ЛОГИКА ОБРАБОТКИ ---
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        msg = event.text.lower()
        user_id = event.user_id

        # 1. Приветствие
        if msg in ['начать', 'привет', 'start', 'меню', 'помощь', 'здарова', 'хай']:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': random.choice(HELLO_PHRASES),
                'keyboard': get_main_keyboard(),
                'random_id': 0
            })
        
        # 2. Где заказать
        elif msg == '🛒 где заказать' or 'заказ' in msg:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'Заказать наши вкусняшки можно на сайте:\n👉 https://курлайк.рф\n\nТам всё меню, акции и быстрая доставка! 🚀',
                'random_id': 0
            })
            
        # 3. Что вкуснее? (Умный ответ)
        elif msg == '😋 что вкуснее?' or 'вкусн' in msg or 'посовет' in msg:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'Если хочешь попробовать что-то новое, рекомендую:\n1. Ролл Мак Чиз (399 ₽) — сырный взрыв! 🧀\n2. Mac & Cheese Фрайс (419 ₽) — сыр, рожки и фри, идеально!\n3. Пицца «Пипец 1992» (2000 ₽) — для большой компании! 🍕\nОни просто огонь! 🔥',
                'random_id': 0
            })

        # 4. Что чаще берут? (Умный ответ)
        elif msg == '🔥 что чаще берут?' or 'хит' in msg or 'популярн' in msg or 'берут' in msg:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'Наши бестселлеры, которые заказывают чаще всего:\n🥇 Ролл Мак Чиз (399 ₽) — хит продаж!\n🥈 Курочка+подружка (990 ₽) — идеальный комбо-набор на двоих.\n🥉 Пицца «Мортальный комбо» (2000 ₽) — для настоящих гурманов.\nПопробуй, не пожалеешь! 😉',
                'random_id': 0
            })
            
        # 5. Наш сайт
        elif msg == '🌐 наш сайт' or 'сайт' in msg:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'Вот ссылка на наш сайт, там есть всё меню и акции:\n👉 https://курлайк.рф',
                'random_id': 0
            })

        # 6. Оставить отзыв
        elif msg == '✍️ оставить отзыв' or 'отзыв' in msg:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'Нам очень важно твое мнение! ❤️ Пожалуйста, напиши свой отзыв или предложение мне в личные сообщения:\n👉 https://vk.com/write58971558\n\nЯ всё прочитаю и обязательно отвечу! 😉',
                'random_id': 0
            })
        
        # 7. Умный поиск по меню (если написали просто слово)
        elif 'ролл' in msg:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'У нас есть офигенные роллы! 🌯\nПопробуй «Ролл Мак Чиз» (399 ₽) или «Ролл Армянский» (367 ₽).\nВсе роллы смотри на сайте: https://курлайк.рф',
                'random_id': 0
            })
        elif 'пицц' in msg:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'Пицца — это святое! 🍕\nВозьми «Мортальный комбо» (2000 ₽) или «Пипец 1992» (2000 ₽).\nОни огромные и очень вкусные!',
                'random_id': 0
            })
        elif 'сыр' in msg or 'мак' in msg:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'Сырная тема — это к нам! 🧀\nОбязательно попробуй «Mac & Cheese Фрайс» (419 ₽) или «Ролл Мак Чиз» (399 ₽).',
                'random_id': 0
            })

        # 8. Если бот не знает команду
        else:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': random.choice(UNKNOWN_PHRASES),
                'keyboard': get_main_keyboard(),
                'random_id': 0
            })
