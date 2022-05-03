from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3

settings = open('settings.txt', 'r').readline().split(',')

# Пароль администратора (используется при добавлении пользователя в админы командой /admin [пароль])
admin_password = str(settings[0])
print(admin_password)

# Создание базы данных, курсора
db = sqlite3.connect('server.db')
sql = db.cursor()

# Создание таблицы корзин пользователей
sql.execute("""CREATE TABLE IF NOT EXISTS carts (
    id INT,
    products TEXT
)""")

# Создание таблицы с товарами
sql.execute("""CREATE TABLE IF NOT EXISTS products (
    id INT,
    name TEXT,
    description TEXT,
    category TEXT,
    price TEXT,
    photo BLOB
)""")

# Создание таблицы администраторов
sql.execute("""CREATE TABLE IF NOT EXISTS admins (id TEXT, username TEXT)""")

if sql.execute(f"SELECT * FROM products WHERE id = '9999999999'").fetchone() is None:
    sql.execute("INSERT INTO products VALUES (?,?,?,?,?,?)", (9999999999, None, None, None, None, None))

# Сохранение всех изменений в БД
db.commit()

# Настройка бота
bot = Bot(token=settings[1])
dp = Dispatcher(bot)

# Первое обновление категорий товаров
sql_query = "SELECT category FROM products"
sql.execute(sql_query)
content = sql.fetchall()
categorys = []
for i in content:
    if str(i[0]) == 'None':
        continue
    category = i[0].lower()
    if not str(category) in categorys:
        categorys.append(f'{category}')


# Проверка пользователя на права администратора
def admin_check(user_id):
    sql.execute(f"SELECT id FROM admins WHERE id = '{user_id}'")
    if sql.fetchone() is None:
        return False
    else:
        return True


# Конвертация файла в байты для дальнейшей записи в БД
def convert_to_binary_data(filename):
    # Преобразование данных в двоичный формат
    with open(filename, 'rb') as file:
        blob_data = file.read()
    return blob_data


# Временная запись в файл картинки из БД по ID, для отправки пользователю
def get_image(Id):
    sql.execute(f"SELECT photo FROM products WHERE id = '{Id}'")
    content = sql.fetchone()
    if content is None:
        print(f'Нет товара с ID {Id}')
    else:
        with open('img_to_write.jpg', 'wb') as file:
            file.write(content[0])


# Получение всей инфы о товаре из БД по одному ID
def get_product(Id):
    sql.execute(f"SELECT * FROM products WHERE id = '{Id}'")
    content = sql.fetchone()
    if content is None:
        print(f'Нету такого товара ID: {Id}')
    else:
        name = content[1]
        description = content[2]
        price = content[3]
        category = content[4]
        get_image(Id)
        return [name, description, price, category]


# Обновление в БД записи товара при редактировании
def update_product(Id, info):
    sql.execute(f"SELECT * FROM products WHERE id = '{Id}'")
    content = sql.fetchone()
    if content is None:
        print(f'Нету такого товара ID: {Id}')
    else:
        new_photo = convert_to_binary_data('img_for_read.jpg')
        sql.execute(f"UPDATE products SET name = ?, description = ?, category = ?, price = ?, photo = ? WHERE id = ?",
                    (info[1], info[2], info[3].lower(), info[4], new_photo, Id))
        db.commit()


# Удаление товара из БД по ID
def delete_product(Id):
    sql.execute(f"DELETE FROM products WHERE id = '{Id}'")
    db.commit()


# Создание записи товара в БД
def insert_products(Id, name, desc, category, price, filename):
    try:
        sql_query = "SELECT * FROM products WHERE id = ?"
        arguments = (Id,)
        sql.execute(sql_query, arguments)
        if sql.fetchone() is None:
            sqlite_insert_query = "INSERT INTO products VALUES (?, ?, ?, ?, ?, ?)"
            photo = convert_to_binary_data(filename)
            data_tuple = (Id, name, desc, category, price, photo)
            sql.execute(sqlite_insert_query, data_tuple)
            db.commit()
        else:
            print('Товар с таким ID уже существует')

    except sqlite3.Error as error:
        print("Ошибка при работе с SQLite", error)


# Хэндлер, отслеживающий получение сообщения с фото (создание, редактирование товара)
@dp.message_handler(content_types=['photo'])
async def handle_docs_photo(message):
    if '/add ' in message.caption and admin_check(message.chat.id):
        user_id = message.chat.id
        args = message.caption.replace('/add ', '').split('/')
        text = 'Запрос отправлен на сервер'
        await message.answer(text)
        if admin_check(user_id) and len(args) == 4:
            await message.photo[-1].download('img_for_read.jpg')
            sql_query = "SELECT * FROM products"
            sql.execute(sql_query)
            all_id = sql.fetchall()
            last_id = all_id[-1]
            ident = str(10000000000 - int(len(all_id)) - 1)
            insert_products(ident, args[0], args[1], args[2].lower(), args[3], 'img_for_read.jpg')
            await message.answer('Товар добавлен')

    elif '/update ' in message.caption and admin_check(message.chat.id):
        user_id = message.chat.id
        args = message.caption.replace('/update ', '').split('/')
        Id = args[0]
        await message.answer('Запрос на обновление отправлен на сервер')
        if admin_check(user_id) and len(args) == 5:
            sql_query = "SELECT * FROM products WHERE id = ?"
            arguments = (Id,)
            sql.execute(sql_query, arguments)
            content = sql.fetchone()
            if content is None:
                await message.answer(f'Товара с таким ID нет в базе. ID: {Id}')
            else:
                await message.photo[-1].download('img_for_read.jpg')
                update_product(args[0], args)
                await message.answer('Товар обновлен')


# Хэндлер, отслеживающий обычные текстовые сообщения
@dp.message_handler()
async def cmd_test1(message: types.Message):
    # Делаем переменную категорий товаров глобальной, чтобы перезаписывать её в дальнейшем
    global categorys
    # print(message.text)
    # LOREMIPSUMLOREMIPSUMLOREMIPSUM

    # Если '/start' в тексте (первая команда)
    if '/start' in message.text or 'в меню' in message.text.lower() or 'в пользовательское меню' in message.text.lower():
        kb_button1 = KeyboardButton('Каталог')
        kb_button2 = KeyboardButton('Корзина')
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(kb_button1, kb_button2)
        text = 'Здравствуйте! Куда вам нужно?'
        await message.answer(text, reply_markup=kb)
    # Если '/id' в тексте (выдача инфы о товаре по ID)
    elif '/id ' in message.text:
        user_id = message.chat.id
        Id = str(message.text.replace('/id ', ''))
        info = get_product(Id)
        photo = open('img_to_write.jpg', 'rb').read()
        text = f"""{info[0]}
{info[1]}
Категория: {info[2]}
{info[3]} рублей
ID: {Id}"""
        await bot.send_photo(chat_id=user_id, photo=photo, caption=text)

    # Если '/delete' в тексте (удаление товара из БД)
    elif '/delete ' in message.text and admin_check(message.chat.id):
        user_id = message.chat.id
        Id = str(message.text.replace('/delete ', ''))
        sql.execute(f"SELECT * FROM products WHERE id = '{Id}'")
        content = sql.fetchone()
        if content is None:
            await message.answer(f'Товара с таким ID нет в базе. ID: {Id}')
        else:
            delete_product(Id)
            await message.answer(f'Товар удален из базы данных. ID: {Id}')

    # Если '/cart' в тексте (Добавление товара в корзину)
    elif '/cart ' in message.text.lower() and len(message.text.replace('/cart ', '')) == 10:
        try:
            message.text = message.text.lower()
            message.text = message.text.replace('/cart ', '')
            int('1' + message.text)
            user_id = message.chat.id
            new_product = message.text
            sql_query = "SELECT id FROM products"
            sql.execute(sql_query)
            content = sql.fetchall()
            all_ids = [i[0] for i in content]
            if int(new_product) in all_ids:
                sql_query = "SELECT products FROM carts WHERE id = ?"
                arguments = (user_id,)
                sql.execute(sql_query, arguments)
                if sql.fetchone() is None:
                    sql_query = "INSERT INTO carts VALUES(?,?)"
                    arguments = (user_id, new_product)
                    sql.execute(sql_query, arguments)
                    db.commit()
                    text = 'Товар успешно добавлен в корзину'
                    await message.answer(text)
                else:
                    sql.execute(f"SELECT products FROM carts WHERE id = '{user_id}'")
                    old_all_products = sql.fetchone()[0]
                    if str(new_product) not in str(old_all_products):
                        all_products = old_all_products + f',{new_product}'
                        sql.execute(f"UPDATE carts SET products = '{all_products}' WHERE id = '{user_id}'")
                        db.commit()
                        await message.answer('Товар успешно добавлен в корзину')
                    else:
                        await message.answer('Вы уже добавили этот товар в корзину')
            else:
                await message.answer('Такого товара не существует')
        except ValueError:
            pass
    #Если 'корзина' в тексте (по-очереди выдаёт все товары из корзины пользователя)
    elif 'корзина' in message.text.lower():
        user_id = message.chat.id
        sql_query = "SELECT products FROM carts WHERE id = ?"
        arguments = (user_id,)
        sql.execute(sql_query, arguments)
        products = sql.fetchone()
        if products is None:
            text = """Ваша корзина пуста.

Чтобы добавить товар в корзину напишите:

/cart [ID товара, который вы хотите добавить]

ID товаров можно узнать во вкладке \"Каталог\""""
            await message.answer(text)
        else:
            await message.answer('Товары в вашей корзине: ')
            products = products[0].split(',')
            total_price = 0
            for i in products:
                sql.execute(f"SELECT * FROM products WHERE id = '{i}'")
                if sql.fetchone() is None:
                    sql.execute(f"SELECT products FROM carts WHERE id = '{user_id}'")
                    products = sql.fetchone()[0]
                    product = i
                    products = products.replace(f'{product},','').replace(f',{product}','').replace(f'{product},','').replace(product, '')
                    if products == '':
                        sql.execute(f"DELETE FROM carts WHERE id = '{user_id}'")
                    sql.execute(f"UPDATE carts SET products = '{products}' WHERE id = '{user_id}'")
                    db.commit()
                    await message.answer('Один из товаров удалён из вашей корзины, т.к. его больше нет в базе данных')
                else:
                    user_id = message.chat.id
                    info = get_product(i)
                    total_price += int(info[3])
                    with open('img_to_write.jpg','rb') as photo:
                        await bot.send_photo(chat_id=user_id, photo=photo, caption=f'{info[0]}\n{info[1]}\nКатегория: {info[2]}\n{info[3]} рублей\nID: {i}')
            kb_button1 = KeyboardButton('Купить')
            kb_button3 = KeyboardButton('Удалить товар из корзины')
            kb_button4 = KeyboardButton('Очистить')
            kb_button2 = KeyboardButton('В меню')
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(kb_button1, kb_button3, kb_button4, kb_button2)
            await message.answer(f'Общая стоимость товаров в корзине: {total_price}', reply_markup=kb)
    #Если 'купить' в тексте (отправляет всем администраторам сообщение с заказом пользователя)
    elif 'купить' in message.text.lower():
        user_id = message.chat.id
        sql_query = "SELECT id FROM admins"
        sql.execute(sql_query)
        admins = sql.fetchall()
        admins = [i[0] for i in admins]
        sql_query = "SELECT products FROM carts WHERE id = ?"
        arguments = (user_id,)
        sql.execute(sql_query, arguments)
        content = sql.fetchone()[0].split(',')
        total_price = 0
        for i in content:
            user_id = message.chat.id
            info = get_product(i)
            total_price += int(info[3])
        products = str(content).replace("'",'')
        username = message.from_user.username
        msg = f"""Пользователь {user_id} (@{username}) заказал следующие товары:

{products}

На сумму {str(total_price)} рублей"""
        for i in admins:
            await bot.send_message(i, msg)
        await message.answer(f'Ваш запрос отправлен менеджеру')
    #Если '/clear_cart' в тексте (полное удаление всех товаров из корзины пользователя)
    elif '/clear_cart' in message.text.lower():
        user_id = message.chat.id
        sql_query = "DELETE FROM carts WHERE id = ?"
        arguments = (user_id,)
        sql.execute(sql_query, arguments)
        db.commit()
        await message.answer(f'Ваша корзина полностью очищена.')
    #Если '/admin' в тексте (вход в режим администратора)
    elif f'/admin {admin_password} ' in message.text:

        kb_button1 = KeyboardButton('Добавить товар')
        kb_button2 = KeyboardButton('Редактировать товар')
        kb_button3 = KeyboardButton('Удалить товар')
        kb_button4 = KeyboardButton('В пользовательское меню')
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(kb_button1, kb_button2, kb_button3, kb_button4)
        user_id = message.chat.id
        username = message.from_user.username
        sql_query = "SELECT id FROM admins WHERE id = ?"
        arguments = (user_id,)
        sql.execute(sql_query, arguments)
        if sql.fetchone() is None:
            sql_query = "INSERT INTO admins VALUES (?, ?)"
            arguments = (user_id, username)
            sql.execute(sql_query,arguments)
            db.commit()
            await message.answer('Здравствуйте! Режим администратора включен. Выберите действие:', reply_markup = kb)
        else:
            await message.answer('Здравствуйте! Режим администратора уже включен. Выберите действие:', reply_markup = kb)
    # Если 'добавить товар' в тексте (помощь при добавлении товара)
    elif 'добавить товар' in message.text.lower():
        user_id = message.chat.id
        text = """Прикрепите фото товара и напишите текст вида (без квадратных скобок):

/add [Название товара]/[Описание товара]/[Категория]/[Цена]"""
        if admin_check(user_id):
            await message.answer(text)
    # Если 'редактировать товар' в тексте (помощь при редактировании товара)
    elif 'редактировать товар' in message.text.lower():
        user_id = message.chat.id
        text = """Прикрепите фото товара (старое/какое будет вместо старого) и напишите текст вида (без квадратных скобок):

/update [ID товара, который вы редактируете]/[Название товара]/[Описание товара]/[Категория]/[Цена]

*Изменятся все данные кроме ID, поэтому заполняйте всю информацию о товаре (ID, название, описание, цену, категорию и фото)"""
        if admin_check(user_id):
            await message.answer(text)
            # Если 'удалить товар' в тексте (помощь при удалении товара)
    elif 'удалить товар' in message.text.lower().replace('удалить товар из корзины', ''):
        user_id = message.chat.id
        text = 'Используйте команду:\n\n/delete [ID товара, который вы хотите удалить]'
        if admin_check(user_id):
            await message.answer(text)
    # Если 'Удалить товар из корзины' в тексте (помощь при удалении пользователем товара из корзины)
    elif 'удалить товар из корзины' in message.text.lower():
        text = 'Используйте команду (без квадратных скобок):\n\n/del [ID товара, который вы хотите удалить из корзины]'
        await message.answer(text)

        # Если '/del' в тексте (удаление пользователем товара из корзины)
    elif '/del ' in message.text.lower():
        user_id = message.chat.id
        sql_query = "SELECT products FROM carts WHERE id = ?"
        arguments = (user_id,)
        sql.execute(sql_query, arguments)
        products = sql.fetchone()
        products = products[0]
        product = message.text.lower().replace('/del ', '')
        if not str(product) in str(products):
            await message.answer(f'Товара с таким ID нет у вас в корзине. ID: {product}')
        else:
            products = products.replace(f'{product},', '').replace(f',{product}', '').replace(f'{product},',
                                                                                              '').replace(product, '')
            if products == '':
                sql.execute(f"DELETE FROM carts WHERE id = '{user_id}'")
            sql.execute(f"UPDATE carts SET products = '{products}' WHERE id = '{user_id}'")
            db.commit()
            await message.answer(f'Товар удален из корзины. ID: {product}')
