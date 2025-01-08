import sqlite3
import json


def init_db():
    conn = sqlite3.connect('recipes.db')
    cursor = conn.cursor()

    # Удаляем таблицу, если она существует
    cursor.execute('DROP TABLE IF EXISTS recipes')

    # Создание таблицы рецептов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        ingredients TEXT NOT NULL,
        nutrition TEXT NOT NULL,
        calories INTEGER NOT NULL
    )
    ''')

    conn.commit()
    conn.close()


def fetch_recipes(query, params=()):
    """
    Универсальная функция для выполнения запросов к базе данных.
    """
    try:
        conn = sqlite3.connect('recipes.db')
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchall()
        conn.close()
        return result
    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {e}")
        return []


def get_random_recipe(category):
    if not category:
        print("Категория не указана!")
        return None
    result = fetch_recipes("SELECT * FROM recipes WHERE category = ? ORDER BY RANDOM() LIMIT 1", (category,))
    return result[0] if result else None

def get_all_categories():
    """Получение всех уникальных категорий из базы данных"""
    query = "SELECT DISTINCT category FROM recipes"
    categories = fetch_recipes(query)  # Используем fetch_recipes для выполнения запроса
    return [category[0] for category in categories]  # Возвращаем список категорий


def get_all_recipes_by_category(category):
    if not category:
        print("Категория не указана!")
        return []
    return fetch_recipes("SELECT * FROM recipes WHERE category = ?", (category,))


def get_recipes_by_ingredient(ingredient):
    """
    Получение всех рецептов, содержащих указанный ингредиент.
    """
    if not ingredient:
        print("Ингредиент не указан!")
        return []
    query = "SELECT * FROM recipes WHERE ingredients LIKE ?"
    return fetch_recipes(query, (f'%{ingredient}%',))


def format_recipe(recipe):
    """
    Преобразование рецепта в удобный словарь.
    """
    if not recipe:
        return None
    keys = ["id", "name", "category", "ingredients", "nutrition", "calories"]
    recipe_dict = dict(zip(keys, recipe))
    recipe_dict["ingredients"] = json.loads(recipe_dict["ingredients"])
    recipe_dict["nutrition"] = json.loads(recipe_dict["nutrition"])
    return recipe_dict


def load_recipes_from_json(json_file):
    try:
        # Открытие файла с рецептами
        with open(json_file, 'r', encoding='utf-8') as file:
            recipes_data = json.load(file)

        # Перебор рецептов и преобразование их в нужный формат
        recipes = []
        for recipe in recipes_data:
            # Преобразуем строку рецепта в список ингредиентов
            ingredients = recipe.get('рецепт', '').split(', ')
            ingredients_list = [{"item": ingredient.split(' ')[-1],
                                 "amount": ingredient.split(' ')[0] + ' ' + ' '.join(ingredient.split(' ')[1:])} for
                                ingredient in ingredients]

            # Преобразуем макроэлементы в формат JSON
            nutrition = {
                "protein": recipe.get('белки', 0),
                "fats": recipe.get('жиры', 0),
                "carbs": recipe.get('углеводы', 0)
            }

            # Формируем рецепт для добавления в базу данных
            recipes.append({
                "name": recipe.get('название', 'Без названия'),
                "category": "smoothies",  # Категория по умолчанию
                "ingredients": json.dumps(ingredients_list),
                "nutrition": json.dumps(nutrition),
                "calories": recipe.get('калории', 0)
            })

        # Вставка данных в базу
        conn = sqlite3.connect('recipes.db')
        cursor = conn.cursor()

        # Вставка рецептов
        cursor.executemany('''
        INSERT INTO recipes (name, category, ingredients, nutrition, calories) 
        VALUES (:name, :category, :ingredients, :nutrition, :calories)
        ''', recipes)

        conn.commit()
        conn.close()
        print(f"{len(recipes)} рецептов успешно загружены из {json_file}.")

    except Exception as e:
        print(f"Ошибка при загрузке рецептов: {e}")


def delete_recipe_by_id(recipe_id):
    """
    Удаление рецепта по ID из базы данных.
    """
    try:
        conn = sqlite3.connect('recipes.db')
        cursor = conn.cursor()

        # Выполняем запрос на удаление рецепта по ID
        cursor.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
        conn.commit()

        # Проверка, был ли удален рецепт
        if cursor.rowcount > 0:
            print(f"Рецепт с ID {recipe_id} был успешно удален.")
        else:
            print(f"Рецепт с ID {recipe_id} не найден.")

        conn.close()
        return cursor.rowcount > 0

    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {e}")
        return False


# Пример использования
if __name__ == "__main__":
    init_db()

    # Загрузка рецептов из файла recipes.json
    load_recipes_from_json('recipes.json')

    # Получение случайного рецепта
    random_recipe = get_random_recipe("smoothies")
    print("Случайный рецепт:", format_recipe(random_recipe))

    # Получение всех рецептов из категории
    all_smoothies = get_all_recipes_by_category("smoothies")
    print("Все смузи:", [format_recipe(recipe) for recipe in all_smoothies])

    # Поиск рецептов по ингредиенту
    recipes_with_banana = get_recipes_by_ingredient("банан")
    print("Рецепты с бананом:", [format_recipe(recipe) for recipe in recipes_with_banana])

    # Удаление рецепта по ID (пример)
    delete_recipe_by_id(1)  # Удалим рецепт с ID = 1
