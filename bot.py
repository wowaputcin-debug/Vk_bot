import os
import json
import time
import random
import vk_api
from datetime import datetime
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

# ==============================
# НАСТРОЙКИ
# ==============================
TOKEN = os.getenv('VK_TOKEN')
ADMIN_ID = 58971558
MAX_ATTEMPTS = 3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, 'fortunes.json')
CODES_FILE = os.path.join(BASE_DIR, 'promo_codes.txt')
USED_FILE = os.path.join(BASE_DIR, 'used_codes.json')
SUBSCRIBERS_FILE = os.path.join(BASE_DIR, 'subscribers.txt')
UNSUB_FILE = os.path.join(BASE_DIR, 'unsubscribed.txt')

# ==============================
# ПОДКЛЮЧЕНИЕ
# ==============================
print("Бот запускается...")
vk_session = vk_api.VkApi(token=TOKEN)
longpoll = VkLongPoll(vk_session)
print("Бот готов и ждет сообщений!")

# ==============================
# РАБОТА С ФАЙЛАМИ
# ==============================
def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_json(path, data):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка сохранения {path}: {e}")

# ==============================
# ПРОМОКОДЫ
# ==============================
def load_promo_codes():
    pools = {}
    if not os.path.exists(CODES_FILE):
        print("Файл promo_codes.txt не найден!")
        return pools
    with open(CODES_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '|' not in line:
                continue
            code, key = line.split('|', 1)
            code, key = code.strip(), key.strip()
            pools.setdefault(key, []).append(code)
    return pools

def get_next_code(pools, used_codes, key):
    for code in pools.get(key, []):
        if code not in used_codes:
            return code
    return None

# ==============================
# ПОДПИСЧИКИ
# ==============================
def add_subscriber(user_id):
    """Добавляет user_id в файл подписчиков. Отписавшиеся не добавляются."""
    user_id = str(user_id)

    # Проверяем, есть ли он в списке отписавшихся
    if os.path.exists(UNSUB_FILE):
        with open(UNSUB_FILE, 'r', encoding='utf-8') as f:
            if user_id in [line.strip() for line in f if line.strip()]:
                return

    existing = set()
    if os.path.exists(SUBSCRIBERS_FILE):
        with open(SUBSCRIBERS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                existing.add(line.strip())
    if user_id not in existing:
        with open(SUBSCRIBERS_FILE, 'a', encoding='utf-8') as f:
            f.write(user_id + '\n')
        print(f"Новый подписчик: {user_id}")

def remove_subscriber(user_id):
    """Удаляет user_id из файла подписчиков."""
    user_id = str(user_id)
    if not os.path.exists(SUBSCRIBERS_FILE):
        return False
    with open(SUBSCRIBERS_FILE, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    if user_id not in lines:
        return False
    lines = [uid for uid in lines if uid != user_id]
    with open(SUBSCRIBERS_FILE, 'w', encoding='utf-8') as f:
        for uid in lines:
            f.write(uid + '\n')
    print(f"Отписался: {user_id}")
    return True

def is_subscribed(user_id):
    """Проверяет, есть ли user_id в базе подписчиков."""
    user_id = str(user_id)
    if not os.path.exists(SUBSCRIBERS_FILE):
        return False
    with open(SUBSCRIBERS_FILE, 'r', encoding='utf-8') as f:
        return user_id in [line.strip() for line in f if line.strip()]

def get_all_subscribers():
    if not os.path.exists(SUBSCRIBERS_FILE):
        return []
    with open(SUBSCRIBERS_FILE, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def broadcast(text):
    subs = get_all_subscribers()
    unsubscribed = set()
    if os.path.exists(UNSUB_FILE):
        with open(UNSUB_FILE, 'r', encoding='utf-8') as f:
            unsubscribed = set(line.strip() for line in f if line.strip())
    subs = [uid for uid in subs if uid not in unsubscribed]

    sent, failed = 0, 0
    for uid in subs:
        try:
            vk_session.method('messages.send', {
                'user_id': int(uid),
                'message': text,
                'random_id': 0
            })
            sent += 1
        except Exception as e:
            failed += 1
            print(f"Ошибка отправки {uid}: {e}")
        time.sleep(0.05)
    return sent, failed

def sync_subscribers_from_conversations():
    """Выгружает все диалоги сообщества и добавляет их в базу подписчиков."""
    added = 0
    skipped = 0
    offset = 0

    try:
        group_info = vk_session.method('groups.getById')
        group_id = group_info[0]['id']
    except Exception as e:
        print(f"Не удалось получить ID группы: {e}")
        return 0, 0

    existing = set()
    if os.path.exists(SUBSCRIBERS_FILE):
        with open(SUBSCRIBERS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                existing.add(line.strip())

    # Отписавшиеся — не добавляем обратно
    unsubscribed = set()
    if os.path.exists(UNSUB_FILE):
        with open(UNSUB_FILE, 'r', encoding='utf-8') as f:
            unsubscribed = set(line.strip() for line in f if line.strip())

    while True:
        try:
            conversations = vk_session.method('messages.getConversations', {
                'group_id': group_id,
                'count': 200,
                'offset': offset,
                'filter': 'all'
            })
        except Exception as e:
            print(f"Ошибка получения диалогов: {e}")
            break

        items = conversations.get('items', [])
        if not items:
            break

        for item in items:
            conv = item.get('conversation', {})
            peer = conv.get('peer', {})
            peer_id = peer.get('id')

            if not peer_id or peer_id <= 0:
                continue

            uid_str = str(peer_id)
            if uid_str in unsubscribed:
                continue
            if uid_str not in existing:
                try:
                    allowed = vk_session.method('messages.isMessagesFromGroupAllowed', {
                        'group_id': group_id,
                        'user_id': peer_id
                    })
                    if allowed.get('is_allowed'):
                        existing.add(uid_str)
                        added += 1
                    else:
                        skipped += 1
                except Exception:
                    skipped += 1
                time.sleep(0.05)

        offset += 200
        if offset >= conversations.get('count', 0):
            break
        time.sleep(0.3)

    with open(SUBSCRIBERS_FILE, 'w', encoding='utf-8') as f:
        for uid in sorted(existing, key=lambda x: int(x) if x.isdigit() else 0):
            f.write(uid + '\n')

    return added, skipped

# ==============================
# СОСТОЯНИЕ ПОЛЬЗОВАТЕЛЯ (колесо фортуны)
# ==============================
def get_user_state(user_id):
    today = datetime.now().strftime('%Y-%m-%d')
    state = load_json(STATE_FILE)
    user = state.get(str(user_id), {})
    if user.get('date') != today:
        user = {'date': today, 'attempts': MAX_ATTEMPTS, 'last_msg_id': None}
    return state, user

def save_user_state(state, user_id, user):
    state[str(user_id)] = user
    save_json(STATE_FILE, state)

# ==============================
# ПРИЗЫ
# ==============================
FORTUNE_REWARDS = [
    {"text": "🎁 Соус в подарок к любому заказу!", "weight": 25, "tier": "common", "code_key": "sous"},
    {"text": "😎 Комплимент от шефа: ты выглядишь на миллион! Но увы, без скидки 😅", "weight": 15, "tier": "common", "code_key": None},
    {"text": "🍟 Картофель фри в подарок при заказе от 500 ₽!", "weight": 15, "tier": "common", "code_key": "fries"},
    {"text": "💸 Скидка 5% на весь заказ!", "weight": 12, "tier": "uncommon", "code_key": "discount5"},
    {"text": "🌯 Ролл Цыпа в подарок при заказе от 1000 ₽!", "weight": 6, "tier": "rare", "code_key": "roll"},
    {"text": "💸 Скидка 10% на весь заказ!", "weight": 5, "tier": "rare", "code_key": "discount10"},
    {"text": "🧀 Mac & Cheese Фрайс в подарок при заказе от 800 ₽!", "weight": 2.5, "tier": "epic", "code_key": "mac"},
    {"text": "🍕 Пицца 25 см в подарок при заказе от 1500 ₽!", "weight": 1.3, "tier": "epic", "code_key": "pizza"},
    {"text": "🔥 ДЖЕКПОТ! Скидка 25% на весь заказ!", "weight": 0.2, "tier": "legendary", "code_key": "jackpot"},
]

TIER_EMOJI = {
    'common': '🎈',
    'uncommon': '🎁',
    'rare': '💎',
    'epic': '👑',
    'legendary': '🔥'
}

def spin_wheel():
    total = sum(r['weight'] for r in FORTUNE_REWARDS)
    r = random.uniform(0, total)
    upto = 0
    for reward in FORTUNE_REWARDS:
        upto += reward['weight']
        if r <= upto:
            return reward
    return FORTUNE_REWARDS[0]

# ==============================
# ШУТКИ И КОМПЛИМЕНТЫ
# ==============================
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
    "Спасибо, что ты есть! Без тебя наша кухня была бы скучной. 🍳❤️",
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
    'Ого, ты меня озадачил! 🤯 Но я всё равно знаю, что тебе нужно — вкусная еда!',
]

MOOD_PHRASES = [
    "Держи позитив! 😄",
    "Лови заряд настроения! ⚡",
    "Специально для тебя: 🎁",
]

# ==============================
# НЕЦЕЛЕВЫЕ ОТВЕТЫ
# ==============================
WORK_RESPONSE = 'Ого, ты хочешь к нам в команду? 🔥\n\nПо вопросам работы пиши сюда:\n👉 https://vk.com/write58971558'
PARTNERSHIP_RESPONSE = 'Спасибо за предложение! 🤝\n\nПо вопросам сотрудничества и рекламы:\n👉 https://vk.com/write58971558'
SPAM_RESPONSE = 'Ой, я бот и не разбираюсь в таких вопросах. 😅\n\nРеальные предложения — сюда:\n👉 https://vk.com/write58971558'

WORK_KEYWORDS = ['работ', 'вакан', 'устро', 'резюме', 'трудоустро', 'зарплат', 'подработ', 'повар', 'курьер']
PARTNERSHIP_KEYWORDS = ['сотруднич', 'партнер', 'партнёр', 'реклам', 'предложени', 'бартер', 'инвестиц', 'коллаб', 'продвижени', 'пиар']
SPAM_KEYWORDS = ['крипт', 'биткоин', 'заработок', 'пассивный доход', 'трейдинг', 'казино', 'ставк', 'форекс', 'накрутк']

# ==============================
# КЛАВИАТУРЫ
# ==============================
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
    kb.add_button('💔 Отписаться', color=VkKeyboardColor.SECONDARY)
    return kb.get_keyboard()

def get_fortune_inline_keyboard(attempts_left):
    kb = VkKeyboard(inline=True)
    kb.add_openlink_button(label='📱 Скачать приложение', link='https://xn--80asbcc3au.xn--p1ai/qr-mobile')
    kb.add_line()
    kb.add_openlink_button(label='🌐 Заказать на сайте', link='https://курлайк.рф')
    if attempts_left > 0:
        kb.add_line()
        kb.add_button('🎲 Ещё раз', color=VkKeyboardColor.POSITIVE)
    return kb.get_keyboard()

def get_inline_keyboard():
    kb = VkKeyboard(inline=True)
    kb.add_openlink_button(label='📱 Скачать приложение', link='https://xn--80asbcc3au.xn--p1ai/qr-mobile')
    kb.add_line()
    kb.add_openlink_button(label='🌐 Заказать на сайте', link='https://курлайк.рф')
    return kb.get_keyboard()

# ==============================
# КОЛЕСО ФОРТУНЫ
# ==============================
def handle_fortune(user_id):
    state, user = get_user_state(user_id)

    if user.get('last_msg_id'):
        try:
            vk_session.method('messages.delete', {
                'message_ids': user['last_msg_id'],
                'delete_for_all': 1
            })
        except Exception as e:
            print(f"Не удалось удалить сообщение: {e}")
        user['last_msg_id'] = None

    if user['attempts'] <= 0:
        response = vk_session.method('messages.send', {
            'user_id': user_id,
            'message': '😢 Ты уже использовал все 3 попытки на сегодня!\n\nВозвращайся завтра за новой порцией удачи. А пока — закажи что-нибудь вкусное в приложении 🍗',
            'keyboard': get_inline_keyboard(),
            'random_id': 0
        })
        user['last_msg_id'] = response
        save_user_state(state, user_id, user)
        return

    user['attempts'] -= 1
    reward = spin_wheel()
    attempts_left = user['attempts']
    emoji = TIER_EMOJI[reward['tier']]

    message = f"🎰 Крутим барабан...\n⏳ Три... Два... Один...\n\n{emoji} {reward['text']}\n\n"
    code_given = None

    if reward['code_key']:
        pools = load_promo_codes()
        used = load_json(USED_FILE)
        code = get_next_code(pools, used, reward['code_key'])
        if code:
            used[code] = {
                'user_id': user_id,
                'date': user['date'],
                'reward': reward['code_key'],
                'text': reward['text']
            }
            save_json(USED_FILE, used)
            code_given = code
            message += (
                f"🎟 Твой промокод: {code}\n\n"
                f"📲 Введи его в приложении или на сайте при оформлении заказа — скидка применится автоматически!\n\n"
            )
        else:
            message = (
                f"🎰 Крутим барабан...\n\n"
                f"😎 Ой, а призы на сегодня закончились! Но ты всё равно классный: "
                f"{random.choice(COMPLIMENTS)}\n\n"
            )

    if code_given:
        message += "👇 Заказывай прямо тут:"
        keyboard = get_fortune_inline_keyboard(attempts_left)
    else:
        if attempts_left > 0:
            keyboard = get_fortune_inline_keyboard(attempts_left)
        else:
            keyboard = get_inline_keyboard()

    response = vk_session.method('messages.send', {
        'user_id': user_id,
        'message': message,
        'keyboard': keyboard,
        'random_id': 0
    })
    user['last_msg_id'] = response
    save_user_state(state, user_id, user)

# ==============================
# АДМИН-СТАТИСТИКА
# ==============================
def send_admin_stats(user_id):
    pools = load_promo_codes()
    used = load_json(USED_FILE)
    lines = ["📊 Статистика промокодов:\n"]
    for key, codes in pools.items():
        free = sum(1 for c in codes if c not in used)
        lines.append(f"• {key}: свободно {free} из {len(codes)}")
    lines.append(f"\nВсего использовано: {len(used)}")
    lines.append(f"👥 Подписчиков: {len(get_all_subscribers())}")
    vk_session.method('messages.send', {
        'user_id': user_id,
        'message': '\n'.join(lines),
        'random_id': 0
    })

# ==============================
# ОСНОВНАЯ ЛОГИКА
# ==============================
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        msg = event.text.lower()
        user_id = event.user_id

        # Сохраняем подписчика (если ещё не отписался)
        add_subscriber(user_id)

        # ==============================
        # АДМИН-КОМАНДЫ
        # ==============================
        if user_id == ADMIN_ID:
            if msg.strip() in ['стата', 'статистика', 'stats']:
                send_admin_stats(user_id)
                continue

            if msg.strip() in ['подписчики', 'база', 'subs']:
                subs = get_all_subscribers()
                vk_session.method('messages.send', {
                    'user_id': user_id,
                    'message': f'📊 В базе {len(subs)} подписчиков.',
                    'random_id': 0
                })
                continue

            if msg.strip() in ['/sync', 'синхронизация', 'выгрузить']:
                vk_session.method('messages.send', {
                    'user_id': user_id,
                    'message': '⏳ Собираю диалоги из сообщества...\nЭто может занять пару минут. Подожди.',
                    'random_id': 0
                })
                added, skipped = sync_subscribers_from_conversations()
                total = len(get_all_subscribers())
                vk_session.method('messages.send', {
                    'user_id': user_id,
                    'message': f'✅ Синхронизация готова!\n\n➕ Добавлено новых: {added}\n🚫 Пропущено: {skipped}\n👥 Всего в базе: {total}',
                    'random_id': 0
                })
                continue

            if msg.startswith('/broadcast '):
                broadcast_text = event.text[len('/broadcast '):].strip()
                if not broadcast_text:
                    vk_session.method('messages.send', {
                        'user_id': user_id,
                        'message': '❌ Текст пустой. Формат: /broadcast Привет, друзья!',
                        'random_id': 0
                    })
                    continue
                vk_session.method('messages.send', {
                    'user_id': user_id,
                    'message': f'🚀 Начинаю рассылку {len(get_all_subscribers())} подписчикам...',
                    'random_id': 0
                })
                sent, failed = broadcast(broadcast_text)
                vk_session.method('messages.send', {
                    'user_id': user_id,
                    'message': f'✅ Рассылка завершена!\n📨 Отправлено: {sent}\n❌ Ошибок: {failed}',
                    'random_id': 0
                })
                continue

        # ==============================
        # ОТПИСКА
        # ==============================
        if msg == '💔 отписаться' or 'отписаться' in msg or 'отписка' in msg:
            was_subscribed = is_subscribed(user_id)
            if was_subscribed:
                remove_subscriber(user_id)
                # Записываем в файл отписавшихся, чтобы не добавлять снова
                with open(UNSUB_FILE, 'a', encoding='utf-8') as f:
                    f.write(str(user_id) + '\n')

                vk_session.method('messages.send', {
                    'user_id': user_id,
                    'message': (
                        '💔 Извини, что мы больше не сможем тебе писать...\n\n'
                        'Ты был лучшим подписчиком! 🥺\n\n'
                        'Если вдруг захочешь вернуться — просто напиши нам «Привет».\n'
                        'Мы будем ждать. 🐔❤️\n\n'
                        'А если захочешь поесть — кнопки ниже всегда для тебя 👇'
                    ),
                    'keyboard': get_main_keyboard(),
                    'random_id': 0
                })
            else:
                vk_session.method('messages.send', {
                    'user_id': user_id,
                    'message': (
                        'Хм, а ты и так не подписан на рассылку 🤔\n'
                        'Но раз уж написал — держи кнопки! 👇'
                    ),
                    'keyboard': get_main_keyboard(),
                    'random_id': 0
                })

        # ==============================
        # НЕЦЕЛЕВЫЕ ТЕМЫ
        # ==============================
        elif any(w in msg for w in WORK_KEYWORDS):
            vk_session.method('messages.send', {'user_id': user_id, 'message': WORK_RESPONSE, 'random_id': 0})
        elif any(w in msg for w in PARTNERSHIP_KEYWORDS):
            vk_session.method('messages.send', {'user_id': user_id, 'message': PARTNERSHIP_RESPONSE, 'random_id': 0})
        elif any(w in msg for w in SPAM_KEYWORDS):
            vk_session.method('messages.send', {'user_id': user_id, 'message': SPAM_RESPONSE, 'keyboard': get_main_keyboard(), 'random_id': 0})

        # ==============================
        # ОСНОВНЫЕ КОМАНДЫ
        # ==============================
        elif msg in ['начать', 'привет', 'start', 'меню', 'помощь', 'здарова', 'хай']:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': f'{random.choice(HELLO_PHRASES)}\n\nКстати, {random.choice(COMPLIMENTS)}',
                'keyboard': get_main_keyboard(),
                'random_id': 0
            })

        elif 'колесо' in msg or msg == '🎲 ещё раз' or 'фортуны' in msg or 'рандом' in msg or 'не знаю' in msg:
            handle_fortune(user_id)

        elif msg == '🛒 где заказать' or 'заказ' in msg:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'Заказать наши вкусняшки можно так:\n👇 Выбирай удобный способ!',
                'keyboard': get_inline_keyboard(),
                'random_id': 0
            })

        elif msg == '😋 что вкуснее?' or 'вкусн' in msg or 'посовет' in msg:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'Если хочешь новое:\n1. Комбо курочка+подружка (1263 ₽) — взрыв курицы! 🍗\n2. Mac & Cheese Фрайс (419 ₽) — сыр, рожки и фри! 🧀\n3. Баскет Пэли мэни пакьяо (631 ₽)! 🥟\nОгонь! 🔥',
                'random_id': 0
            })

        elif msg == '🔥 что чаще берут?' or 'хит' in msg or 'популярн' in msg or 'берут' in msg:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'Бестселлеры:\n🥇 Цыпа (378 ₽)\n🥈 Курочка+друг (1263 ₽)\n🥉 Пицца «ТАНОС» (1981 ₽)\nПопробуй! 😉',
                'random_id': 0
            })

        elif msg == '🌐 наш сайт' or 'сайт' in msg:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'Сайт с меню и акциями:\n👉 https://курлайк.рф',
                'random_id': 0
            })

        elif msg == '✍️ оставить отзыв' or 'отзыв' in msg:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'Нам важно твоё мнение! ❤️ Напиши отзыв:\n👉 https://vk.com/write58971558',
                'random_id': 0
            })

        elif msg == '😄 поднять настроение' or 'шутк' in msg or 'анекдот' in msg or 'комплимент' in msg or 'настроение' in msg:
            text = random.choice(JOKES) if random.choice([True, False]) else random.choice(COMPLIMENTS)
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': f'{random.choice(MOOD_PHRASES)}\n\n{text}',
                'keyboard': get_main_keyboard(),
                'random_id': 0
            })

        # ==============================
        # РЕАКЦИИ НА ПОЗИТИВ
        # ==============================
        elif any(word in msg for word in ['спасибо', 'круто', 'супер', 'вкусно', 'огонь', 'класс', 'люблю', 'обожаю', 'молодцы']):
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'Ох, спасибо! 🥰 Нам очень приятно! Огонь! 🔥',
                'random_id': 0
            })

        # ==============================
        # УМНЫЙ ПОИСК
        # ==============================
        elif 'ролл' in msg:
            vk_session.method('messages.send', {'user_id': user_id, 'message': 'Роллы! 🌯\n«Цыпа» (378 ₽), «Армянский» (404 ₽).\nВсё тут: https://курлайк.рф', 'random_id': 0})
        elif 'пицц' in msg:
            vk_session.method('messages.send', {'user_id': user_id, 'message': 'Пицца! 🍕\n«Танос» (1981 ₽) или «Цезарь Power» (549 ₽).', 'random_id': 0})
        elif 'сыр' in msg or 'мак' in msg:
            vk_session.method('messages.send', {'user_id': user_id, 'message': 'Сырная тема! 🧀\n«Mac & Cheese Фрайс» (419 ₽) или «Мак &Чизос» (419 ₽).', 'random_id': 0})
        elif 'крыл' in msg:
            vk_session.method('messages.send', {'user_id': user_id, 'message': 'Крылышки! 🍗\n5 шт — 465 ₽, 10 шт — 899 ₽, 15 шт — 1302 ₽.', 'random_id': 0})

        # ==============================
        # ЕСЛИ БОТ НЕ ПОНЯЛ
        # ==============================
        else:
            bonus = random.choice(JOKES) if random.choice([True, False]) else random.choice(COMPLIMENTS)
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': f'{bonus}\n\n{random.choice(UNKNOWN_PHRASES)}',
                'keyboard': get_main_keyboard(),
                'random_id': 0
            })
