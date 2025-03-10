from db_bot import get_db_connection


def data_base():
    """Создаёт таблицы в базе данных и заполняет их начальными данными."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('''
            CREATE TABLE users (
                user_id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
     
                        
                ''')
            
            cur.execute('''
            CREATE TABLE IF NOT EXISTS words (
	            id SERIAL PRIMARY KEY,
                english_word VARCHAR(100) UNIQUE NOT NULL,
	            russian_word VARCHAR(100) NOT NULL	
            )      
                        
                ''')
            
            cur.execute('''
            CREATE TABLE IF NOT EXISTS user_words (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL REFERENCES users (user_id),
                english_word VARCHAR(100) NOT NULL,
                russian_word VARCHAR(100) NOT NULL,
                UNIQUE (user_id, english_word)
            )      
                        
                ''')
            

            conn.commit()
            
            
def user_check(username, user_id):
    """Проверяет, существует ли пользователь в базе данных и создает его, если необходимо."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO users (username, user_id)
	            VALUES(%s, %s)
                ON CONFLICT (user_id) DO UPDATE
                SET username = EXCLUDED.username
                ''',(user_id, username))
            conn.commit()

def fill_common_words(common_words):
    """Заполняет общий словарь."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany('''
                INSERT INTO words (english_word, russian_word)
                VALUES (%s, %s)
                ON CONFLICT (english_word) DO NOTHING
                        ''', common_words)
            conn.commit()
            
def get_random_words(cid, limit=4):
    """Получает случайные слова из общего и персонального словарей."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT english_word, russian_word
                FROM (
                  SELECT w.english_word, w.russian_word
                    FROM words w
                   UNION
                  SELECT uw.english_word, uw.russian_word
                    FROM users_words uw
                   WHERE uw.user_id = %s
                     ) AS combined_words
                   ORDER BY RANDOM()
                   LIMIT %s;
                ''', (cid, limit))
            return cur.fetchall()

def check_words(word):
    """Проверяет, существует ли слово в общем словаре."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT 1
                  FROM words
                 WHERE english_word = %s
                ''',(word,))
            return cur.fetchone() is not None

def add_word_user(user_id, english_word, russian_word):
    """Сохраняет слово в персональный словарь."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO user_words (user_id, english_word, russian_word)
                VALUES (%s, %s, %s)
                ON CONFLICT (users_id, english_word) DO NOTHING
                ''',(user_id, english_word.strip().capitalize(), russian_word.strip().capitalize()))
            conn.commit()

def delete_words_users(user_id, delete_word):
    """Удаляет слово из персонального словаря."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                DELETE FROM user_words
                WHERE user_id = %s
                  AND english_word = %s
                RETURNING english_word;
            ''', (user_id, delete_word))
            result = cur.fetchone()
            return result
        
def update_users_words(user_id, english_word, russian_word):
    """Обновляет персональный словарь."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO user_words (user_id, english_word, russian_word)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, english_word) 
                DO UPDATE SET russian_word = EXCLUDED.russian_word
            ''', (user_id, english_word.strip().capitalize(), russian_word.strip().capitalize()))
            conn.commit()