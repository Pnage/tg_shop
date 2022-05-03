from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3

settings = open('settings.txt','r').readline().split(',')

#Пароль администратора (используется при добавлении пользователя в админы командой /admin [пароль])
admin_password = str(settings[0])
print(admin_password)

#Создание базы данных, курсора
db = sqlite3.connect('server.db')
sql = db.cursor()

#Создание таблицы корзин пользователей
sql.execute("""CREATE TABLE IF NOT EXISTS carts (
    id INT,
    products TEXT
)""")

#Создание таблицы с товарами
sql.execute("""CREATE TABLE IF NOT EXISTS products (
    id INT,
    name TEXT,
    description TEXT,
    category TEXT,
    price TEXT,
    photo BLOB
)""")

#Создание таблицы администраторов
sql.execute("""CREATE TABLE IF NOT EXISTS admins (id TEXT, username TEXT)""")


if sql.execute(f"SELECT * FROM products WHERE id = '9999999999'").fetchone() is None:
    sql.execute("INSERT INTO products VALUES (?,?,?,?,?,?)",(9999999999, None, None, None, None, None))

#Сохранение всех изменений в БД
db.commit()

#Настройка бота
bot = Bot(token=settings[1])
dp = Dispatcher(bot)

#Первое обновление категорий товаров
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

#Проверка пользователя на права администратора
def admin_check(user_id):
    sql.execute(f"SELECT id FROM admins WHERE id = '{user_id}'")
    if sql.fetchone() is None:
        return False
    else:
        return True

#Конвертация файла в байты для дальнейшей записи в БД
def convert_to_binary_data(filename):
    # Преобразование данных в двоичный формат
    with open(filename, 'rb') as file:
        blob_data = file.read()
    return blob_data

#Временная запись в файл картинки из БД по ID, для отправки пользователю
def get_image(Id):
    sql.execute(f"SELECT photo FROM products WHERE id = '{Id}'")
    content = sql.fetchone()
    if  content is None:
        print(f'Нет товара с ID {Id}')
    else:
        with open('img_to_write.jpg','wb') as file:
            file.write(content[0])

#Получение всей инфы о товаре из БД по одному ID
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

#Обновление в БД записи товара при редактировании
def update_product(Id, info):
    sql.execute(f"SELECT * FROM products WHERE id = '{Id}'")
    content = sql.fetchone()
    if content is None:
        print(f'Нету такого товара ID: {Id}')
    else:
        new_photo = convert_to_binary_data('img_for_read.jpg')
        sql.execute(f"UPDATE products SET name = ?, description = ?, category = ?, price = ?, photo = ? WHERE id = ?", (info[1],info[2],info[3].lower(),info[4],new_photo,Id))
        db.commit()

#Удаление товара из БД по ID
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