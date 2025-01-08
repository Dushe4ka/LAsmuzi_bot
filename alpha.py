import telebot
from telebot import types
import json
import sqlite3
from database_2 import init_db, get_random_recipe, get_all_recipes_by_category, format_recipe, load_recipes_from_json, fetch_recipes, delete_recipe_by_id, get_all_categories



# Инициализация бота с вашим токеном
bot = telebot.TeleBot('7691968898:AAF3hAmA_6nwBRr3DP-8Mt8HUMEmj0kjQPc')

# Список ID администраторов
ADMIN_IDS = [1395854084, 815125048]  # Добавьте сюда все ID администраторов

# Инициализация базы данных
init_db()  # Вызовите один раз для инициализации базы данных
load_recipes_from_json('recipes.json')


@bot.message_handler(commands=['start'])
def send_welcome(message):
    log_user_message(message)  # Логируем сообщение пользователя
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('🥤 Рецепты')
    btn3 = types.KeyboardButton('👨‍💻 Поддержка')

    # Проверяем, является ли пользователь администратором
    if message.from_user.id in ADMIN_IDS:
        btn4 = types.KeyboardButton('👨‍⚖️ Админ панель')
        markup.add(btn1, btn3, btn4)
    else:
        markup.add(btn1, btn3)

    bot.send_message(message.chat.id,
                     "Добро пожаловать в LAsmuzi! 🌟\n\n\n"
                     "Уважаемый клиент!\n\n"
                     "Благодарим вас за покупку нашего мини блендера для смузи! Мы рады, что именно наш продукт стал вашим помощником в создании вкусных и полезных напитков. И мы ценим ваше доверие к нам!\n\n"
                     "Ваше мнение очень важно для нас, поэтому мы будем признательны, если вы сможете поделиться своим отзывом о нашем блендере. Это поможет нам улучшать нашу продукцию и заботиться о ваших потребностях.\n\n"
                     "В качестве небольшого бонуса мы рады предложить вам подборку лучших рецептов для смузи, которые помогут зарядить вас энергией на весь день. \n\n"
                     "Если у вас возникнут вопросы или понадобится помощь, не стесняйтесь обращаться к нам!\n\n"
                     "С уважением, LAsmuzi",
                     reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == '🥤 Рецепты')
def show_recipes_menu(message):
    log_user_message(message)  # Логируем сообщение пользователя
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Смузи', callback_data='smoothies')
    btn2 = types.InlineKeyboardButton('Получить случайный рецепт', callback_data='random_recipe')
    markup.add(btn1, btn2)

    bot.send_message(message.chat.id, "Выберите категорию рецептов:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ['smoothies', 'random_recipe'])
def callback_handler(call):
    log_user_message(call.message)  # Логируем сообщение пользователя
    if call.data == 'smoothies':
        recipes = get_all_recipes_by_category('smoothies')  # Получаем все рецепты из категории "smoothies"
        if recipes:
            message_text = format_recipes_list(recipes)  # Форматируем список рецептов
            markup = create_recipe_buttons(recipes)  # Создаем кнопки для выбора рецептов
            bot.edit_message_text(chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  text=message_text,
                                  reply_markup=markup)
        else:
            bot.edit_message_text(chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  text="Извините, не удалось найти рецепты в этой категории. Пожалуйста, попробуйте снова позже.")
    elif call.data == 'random_recipe':
        random_recipe = get_random_recipe('smoothies')  # Получаем случайный рецепт из категории "smoothies"
        if random_recipe:
            formatted_recipe = format_recipe(random_recipe)
            bot.send_message(call.message.chat.id, formatted_recipe)
        else:
            bot.edit_message_text(chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  text="Извините, не удалось найти случайный рецепт. Попробуйте снова позже.")

@bot.callback_query_handler(func=lambda call: call.data.isdigit())
def handle_recipe_selection(call):
    try:
        recipe_id = int(call.data)  # Получаем ID рецепта из callback_data
        recipe = get_recipe_by_id(recipe_id)
        if recipe:
            bot.send_message(call.message.chat.id, format_recipe(recipe))
        else:
            bot.edit_message_text(chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  text="Рецепт не найден.")
    except ValueError:
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text="Неверный формат данных.")

def get_recipe_by_id(recipe_id):
    # Получаем рецепт по ID
    recipe = fetch_recipes("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
    return recipe[0] if recipe else None

def log_user_message(message):
    """Логируем сообщения пользователей в консоль."""
    user_id = message.from_user.id
    username = message.from_user.username or "Не указано"
    user_message = message.text
    print(f"ID: {user_id}, Имя пользователя: {username}, Сообщение: {user_message}")

def format_recipes_list(recipes):
    result = "📋 Вот список рецептов:\n\n"
    for recipe in recipes:
        result += f"🥤 {recipe[1]}\n"  # recipe[1] - название рецепта
    result += "\nНажмите на название рецепта, чтобы узнать подробности."
    return result

def create_recipe_buttons(recipes):
    markup = types.InlineKeyboardMarkup()
    for recipe in recipes:
        btn = types.InlineKeyboardButton(recipe[1], callback_data=str(recipe[0]))  # recipe[1] - название, recipe[0] - ID
        markup.add(btn)
    return markup

def format_recipe(recipe):
    result = f"🥤 {recipe[1]}\n\n"  # recipe[1] - название рецепта
    ingredients = json.loads(recipe[3])  # recipe[3] - ингредиенты в формате JSON
    result += "Ингредиенты:\n"
    for ing in ingredients:
        result += f"• {ing['item']}: {ing['amount']}\n"

    nutrition = json.loads(recipe[4])  # recipe[4] - макроэлементы в формате JSON
    result += f"\nПищевая ценность:\n"
    result += f"Белки: {nutrition['protein']}\n"
    result += f"Жиры: {nutrition['fats']}\n"
    result += f"Углеводы: {nutrition['carbs']}\n"
    result += f"Калории: {recipe[5]} ккал"
    return result

@bot.message_handler(func=lambda message: message.text == '👨‍💻 Поддержка')
def support(message):
    log_user_message(message)  # Логируем сообщение пользователя
    bot.send_message(message.chat.id,
                     "По всем вопросам обращайтесь к @Assalout72")

@bot.message_handler(func=lambda message: message.text == '👨‍⚖️ Админ панель')
def admin_panel(message):
    log_user_message(message)  # Логируем сообщение пользователя
    if message.from_user.id in ADMIN_IDS:  # Проверка на список ID администраторов
        admin_text = """
Добро пожаловать в админ панель! 🌟

Вот доступные команды:
1. /add_recipe - Добавить новый рецепт
2. /view_recipes - Просмотреть все рецепты
3. /delete_recipe - Удалить рецепт по ID

Выберите команду, чтобы продолжить.
        """
        bot.send_message(message.chat.id, admin_text)
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к этой функции.")

# Пример команд для админ панели

@bot.message_handler(commands=['view_recipes'])
def view_recipes(message):
    if message.from_user.id in ADMIN_IDS:
        recipes = fetch_recipes("SELECT * FROM recipes")
        if recipes:
            recipe_list = "📋 Все рецепты:\n\n"
            for recipe in recipes:
                recipe_list += f"ID: {recipe[0]}, Название: {recipe[1]}\n"
            bot.send_message(message.chat.id, recipe_list)
        else:
            bot.send_message(message.chat.id, "Нет доступных рецептов.")
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к этой функции.")

@bot.message_handler(commands=['delete_recipe'])
def delete_recipe(message):
    if message.from_user.id in ADMIN_IDS:
        bot.send_message(message.chat.id, "Введите ID рецепта для удаления.")
        bot.register_next_step_handler(message, process_delete_recipe)
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к этой функции.")

def process_delete_recipe(message):
    try:
        recipe_id = int(message.text)  # Получаем ID рецепта
        if delete_recipe_by_id(recipe_id):  # Удаляем рецепт по ID
            bot.send_message(message.chat.id, f"Рецепт с ID {recipe_id} успешно удален.")
        else:
            bot.send_message(message.chat.id, f"Рецепт с ID {recipe_id} не найден.")
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат ID. Пожалуйста, введите правильное число.")

# Функция для удаления рецепта по ID из базы данных
def delete_recipe_by_id(recipe_id):
    try:
        conn = sqlite3.connect('recipes.db')
        cursor = conn.cursor()

        # Выполняем запрос на удаление рецепта по ID
        cursor.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
        conn.commit()

        # Проверка, был ли удален рецепт
        if cursor.rowcount > 0:
            conn.close()
            return True
        else:
            conn.close()
            return False
    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {e}")
        return False


@bot.message_handler(commands=['add_recipe'])
def add_recipe(message):
    if message.from_user.id in ADMIN_IDS:
        bot.send_message(message.chat.id, "Введите название рецепта.")
        bot.register_next_step_handler(message, get_recipe_name)
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к этой функции.")

def get_recipe_name(message):
    recipe_name = message.text
    show_category_selection(message)  # Показываем кнопки для выбора категории
    bot.register_next_step_handler(message, get_recipe_category, recipe_name)

def get_recipe_category(message, recipe_name):
    category = message.text.lower()  # Считываем категорию, выбранную пользователем
    if category in [cat.lower() for cat in get_all_categories()]:  # Проверяем, что категория существует
        bot.send_message(message.chat.id, "Введите ингредиенты (через запятую).")
        bot.register_next_step_handler(message, get_recipe_ingredients, recipe_name, category)
    else:
        bot.send_message(message.chat.id, "Неизвестная категория. Пожалуйста, выберите одну из предложенных.")
        show_category_selection(message)  # Если категория не найдена, снова показываем выбор

def show_category_selection(message):
    categories = get_all_categories()  # Получаем все категории из базы данных
    if categories:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for category in categories:
            btn = types.KeyboardButton(category.capitalize())
            markup.add(btn)
        bot.send_message(message.chat.id, "Выберите категорию для рецепта:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Извините, категории рецептов не найдены. Попробуйте позже.")

def get_recipe_category(message, recipe_name):
    category = message.text.lower()  # Считываем категорию, выбранную пользователем
    if category in [cat.lower() for cat in get_all_categories()]:  # Проверяем, что категория существует
        bot.send_message(message.chat.id, "Введите ингредиенты (через запятую).")
        bot.register_next_step_handler(message, get_recipe_ingredients, recipe_name, category)
    else:
        bot.send_message(message.chat.id, "Неизвестная категория. Пожалуйста, выберите одну из предложенных.")
        show_category_selection(message)  # Если категория не найдена, снова показываем выбор

def get_recipe_ingredients(message, recipe_name, category):
    ingredients_text = message.text
    ingredients_list = ingredients_text.split(",")  # Разделяем ингредиенты по запятой
    ingredients = [{"item": ing.strip(), "amount": "Не указано"} for ing in ingredients_list]  # Примерное хранение ингредиентов

    bot.send_message(message.chat.id, "Введите пищевую ценность (белки, жиры, углеводы, калории).")
    bot.register_next_step_handler(message, get_nutrition, recipe_name, category, ingredients)

def get_nutrition(message, recipe_name, category, ingredients):
    nutrition_text = message.text
    try:
        protein, fats, carbs, calories = map(int, nutrition_text.split())  # Преобразуем данные в числа
        nutrition = {
            "protein": protein,
            "fats": fats,
            "carbs": carbs,
            "calories": calories
        }

        bot.send_message(message.chat.id, "Введите описание рецепта.")
        bot.register_next_step_handler(message, save_recipe, recipe_name, category, ingredients, nutrition)

    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите значения корректно (например, 10 5 20 150). Попробуйте снова.")
        bot.register_next_step_handler(message, get_nutrition, recipe_name, category, ingredients)

def save_recipe(message, recipe_name, category, ingredients, nutrition):
    description = message.text

    # Добавляем рецепт в базу данных
    conn = sqlite3.connect('recipes.db')
    cursor = conn.cursor()

    ingredients_json = json.dumps(ingredients)
    nutrition_json = json.dumps(nutrition)

    cursor.execute("""
    INSERT INTO recipes (name, category, ingredients, nutrition, description)
    VALUES (?, ?, ?, ?, ?)
    """, (recipe_name, category, ingredients_json, nutrition_json, description))

    conn.commit()
    conn.close()

    bot.send_message(message.chat.id, f"Рецепт '{recipe_name}' успешно добавлен!")

@bot.message_handler(func=lambda message: message.text == '👨‍💻 Поддержка')
def support(message):
    log_user_message(message)  # Логируем сообщение пользователя
    bot.send_message(message.chat.id,
                     "По всем вопросам обращайтесь к @Assalout72")

@bot.message_handler(func=lambda message: message.text == '👨‍⚖️ Админ панель')
def admin_panel(message):
    log_user_message(message)  # Логируем сообщение пользователя
    if message.from_user.id in ADMIN_IDS:  # Проверка на список ID администраторов
        admin_text = """
Добро пожаловать в админ панель! 🌟

Вот доступные команды:
1. /add_recipe - Добавить новый рецепт
2. /view_recipes - Просмотреть все рецепты
3. /delete_recipe - Удалить рецепт по ID
4. /help - Показать это сообщение

Выберите команду, чтобы продолжить.
        """
        bot.send_message(message.chat.id, admin_text)
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к этой функции.")

# Пример команд для админ панели

@bot.message_handler(commands=['view_recipes'])
def view_recipes(message):
    if message.from_user.id in ADMIN_IDS:
        recipes = fetch_recipes("SELECT * FROM recipes")
        if recipes:
            recipe_list = "📋 Все рецепты:\n\n"
            for recipe in recipes:
                recipe_list += f"ID: {recipe[0]}, Название: {recipe[1]}\n"
            bot.send_message(message.chat.id, recipe_list)
        else:
            bot.send_message(message.chat.id, "Нет доступных рецептов.")
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к этой функции.")

@bot.message_handler(commands=['delete_recipe'])
def delete_recipe(message):
    if message.from_user.id in ADMIN_IDS:
        bot.send_message(message.chat.id, "Введите ID рецепта для удаления.")
        bot.register_next_step_handler(message, process_delete_recipe)
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к этой функции.")

def process_delete_recipe(message):
    try:
        recipe_id = int(message.text)  # Получаем ID рецепта
        if delete_recipe_by_id(recipe_id):  # Удаляем рецепт по ID
            bot.send_message(message.chat.id, f"Рецепт с ID {recipe_id} успешно удален.")
        else:
            bot.send_message(message.chat.id, f"Рецепт с ID {recipe_id} не найден.")
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат ID. Пожалуйста, введите правильное число.")

# Функция для удаления рецепта по ID из базы данных
def delete_recipe_by_id(recipe_id):
    try:
        conn = sqlite3.connect('recipes.db')
        cursor = conn.cursor()

        # Выполняем запрос на удаление рецепта по ID
        cursor.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
        conn.commit()

        # Проверка, был ли удален рецепт
        if cursor.rowcount > 0:
            conn.close()
            return True
        else:
            conn.close()
            return False
    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {e}")
        return False


@bot.message_handler(commands=['add_recipe'])
def add_recipe(message):
    if message.from_user.id in ADMIN_IDS:
        bot.send_message(message.chat.id, "Введите название рецепта.")
        bot.register_next_step_handler(message, get_recipe_name)
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к этой функции.")

def get_recipe_name(message):
    recipe_name = message.text
    show_category_selection(message)  # Показываем кнопки для выбора категории
    bot.register_next_step_handler(message, get_recipe_category, recipe_name)

# Остальные функции для работы с рецептурами и их добавлением, форматированием и отображением...

bot.polling(none_stop=True)

