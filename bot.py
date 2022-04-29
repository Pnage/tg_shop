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