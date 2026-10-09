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

# --- СПИСОК БЛЮД ДЛЯ КОЛЕСА ФОРТУНЫ ---
DISHES = [
    "Ролл Цыпа (378 ₽) — хит продаж! 🌯",
    "Ролл Армянский (404 ₽) — с армянскими специями! 🌯",
    "Mac & Cheese Фрайс (419 ₽) — сыр, рожки и фри! 🧀",
    "Мак &Чизос (419 ₽) — мегасырный с читос! 🧀",
    "Пицца Танос (1981 ₽) — для настоящих гурманов! 🍕",
    "Курочка+подружка (1263 ₽) — идеальный комбо на двоих! 🍗",
    "Баскет Пэли Мэни Пакьяо (631 ₽) — азиатские пельмени! 🥟",
    "10 крыльев (899 ₽) — хрустящие, в оригинальной панировке! 🍗",
    "Пицца Цезарь Power (549 ₽) — 25 см сытного удовольствия! 🍕",
    "Комбо набор #1 (1643 ₽) — крылья, голени и фри! 🍟"
]

# --- ШУТКИ ПРО ЕДУ ---
JOKES = [
    "— Почему курица перешла дорогу?\n— Потому что ты заказал её с доставкой! 🐔🚗",
    "— Что сказал сыр, когда его положили в Mac & Cheese?\n— «Я в своей тарелке!» 🧀",
    "— Почему ролл никогда не грустит?\n— Потому что он всегда завёрнут с любовью! 🌯❤️",
    "— Сколько нужно программистов, чтобы приготовить крылышки?\n— Ни одного, у нас есть бот! 🤖🍗",
    "— Что общего у пиццы и хорошего настроения?\n— И то, и другое хочется ещё! 🍕😎",
    "— Почему картошка фри всегда в топе?\n— Потому что она знает, как найти подход к каждому! 🍟",
    "— Знаешь, почему наши крылья такие вкусные?\n— Они прошли курсы повышения хрусткости! 🍗📚",
    "— Что сказал соус BBQ котлете?\n— «Держись, я тебя прикрою!» 🍖",
    "— Почему клиент всегда прав?\n— Потому что он заказывает у нас! 😄🍔",
    "— Как называется страх перед пустой тарелкой?\n— Опустотофобия! 🍽️😱"
]

# --- КОМПЛИМЕНТЫ ---
COMPLIMENTS = [
    "Ты сегодня просто огонь! 🔥 Даже наша печь завидует.",
    "С тобой приятно иметь дело! 😎 Настоящий ценитель вкуса.",
    "Ты — тот самый клиент, ради которого мы готовим! ❤️",
    "У тебя отличный вкус! 🍗 Прям как у нашего шефа.",
    "Ты выглядишь на миллион! 💰 А наш ролл — всего на 378.",
    "С тобой даже понедельник не страшен! 😄",
    "Ты — причина, по которой курочка несёт яйца с улыбкой! 🐔😊",
    "Ты легенда! 🏆 И заслуживаешь только самое вкусное.",
    "Твоя харизма сильнее, чем соус остро-вкусно! 🌶️😎",
    "Спасибо, что ты есть! Без тебя наша кухня была бы скучной. 🍳❤️"
]

# --- ФРАЗЫ ДЛЯ РАЗНЫХ СЛУЧАЕВ ---
HELLO_PHRASES = [
    'Здарова! 👋 Голоден? Я помогу выбрать, что заказать. Жми кнопки ниже!',
    'Привет! 👋 Я бот-помощник «Курочка рядом». Что будем кушать сегодня? 😋',
    'О, привет! 👋 Соскучился по вкусняшкам? Выбирай, что тебе по душе!',
    'Курочка рядом на связи! 🐔 Чем могу помочь? Жми кнопки!'
]

UNKNOWN_PHRASES = [
    'Хм, сложный вопрос! 🤔 Давай лучше закажем что-нибудь вкусное. Жми кнопки! 👇',
    'Я пока еще учусь понимать людей. 😅 Тыкни на кнопку, я все покажу!',
    'Не, ну я конечно умный, но не настолько. 😂 Давай лучше закажем что-нибудь вкусное!',
    'Ого, ты меня озадачил! 🤯 Но я всё равно знаю, что тебе нужно — вкусная еда. Жми кнопку! 👇',
    'Так-так, думаю... 🧐 Не, не думается. Давай просто закажем? Кнопки внизу 👇'
]

FORTUNE_PHRASES = [
    "Крутим барабан... 🎰 Выпало:",
    "Фортуна улыбается тебе! 😉 Сегодня твой выбор:",
    "Рандом решил за тебя! 🎲 Бери это:",
    "Вот что советует наша курочка: 🐔",
    "Огонь! 🔥 Попробуй сегодня это:"
]

MOOD_PHRASES = [
    "Держи порцию позитива! 😄",
    "Лови заряд хорошего настроения! ⚡",
    "Специально для тебя: 🎁",
    "От нашей курочки с любовью: 🐔❤️",
    "Ням-ням, вот тебе комплимент: 😋"
]

# --- ОБЫЧНАЯ КЛАВИАТУРА (внизу экрана) ---
def get_main_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('🛒 Где заказать', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('😋 Что вкуснее?', color=VkKeyboardColor.POSITIVE)
    
    keyboard.add_line()
    keyboard.add_button('🔥 Что чаще берут?', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('🎲 Колесо фортуны', color=VkKeyboardColor.POSITIVE)
    
    keyboard.add_line()
    keyboard.add_button('😄 Поднять настроение', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('🌐 Наш сайт', color=VkKeyboardColor.PRIMARY)
    
    keyboard.add_line()
    keyboard.add_button('✍️ Оставить отзыв', color=VkKeyboardColor.NEGATIVE)
    
    return keyboard.get_keyboard()

# --- INLINE-КЛАВИАТУРА (кнопки внутри сообщения) ---
def get_inline_keyboard():
    # inline=True — кнопки прикрепляются к сообщению
    keyboard = VkKeyboard(inline=True)
    
    # Первая строка — заказ
    keyboard.add_openlink_button(label='🌐 Заказать на сайте', link='https://курлайк.рф')
    keyboard.add_line()
    keyboard.add_openlink_button(label='📱 Скачать приложение', link='https://xn--80asbcc3au.xn--p1ai/qr-mobile')
    keyboard.add_line()
    keyboard.add_openlink_button(label='📞 Позвонить', link='tel:+79145182212')
    
    return keyboard.get_keyboard()

# --- ОСНОВНАЯ ЛОГИКА ---
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        msg = event.text.lower()
        user_id = event.user_id

        # 1. Приветствие (с комплиментом!)
        if msg in ['начать', 'привет', 'start', 'меню', 'помощь', 'здарова', 'хай']:
            greeting = random.choice(HELLO_PHRASES)
            compliment = random.choice(COMPLIMENTS)
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': f'{greeting}\n\nКстати, {compliment}',
                'keyboard': get_main_keyboard(),
                'random_id': 0
            })
        
        # 2. Где заказать (ОБНОВЛЕНО: inline-кнопки!)
        elif msg == '🛒 где заказать' or 'заказ' in msg:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'Заказать наши вкусняшки можно так:\n👇 Выбирай удобный способ!',
                'keyboard': get_inline_keyboard(),
                'random_id': 0
            })
            
        # 3. Что вкуснее?
        elif msg == '😋 что вкуснее?' or 'вкусн' in msg or 'посовет' in msg:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'Если хочешь попробовать что-то новое, рекомендую:\n1. Комбо курочка+подружка (1263 ₽) — взрыв курицы! 🍗\n2. Mac & Cheese Фрайс (419 ₽) — сыр, рожки и фри, идеально! 🧀\n3. Баскет Пэли мэни пакьяо (631 ₽) — для Всех! 🥟\nОни просто огонь! 🔥',
                'random_id': 0
            })

        # 4. Что чаще берут?
        elif msg == '🔥 что чаще берут?' or 'хит' in msg or 'популярн' in msg or 'берут' in msg:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'Наши бестселлеры, которые заказывают чаще всего:\n🥇 Цыпа (378 ₽) — хит продаж!\n🥈 Курочка+друг (1263 ₽) — идеальный комбо-набор на двоих.\n🥉 Пицца «ТАНОС» (1981 ₽) — для настоящих гурманов.\nПопробуй, не пожалеешь! 😉',
                'random_id': 0
            })
            
        # 5. Наш сайт
        elif msg == '🌐 наш сайт' or 'сайт' in msg:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'Вот ссылка на наш сайт, там есть всё меню и акции:\n👉 https://курлайк.рф',
                'random_id': 0
            })

        # 6. Оставить отзыв (обновлён ID!)
        elif msg == '✍️ оставить отзыв' or 'отзыв' in msg:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'Нам очень важно твое мнение! ❤️ Пожалуйста, напиши свой отзыв или предложение мне в личные сообщения:\n👉 https://vk.com/write58971558\n\nЯ всё прочитаю и обязательно отвечу! 😉',
                'random_id': 0
            })

        # 7. КОЛЕСО ФОРТУНЫ
        elif msg == '🎲 колесо фортуны' or 'колесо' in msg or 'не знаю' in msg or 'рандом' in msg:
            dish = random.choice(DISHES)
            phrase = random.choice(FORTUNE_PHRASES)
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': f'{phrase}\n\n{dish}\n\nЗаказать можно тут: https://курлайк.рф',
                'random_id': 0
            })

        # 8. ПОДНЯТЬ НАСТРОЕНИЕ
        elif msg == '😄 поднять настроение' or 'шутк' in msg or 'анекдот' in msg or 'комплимент' in msg or 'настроение' in msg:
            if random.choice([True, False]):
                text = random.choice(JOKES)
            else:
                text = random.choice(COMPLIMENTS)
            
            phrase = random.choice(MOOD_PHRASES)
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': f'{phrase}\n\n{text}',
                'keyboard': get_main_keyboard(),
                'random_id': 0
            })
        
        # 9. Умный поиск по меню
        elif 'ролл' in msg:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'У нас есть офигенные роллы! 🌯\nПопробуй «Ролл Цыпа» (378 ₽) или «Ролл Армянский» (404 ₽).\nВсе роллы смотри на сайте: https://курлайк.рф',
                'random_id': 0
            })
        elif 'пицц' in msg:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'Пицца — это святое! 🍕\nВозьми «Пицца Танос» (1981 ₽) или «Пицца Цезарь Power» (549 ₽).\nОни огромные и очень вкусные!',
                'random_id': 0
            })
        elif 'сыр' in msg or 'мак' in msg:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'Сырная тема — это к нам! 🧀\nОбязательно попробуй «Mac & Cheese Фрайс» (419 ₽) или «Мак &Чизос» (419 ₽).',
                'random_id': 0
            })
        elif 'крыл' in msg:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'Крылышки — наша гордость! 🍗\n5 крыльев — 465 ₽, 10 крыльев — 899 ₽, 15 крыльев — 1302 ₽.\nЕсть острые, BBQ и Ну мед!',
                'random_id': 0
            })

        # 10. Если бот не знает команду
        else:
            if random.choice([True, False]):
                bonus = random.choice(JOKES)
            else:
                bonus = random.choice(COMPLIMENTS)
            
            phrase = random.choice(UNKNOWN_PHRASES)
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': f'{bonus}\n\n{phrase}',
                'keyboard': get_main_keyboard(),
                'random_id': 0
            })
