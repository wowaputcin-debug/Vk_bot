import os
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
    # Создаем клавиатуру (one_time=False, значит она не исчезнет после нажатия)
    keyboard = VkKeyboard(one_time=False)
    
    # Первый ряд кнопок
    keyboard.add_button('🛒 Где заказать', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('😋 Что вкуснее?', color=VkKeyboardColor.POSITIVE)
    
    # Второй ряд
    keyboard.add_line() # Переход на новую строку
    keyboard.add_button('🔥 Что чаще берут?', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('🌐 Наш сайт', color=VkKeyboardColor.PRIMARY)
    
    # Третий ряд
    keyboard.add_line()
    keyboard.add_button('✍️ Оставить отзыв', color=VkKeyboardColor.NEGATIVE)
    
    return keyboard.get_keyboard()

# --- ОСНОВНАЯ ЛОГИКА ---
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        # Получаем текст сообщения от пользователя и приводим к нижнему регистру
        msg = event.text.lower()
        user_id = event.user_id

        # --- ОБРАБОТКА КОМАНД ---
        
        # 1. Команда "начать" или "привет"
        if msg in ['начать', 'привет', 'start', 'меню', 'помощь']:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'Привет! 👋 Я бот-помощник. Чем могу помочь? Выбери кнопку ниже 👇',
                'keyboard': get_main_keyboard(),
                'random_id': 0 # Нужен, чтобы сообщение не дублировалось
            })
        
        # 2. Ответ на кнопку "Где заказать"
        elif msg == '🛒 где заказать':
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'Заказать наши вкусняшки можно тут:\n👉 [ссылка на сайт или приложение]',
                'random_id': 0
            })
            
        # 3. Ответ на кнопку "Что вкуснее?"
        elif msg == '😋 что вкуснее?':
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'Если хочешь попробовать что-то новое, рекомендую:\n1. [Название блюда 1]\n2. [Название блюда 2]\nОни просто огонь! 🔥',
                'random_id': 0
            })

        # 4. Ответ на кнопку "Что чаще берут?"
        elif msg == '🔥 что чаще берут?':
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'Наши бестселлеры:\n🥇 [Популярное блюдо 1] — заказывают чаще всего!\n🥈 [Популярное блюдо 2] — тоже очень любят.\nПопробуй, не пожалеешь! 😉',
                'random_id': 0
            })
            
        # 5. Ответ на кнопку "Наш сайт"
        elif msg == '🌐 наш сайт':
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'Вот ссылка на наш сайт, там есть всё меню и акции:\n👉 [ССЫЛКА НА САЙТ]',
                'random_id': 0
            })

        # 6. Ответ на кнопку "Оставить отзыв"
        elif msg == '✍️ оставить отзыв':
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'Мы будем очень рады твоему отзыву! Напиши его тут: [ссылка на страницу отзывов]',
                'random_id': 0
            })
        
        # 7. Если бот не знает команду
        else:
            vk_session.method('messages.send', {
                'user_id': user_id,
                'message': 'Я тебя не совсем понял. 😔 Пожалуйста, воспользуйся кнопками меню или напиши "Привет".',
                'keyboard': get_main_keyboard(),
                'random_id': 0
            })
