import os
import json
import random
import string
import vk_api
from datetime import datetime
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

# --- НАСТРОЙКИ ---
TOKEN = os.getenv('VK_TOKEN')
STATE_FILE = 'fortunes.json'   # файл для сохранения попыток
MAX_ATTEMPTS = 3

# --- ПОДКЛЮЧЕНИЕ ---
print("Бот запускается...")
vk_session = vk_api.VkApi(token=TOKEN)
longpoll = VkLongPoll(vk_session)
print("Бот готов и ждет сообщений!")

# --- ФАЙЛ СОСТОЯНИЯ (чтобы попытки не сбрасывались) ---
def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_state(state):
    try:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка сохранения: {e}")

def get_user_state(user_id):
    today = datetime.now().strftime('%Y-%m-%d')
    key = str(user_id)
    state = load_state()
    user = state.get(key, {})
    if user.get('date') != today:
        user = {
            'date': today,
            'attempts': MAX_ATTEMPTS,
            'last_msg_id': None,
            'codes': user.get('codes', [])[-50:]  # храним максимум 50 кодов
        }
    return state, user

def save_user_state(state, user_id, user):
    state[str(user_id)] = user
    save_state(state)

def generate_code():
    chars = string.ascii_uppercase + string.digits
    return 'FORT-' + ''.join(random.choices(chars, k=6))

# --- ПРИЗЫ (вес = вероятность) ---
# 40% скидка/подарок, 60% комплименты и мелочи
FORTUNE_REWARDS = [
    {"text": "🎁 Соус в подарок к любому заказу!", "weight": 25, "tier": "common"},
    {"text": "😎 Комплимент от шефа: ты выглядишь на миллион! Но увы, без скидки 😅", "weight": 15, "tier": "common"},
    {"text": "🍟 Картофель фри в подарок при заказе от 500 ₽!", "weight": 15, "tier": "common"},
    {"text": "💸 Скидка 5% на весь заказ!", "weight": 12, "tier": "uncommon"},
    {"text": "🥤 Напиток в подарок к любому комбо!", "weight": 10, "tier": "uncommon"},
    {"text": "🌯 Ролл Цыпа в подарок при заказе от 1000 ₽!", "weight": 6, "tier": "rare"},
    {"text": "💸 Скидка 10% на весь заказ!", "weight": 5, "tier": "rare"},
    {"text": "🧀 Mac & Cheese Фрайс в подарок при заказе от 800 ₽!", "weight": 2.5, "tier": "epic"},
    {"text": "🍕 Пицца 25 см в подарок при заказе от 1500 ₽!", "weight": 1.3, "tier": "epic"},
    {"text": "🔥 ДЖЕКПОТ! Скидка 25% на весь заказ!", "weight": 0.2, "tier": "legendary"},
]

TIER_EMOJI = {'common': '🎈', 'uncommon': '🎁', 'rare': '💎', 'epic': '👑', 'legendary': '🔥'}

def spin_wheel():
    total = sum(r['weight'] for r in FORTUNE_REWARDS)
    r = random.uniform(0, total)
    upto = 0
    for reward in FORTUNE_REWARDS:
        upto += reward['weight']
        if r <= upto:
            return reward
    return FORTUNE_REWARDS[0]

# --- ШУТКИ, КОМПЛИМЕНТЫ, ФРАЗЫ ---
JOKES = [
    "— Почему курица перешла дорогу?\n— Потому что ты заказал её с доставкой! 🐔🚗",
    "— Что сказал сыр в Mac & Cheese?\n— «Я в своей тарелке!» 🧀",
    "— Почему ролл не грустит?\n— Он всегда завёрнут с любовью! 🌯❤️",
    "— Сколько программистов нужно, чтоб приготовить крылышки?\n— Ни одного, у нас есть бот! 🤖🍗",
    "— Что общего у пиццы и настроения?\n— И то, и другое хочется ещё! 🍕😎",
    "— Почему картошка фри в топе?\n— Она знает подход к каждому! 🍟",
    "— Почему наши крылья вкусные?\n— Прошли курсы повышения хрусткости! 🍗📚",
]
COMPLIMENTS = [
    "Ты сегодня просто огонь! 🔥",
    "С тобой приятно иметь дело! 😎",
    "У тебя отличный вкус! 🍗",
    "Ты выглядишь на миллион! 💰",
    "Ты легенда! 🏆",
    "Твоя харизма сильнее соуса остро-вкусно! 🌶️",
]
HELLO_PHRASES = [
    'Здарова! 👋 Голоден? Жми кнопки!',
    'Привет! 👋 Что будем кушать сегодня? 😋',
    'О, привет! 👋 Соскучился по вкусняшкам?',
    'Курочка рядом на связи! 🐔',
]
UNKNOWN_PHRASES = [
    'Хм, сложный вопрос! 🤔 Давай лучше закажем вкусное. Жми кнопки! 👇',
    'Я пока учусь понимать людей. 😅 Тыкни на кнопку!',
    'Не, ну я умный, но не настолько. 😂 Давай закажем?',
]
FORTUNE_PHRASES = [
    "Крутим барабан... 🎰 Выпало:",
    "Фортуна улыбается! 😉 Твой выбор:",
    "Рандом решил за тебя! 🎲",
    "Огонь! 🔥 Попробуй сегодня это:",
]
MOOD_PHRASES = ["Держи позитив! 😄", "Лови заряд настроения! ⚡", "Специально для тебя: 🎁"]

# --- ОТВЕТЫ НА НЕЦЕЛЕВЫЕ ---
WORK_RESPONSE = 'Ого, ты хочешь к нам в команду? 🔥\n\nПо вопросам работы пиши сюда:\n👉 https://vk.com/write58971558'
PARTNERSHIP_RESPONSE = 'Спасибо за предложение! 🤝\n\nПо вопросам сотрудничества и рекламы:\n👉 https://vk.com/write58971558'
SPAM_RESPONSE = 'Ой, я бот и не разбираюсь в таких вопросах. 😅\n\nРеальные предложения — сюда:\n👉 https://vk.com/write58971558'

WORK_KEYWORDS = ['работ', 'вакан', 'устро', 'резюме', 'трудоустро', 'зарплат', 'подработ', 'повар', 'курьер']
PARTNERSHIP_KEYWORDS = ['сотруднич', 'партнер', 'партнёр', 'реклам', 'предложени', 'бартер', 'инвестиц', 'коллаб', 'продвижени', 'пиар']
SPAM_KEYWORDS = ['крипт', 'биткоин', 'заработок', 'пассивный доход', 'трейдинг', 'казино', 'ставк', 'форекс', 'накрутк']

# --- КЛАВИАТУРЫ ---
def get_main_keyboard():
    kb = VkKeyboard(one_time=False)
    kb.add_button('🛒 Где заказать', color=VkKeyboardColor.PRIMARY)
    kb.add_button('😋 Что вкуснее?', color=VkKeyboardColor.POSITIVE)
    kb.add_line()
    kb.add_button('🔥 Что чаще берут?', color=VkKeyboardColor.SECONDARY)
    kb.add_button('🎲 Колесо фортуны', color=VkKeyboardColor.POSITIVE)
    kb.add_line()
    kb.add_button('😄 Поднять настроение', color=VkKeyboardColor.POSITIVE)
    kb.add_button('🌐 Наш сайт', color=VkKeyboardColor.PRIMARY)
    kb.add_line()
    kb.add_button('✍️ Оставить отзыв', color=VkKeyboardColor.NEGATIVE)
    return kb.get_keyboard()

def get_fortune_keyboard(attempts_left):
    """Клавиатура после выигрыша: только 'Ещё раз', если попытки остались"""
    if attempts_left <= 0:
        return get_main_keyboard()
    kb = VkKeyboard(one_time=False)
    kb.add_button('🎲 Ещё раз', color=VkKeyboardColor.POSITIVE)
    kb.add_button('🛒 Где заказать', color=VkKeyboardColor.PRIMARY)
    return kb.get_keyboard()

def get_inline_keyboard():
    kb = VkKeyboard(inline=True)
    kb.add_openlink_button(label='🌐 Заказать на сайте', link='https://курлайк.рф')
    kb.add_line()
    kb.add_openlink_button(label='📱 Скачать приложение', link='https://xn--80asbcc3au.xn--p1ai/qr-mobile')
    return kb.get_keyboard()

# --- ФУНКЦИЯ КОЛЕСА ---
def handle_fortune(user_id):
    state, user = get_user_state(user_id)

    # Удаляем предыдущее сообщение с результатом
    if user.get('last_msg_id'):
        try:
            vk_session.method('messages.delete', {
                'message_ids': user['last_msg_id'],
                'delete_for_all': 1
            })
        except Exception as e:
            print(f"Не удалось удалить сообщение: {e}")
        user['last_msg_id'] = None

    # Попытки закончились
    if user['attempts'] <= 0:
        response = vk_session.method('messages.send', {
            'user_id': user_id,
            'message': '😢 Ты уже использовал все 3 попытки на сегодня!\n\nВозвращайся завтра за новой порцией удачи. А пока — закажи что-нибудь вкусное! 🍗',
            'keyboard': get_main_keyboard(),
            'random_id': 0
        })
        user['last_msg_id'] = response
        save_user_state(state, user_id, user)
        return

    # Крутим
    user['attempts'] -= 1
    reward = spin_wheel()
    code = generate_code()
    user['codes'].append({'code': code, 'reward': reward['text'], 'date': user['date']})
    attempts_left = user['attempts']

    emoji = TIER_EMOJI[reward['tier']]
    message = f"🎰 Крутим барабан...\n⏳ Три... Два... Один...\n\n{emoji} {reward['text']}\n\n"

    # Промокод только для реальных подарков
    if 'без скидки' not in reward['text']:
        message += f"🎟 Промокод: {code}\n📌 Покажи этот код при заказе.\n\n"

    if attempts_left > 0:
        message += f"🎯 Осталось попыток: {attempts_left}"
    else:
        message += "🎯 Это была твоя последняя попытка на сегодня!"

    response = vk_session.method('messages.send', {
        'user_id': user_id,
        'message': message,
        'keyboard': get_fortune_keyboard(attempts_left),
        'random_id': 0
    })
    user['last_msg_id'] = response
    save_user_state(state, user_id, user)

# --- ОСНОВНАЯ ЛОГИКА ---
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        msg = event.text.lower()
        user_id = event.user_id

        is_work = any(w in msg for w in WORK_KEYWORDS)
        is_partner = any(w in msg for w in PARTNERSHIP_KEYWORDS)
        is_spam = any(w in msg for w in SPAM_KEYWORDS)

        # 1. Работа / Сотрудничество / Спам
        if is_work:
            vk_session.method('messages.send', {'user_id': user_id, 'message': WORK_RESPONSE, 'random_id': 0})
        elif is_partner:
            vk_session.method('messages.send', {'user_id': user_id, 'message': PARTNERSHIP_RESPONSE, 'random_id': 0})
        elif is_spam:
            vk_session.method('messages.send', {'user_id': user_id, 'message': SPAM_RESPONSE, 'keyboard': get_main_keyboard(), 'random_id': 0})

        # 2. Приветствие
        elif msg in ['начать', 'привет', 'start', 'меню', 'помощь', 'здарова', 'хай']:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': f'{random.choice(HELLO_PHRASES)}\n\nКстати, {random.choice(COMPLIMENTS)}',
                'keyboard': get_main_keyboard(),
                'random_id': 0
            })

        # 3. КОЛЕСО ФОРТУНЫ (включая «Ещё раз»)
        elif 'колесо' in msg or msg == '🎲 ещё раз' or 'фортуны' in msg or 'рандом' in msg or 'не знаю' in msg:
            handle_fortune(user_id)

        # 4. Где заказать
        elif msg == '🛒 где заказать' or 'заказ' in msg:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'Заказать наши вкусняшки можно так:\n👇 Выбирай удобный способ!',
                'keyboard': get_inline_keyboard(),
                'random_id': 0
            })

        # 5. Что вкуснее?
        elif msg == '😋 что вкуснее?' or 'вкусн' in msg or 'посовет' in msg:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'Если хочешь попробовать новое:\n1. Комбо курочка+подружка (1263 ₽) — взрыв курицы! 🍗\n2. Mac & Cheese Фрайс (419 ₽) — сыр, рожки и фри! 🧀\n3. Баскет Пэли мэни пакьяо (631 ₽) — для всех! 🥟\nОни просто огонь! 🔥',
                'random_id': 0
            })

        # 6. Что чаще берут?
        elif msg == '🔥 что чаще берут?' or 'хит' in msg or 'популярн' in msg or 'берут' in msg:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'Наши бестселлеры:\n🥇 Цыпа (378 ₽) — хит продаж!\n🥈 Курочка+друг (1263 ₽) — комбо на двоих.\n🥉 Пицца «ТАНОС» (1981 ₽) — для гурманов.\nПопробуй! 😉',
                'random_id': 0
            })

        # 7. Наш сайт
        elif msg == '🌐 наш сайт' or 'сайт' in msg:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'Ссылка на сайт с меню и акциями:\n👉 https://курлайк.рф',
                'random_id': 0
            })

        # 8. Оставить отзыв
        elif msg == '✍️ оставить отзыв' or 'отзыв' in msg:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'Нам важно твоё мнение! ❤️ Напиши отзыв:\n👉 https://vk.com/write58971558',
                'random_id': 0
            })

        # 9. Поднять настроение
        elif msg == '😄 поднять настроение' or 'шутк' in msg or 'анекдот' in msg or 'комплимент' in msg or 'настроение' in msg:
            text = random.choice(JOKES) if random.choice([True, False]) else random.choice(COMPLIMENTS)
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': f'{random.choice(MOOD_PHRASES)}\n\n{text}',
                'keyboard': get_main_keyboard(),
                'random_id': 0
            })

        # 10. Умный поиск
        elif 'ролл' in msg:
            vk_session.method('messages.send', {'user_id': user_id, 'message': 'У нас офигенные роллы! 🌯\n«Ролл Цыпа» (378 ₽), «Ролл Армянский» (404 ₽).\nВсё тут: https://курлайк.рф', 'random_id': 0})
        elif 'пицц' in msg:
            vk_session.method('messages.send', {'user_id': user_id, 'message': 'Пицца — это святое! 🍕\n«Пицца Танос» (1981 ₽) или «Цезарь Power» (549 ₽).', 'random_id': 0})
        elif 'сыр' in msg or 'мак' in msg:
            vk_session.method('messages.send', {'user_id': user_id, 'message': 'Сырная тема! 🧀\n«Mac & Cheese Фрайс» (419 ₽) или «Мак &Чизос» (419 ₽).', 'random_id': 0})
        elif 'крыл' in msg:
            vk_session.method('messages.send', {'user_id': user_id, 'message': 'Крылышки — гордость! 🍗\n5 шт — 465 ₽, 10 шт — 899 ₽, 15 шт — 1302 ₽.\nЕсть острые, BBQ и Ну мед!', 'random_id': 0})

        # 11. Не понял
        else:
            bonus = random.choice(JOKES) if random.choice([True, False]) else random.choice(COMPLIMENTS)
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': f'{bonus}\n\n{random.choice(UNKNOWN_PHRASES)}',
                'keyboard': get_main_keyboard(),
                'random_id': 0
            })
