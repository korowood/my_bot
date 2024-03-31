import sqlite3


def delete_user(user_id):
    cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
    conn.commit()


# Подключение к базе данных
conn = sqlite3.connect('bot_users.db')
cursor = conn.cursor()

# cursor.execute('''
#     ALTER TABLE users
#     ADD COLUMN nickname TEXT;
# ''')

# conn.commit()
# delete_user(111767672)
# delete_user(322968938)
# delete_user(353354194)
# delete_user(465778033)

# Выполнение запроса для просмотра содержимого таблицы
cursor.execute("SELECT * FROM users")

# Получение результатов запроса
rows = cursor.fetchall()

for row in rows:
    print(row)


# Закрытие соединения с базой данных
conn.close()
