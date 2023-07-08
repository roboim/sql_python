import psycopg2
import pprint

class DataBaseStore:

    def create_dbs (self, conn, drop_flag=False):
        with conn.cursor() as cur:
            # удаление таблиц
            if drop_flag is True:
                cur.execute("""
                DROP TABLE ClientPhone;
                DROP TABLE Phone;
                DROP TABLE Client;
                """)

            conn.commit()  # фиксируем в БД

            cur.execute("""
            CREATE TABLE IF NOT EXISTS Client (
                client_id SERIAL PRIMARY KEY,
                surname VARCHAR(40) NOT NULL,
                firstname VARCHAR(40) NOT NULL,
                email VARCHAR(40) UNIQUE NOT NULL
            );
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS Phone (
                phone_id SERIAL PRIMARY KEY,
                number VARCHAR(12) UNIQUE NOT NULL
            );
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS ClientPhone (
                client_id INTEGER REFERENCES Client(client_id),
                phone_id INTEGER REFERENCES Phone(phone_id),
                CONSTRAINT pkcp PRIMARY KEY (client_id, phone_id)
            );
            """)

            conn.commit()  # фиксируем в БД

    def addclient_dbs(self, conn, data_client=("", "", "")):
        with conn.cursor() as cur:
            surname = ""
            firstname = ""
            email = ""
            if data_client[0] == "":
                surname = input("\nВведите фамилию заказчика: ")
                firstname = input("\nВведите имя заказчика: ")
                email = input("\nВведите e-mail заказчика: ")
            else:
                surname = data_client[0]
                firstname = data_client[1]
                email = data_client[2]

            try:
                cur.execute("""
                INSERT INTO Client(surname, firstname, email) VALUES(%s, %s, %s);
                """, (surname, firstname, email))
                conn.commit()  # фиксируем в БД

                print(f'\nУспешно введены данные.'
                      f'\n Фамилия: {surname}'
                      f'\n Имя: {firstname}'
                      f'\n e-mail: {email}')
            except:
                print('Ошибка ввода или заказчик с данным e-mail уже существует!')


database_dbs = "musicstoreclients"
user_dbs="postgres"
password_dbs=""

print(f'\nБаза данных: {database_dbs}'
      f'\nПользователь: {user_dbs}'
      f'\nПароль: {password_dbs}')
db_store = DataBaseStore()

print('\nСоздаётся база данных с пилотными заказчиками')
cl_0 = ("", "", "")
cl_1 = ("Гагарин","Юрий", "yg@cosmos.ru")
cl_2 = ("Королёв","Сергей", "sk@cosmos.ru")
cl_3 = ("Циолковский","Константин", "kc@cosmos.ru")

with psycopg2.connect(database=database_dbs, user=user_dbs, password=password_dbs) as connection:
    db_store.create_dbs(connection,True)
    db_store.addclient_dbs(connection,cl_1)
    db_store.addclient_dbs(connection,cl_2)
    db_store.addclient_dbs(connection,cl_3)

    # Введите нового заказчика
    db_store.addclient_dbs(connection)

connection.close()

f=input("\nВведите любые данные для завершения")