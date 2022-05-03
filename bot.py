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