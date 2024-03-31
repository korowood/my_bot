from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from wu_tang import generate_name
from aiogram.types import MediaGroup, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from aiogram.dispatcher.webhook import *
import logging
import os
from config import TOKEN
import sqlite3

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

# Подключение к базе данных
conn = sqlite3.connect('bot_users.db')
cursor = conn.cursor()

# Создание таблицы пользователей, если она не существует
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        photo_id TEXT,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        rating INTEGER DEFAULT 0,
        nickname TEXT
    )
''')
conn.commit()


# Функция для добавления пользователя в базу данных
def add_user(user_id, username, first_name, last_name, nickname):
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, nickname)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, username, first_name, last_name))
    conn.commit()


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    realname = username if username else first_name
    nickname = generate_name(realname)
    add_user(user_id, username, first_name, last_name, nickname)
    await message.reply("Добро пожаловать! Вы успешно подключились к боту.")


@dp.message_handler(content_types=['photo'])
async def handle_photo_rating(message: types.Message):
    user_id = message.from_user.id

    photo_ids = [photo.file_id for i, photo in enumerate(message.photo) if i % len(message.photo) == 1]

    # Обновляем базу данных, сохраняя id фотографии для пользователя
    cursor.execute('UPDATE users SET photo_id = ? WHERE user_id = ?', (photo_ids[0], user_id))
    conn.commit()

    # Получаем список всех пользователей
    cursor.execute('SELECT user_id FROM users')
    user_ids = cursor.fetchall()

    # Создаем список медиа с фотографиями для отправки медиагруппой
    media = MediaGroup()
    for photo_id in photo_ids:
        media.attach_photo(photo_id)

    # Отправляем каждому пользователю сообщение с изображением и просьбой оценить его
    for user_id in user_ids:
        try:
            await bot.send_media_group(user_id[0], media)

        except Exception as e:
            logging.error(f"Ошибка отправки изображения пользователю {user_id[0]}: {e}")

    for user_id in user_ids:
        await bot.send_message(user_id[0], "Поставьте оценку от 1 до 10 этой фотографии:")


# Функция для обработки оценки фотографии
@dp.message_handler(lambda message: message.text.isdigit() and 0 < int(message.text) <= 10)
async def handle_rating(message: types.Message):
    user_id = message.from_user.id
    rating = int(message.text)
    # Обновляем базу данных, сохраняя оценку для пользователя
    cursor.execute('UPDATE users SET rating = ? WHERE user_id = ?', (rating, user_id))
    conn.commit()
    await message.reply("Спасибо за вашу оценку!")


# Функция для вычисления средней оценки всех пользователей
def calculate_average_rating():
    cursor.execute('SELECT rating FROM users WHERE rating > 0')
    ratings = cursor.fetchall()  # Получаем все оценки из базы данных
    total_ratings = sum(rating[0] for rating in ratings)  # Вычисляем сумму всех оценок
    min_ratings = min(rating[0] for rating in ratings)
    max_ratings = max(rating[0] for rating in ratings)
    num_ratings = len(ratings)  # Вычисляем количество оценок
    if num_ratings > 0:
        return total_ratings, num_ratings, min_ratings, max_ratings  # Возвращаем среднее значение
    else:
        return 0, 0, 0, 0  # Если нет оценок, возвращаем 0


# Функция для обнуления всех оценок в базе данных
def reset_ratings():
    cursor.execute('UPDATE users SET rating = 0')
    conn.commit()


@dp.message_handler(commands=['average_rating'])
async def get_average_rating(message: types.Message):
    total_ratings, num_ratings, min_ratings, max_ratings = calculate_average_rating()

    # Обнуляем все оценки в базе данных
    reset_ratings()

    # Получаем список всех пользователей
    cursor.execute('SELECT user_id FROM users')
    user_ids = cursor.fetchall()

    # Отправляем каждому пользователю сообщение о средней оценке
    for user_id in user_ids:
        try:
            await bot.send_message(user_id[0], f"Средняя оценка всех пользователей: {total_ratings / num_ratings:.2f} "
                                               f"Min: {min_ratings} | Max: {max_ratings} | Count: {num_ratings}")
        except Exception as e:
            logging.error(f"Ошибка отправки сообщения пользователю {user_id[0]}: {e}")


@dp.message_handler(commands=['notice'])
async def send_notice_to_all(message: types.Message):
    # Получаем текст уведомления из сообщения пользователя
    notification_text = message.text.split(maxsplit=1)[1]

    # Получаем список всех пользователей
    cursor.execute('SELECT user_id FROM users')
    user_ids = cursor.fetchall()

    # Отправляем уведомление каждому пользователю
    for user_id in user_ids:
        try:
            await bot.send_message(user_id[0], notification_text)
        except Exception as e:
            logging.error(f"Ошибка отправки уведомления пользователю {user_id[0]}: {e}")

    await message.reply("Уведомление успешно отправлено всем пользователям.")


# @dp.message_handler(commands=['voted'])
# async def show_voted_count(message: types.Message):
#     # Получаем последнюю фотографию из базы данных для каждого пользователя
#     cursor.execute('SELECT photo_id FROM users WHERE photo_id IS NOT NULL')
#     last_photo_ids = cursor.fetchall()
#
#     # Если есть хотя бы одна фотография, за которую проголосовали пользователи
#     if last_photo_ids:
#         last_photo_id = last_photo_ids[-1][0]  # Берем ID последней фотографии
#         # Получаем количество пользователей, проголосовавших за эту фотографию
#         cursor.execute('SELECT COUNT(DISTINCT user_id) FROM users WHERE photo_id = ?', (last_photo_id,))
#         voted_count = cursor.fetchone()[0]
#         await message.reply(f"Количество пользователей, поставивших рейтинг последней фотографии: {voted_count}")
#     else:
#         await message.reply("Пока ни один пользователь не поставил рейтинг ни одной фотографии.")
@dp.message_handler(commands=['voted'])
async def show_voted_count(message: types.Message):
    # Получаем количество пользователей, у которых рейтинг больше нуля
    cursor.execute('SELECT COUNT(DISTINCT user_id) FROM users WHERE rating > 0')
    voted_count = cursor.fetchone()[0]

    await message.reply(f"Количество пользователей, поставивших рейтинг: {voted_count}")


# Обработчик для команды /set_nickname
@dp.message_handler(commands=['set_nickname'])
async def set_nickname(message: types.Message):
    # Получаем список всех пользователей из базы данных
    cursor.execute('SELECT user_id, username, first_name FROM users WHERE nickname IS NULL')
    users_without_nickname = cursor.fetchall()

    for user_id, username, first_name in users_without_nickname:
        realname = username if username else first_name
        nickname = generate_name(realname)
        if nickname:
            update_nickname(user_id, nickname)
            await bot.send_message(user_id, f"Ваш никнейм успешно обновлен: {nickname}")
        else:
            await bot.send_message(user_id, "Не удалось сгенерировать никнейм.")

    await message.reply("Все никнеймы успешно обновлены.")


# Функция для обновления никнейма в базе данных
def update_nickname(user_id, nickname):
    cursor.execute('UPDATE users SET nickname = ? WHERE user_id = ?', (nickname, user_id))
    conn.commit()


@dp.message_handler(commands=['profile'])
async def get_profile(message: types.Message):
    user_id = message.from_user.id

    # Получаем никнейм пользователя из базы данных
    cursor.execute('SELECT nickname FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    if row:
        nickname = row[0]
        await message.reply(f"Ваш никнейм: {nickname}")
    else:
        await message.reply("Вы еще не установили никнейм. Используйте команду /set_nickname для установки никнейма.")


# Запускаем бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
