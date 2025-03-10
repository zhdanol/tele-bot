import psycopg2

db_name = 'postgres'
db_user = 'postgres'
db_password = '1589'
db_host = 'localhost'
db_port = '5432'

def get_db_connection():
    try:
        connection = psycopg2.connect(user=db_user,  
                                      password=db_password,
                                      host=db_host,
                                      port=db_port,
                                      database=db_name)
        return connection
    except Exception as e:
        print(f"Ошибка при подключении к базе данных: {e}")
        return None
