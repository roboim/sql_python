import psycopg2
import pprint

class Person:
    def __init__(self, surname:str, firstname:str, email:str, phones:list):
        self.surname = surname
        self.firstname = firstname
        self.email = email
        self.phones = phones


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
                client_id INTEGER REFERENCES Client(client_id) ON DELETE CASCADE,
                phone_id INTEGER REFERENCES Phone(phone_id) ON DELETE CASCADE,
                CONSTRAINT pkcp PRIMARY KEY (client_id, phone_id)
            );
            """)

            conn.commit()  # фиксируем в БД

    def add_client_dbs(self, conn, db_client):
        with conn.cursor() as cur:
            if db_client.surname == "":
                db_client.surname = input("\nВведите фамилию заказчика: ")
                db_client.firstname = input("\nВведите имя заказчика: ")
                db_client.email = input("\nВведите e-mail заказчика: ")

            try:
                cur.execute("""
                INSERT INTO Client(surname, firstname, email) VALUES(%s, %s, %s) RETURNING client_id;
                """, (db_client.surname, db_client.firstname, db_client.email,))
                get_client_id = cur.fetchone()[0]

                print(f'\nУспешно введены данные.'
                      f'\n Фамилия: {db_client.surname}'
                      f'\n Имя: {db_client.firstname}'
                      f'\n e-mail: {db_client.email}')

                db_store.add_client_phone_dbs(conn, get_client_id, db_client.phones)
            except:
                print('\nОшибка ввода или заказчик с данным e-mail уже существует!')


    def add_client_phone_dbs(self, conn, client_id, phonenum=""):
        with conn.cursor() as cur:
            if phonenum == "":
                phonenum = input("\nВведите номер телефона(не более 10 цифр): +7 ")
                phonenum = "+7" + phonenum

            phonenum = phonenum[:12]
            if phonenum != "+7":
                try:
                    cur.execute("""
                    INSERT INTO Phone(number) VALUES(%s) RETURNING phone_id;
                    """, (phonenum,))
                    phonenum_id = cur.fetchone()

                    cur.execute("""
                    INSERT INTO ClientPhone(client_id, phone_id) VALUES(%s, %s) RETURNING phone_id;
                    """, (client_id, phonenum_id,))
                    conn.commit()  # фиксируем в БД
                    print(f' Записан номер {phonenum} для заказчика {client_id}.')
                except:
                    print('\nОшибка ввода телефонного номера!')
            else:
                print('\nТелефонный номер не введён!')

    def delete_client_phone_dbs(self,conn, client_id, phone_str):
        with conn.cursor() as cur:
            try:
                # поиск phone_id
                cur.execute("""
                SELECT phone_id FROM Phone WHERE number=%s;
                """, (phone_str,))
                phone_id = cur.fetchone()[0]

                # удаление данных Phone и ClientPhone (D из CRUD, учитывая DELETE ON CASCADE)
                cur.execute("""
                DELETE FROM Phone WHERE phone_id=%s;
                """, (phone_id,))
                conn.commit()  # фиксируем в БД
                print(f'\nТелефонный номер {phone_str} удалён у заказчика {client_id}!')
            except:
                print(f'Ошибка удаления телефонного у заказчика {client_id}!')

    def adjust_client_dbs(self, conn, client_id, db_client):
        with conn.cursor() as cur:
            try:
                # обновление данных (U из CRUD)
                cur.execute("""
                UPDATE Client SET surname=%s,firstname=%s, email=%s WHERE client_id=%s RETURNING client_id;
                """, (db_client.surname,db_client.firstname,db_client.email,client_id, ))
                conn.commit()  # фиксируем в БД
                print(f'\nИзменены данные заказчика {client_id}: '
                      f'{db_client.surname}, {db_client.firstname}, {db_client.email}!')
                db_store.add_client_phone_dbs(conn, client_id, db_client.phones)

            except:
                print('Ошибка обновления данных!')

    def delete_client_dbs(self, conn, client_id):
        with conn.cursor() as cur:
            data_person = DataBaseStore()
            cur.execute("""
            SELECT Phone.number FROM Phone 
            JOIN ClientPhone ON ClientPhone.phone_id = Phone.phone_id
            WHERE ClientPhone.client_id=%s;
            """, (client_id,))
            phone_ids = cur.fetchall()

        for phone in phone_ids:
            data_person.delete_client_phone_dbs(conn, client_id, phone[0])

        with conn.cursor() as cur:
            try:
                # удаление данных Client (D из CRUD, учитывая DELETE ON CASCADE)
                cur.execute("""
                DELETE FROM Client WHERE client_id=%s;
                """, (client_id,))
                conn.commit()  # фиксируем в БД
                print(f'Удалён заказчик {client_id}!')

            except:
                print(f'Ошибка удаления заказчика {client_id}!')

    def search_client_dbs(self,conn, surname=None, firstname=None, email=None, phone=None):
        surname = surname.lower()
        firstname = firstname.lower()
        email = email.lower()
        phone = phone.lower()

        with conn.cursor() as cur:
            data_person = DataBaseStore()
            try:
                cur.execute("""
                SELECT DISTINCT Client.client_id,Client.surname,Client.firstname,Client.email FROM Client
                JOIN ClientPhone ON ClientPhone.client_id = Client.client_id
                JOIN Phone ON Phone.phone_id = ClientPhone.phone_id
                WHERE lower(Client.surname)=%s OR lower(Client.firstname)=%s
                OR lower(Client.email)=%s OR Phone.number=%s;
                """, (surname,firstname,email,phone,))
                clients_ids = cur.fetchall()
                if len(clients_ids) == 0:
                    print("\nПо указанным данным результатов нет!")
                else:
                    print("\nРезультаты поиска:")
                    for client in clients_ids:
                        cur.execute("""
                        SELECT DISTINCT Phone.number FROM Phone
                        JOIN ClientPhone ON ClientPhone.phone_id = Phone.phone_id
                        WHERE ClientPhone.client_id=%s;
                        """, (client[0],))
                        conn.commit()  # фиксируем в БД
                        data = cur.fetchone()
                        client = client + data
                        print(client)
            except:
                print(f'Ошибка поиска!')

print('Для удаления таблиц при проверке используйте функцию: db_store.create_dbs(connection,True)')

database_dbs = "postgres"
user_dbs="postgres"
password_dbs=input("ВВЕДИТЕ ПАРОЛЬ, ПОЖАЛУЙСТА, от postgres: ")

print(f'\nБаза данных: {database_dbs}'
      f'\nПользователь: {user_dbs}'
      f'\nПароль: {password_dbs}')
db_store = DataBaseStore()

print('\nСоздаётся база данных с пилотными заказчиками')
cl_0 = Person("", "", "", "")
cl_1 = Person("Гагарин","Юрий","yg@cosmos.ru","+79991112233")
cl_2 = Person("Королёв","Сергей", "sk@cosmos.ru", "+79991112244")
cl_3 = Person("Циолковский","Константин", "kc@cosmos.ru", "+79991112255")
cl_4 = Person("ГАГАРИН","ЮРИЙ", "YG@COSMOS.RU", "+78888888888")
cl_5 = Person("Фамилия","Имя", "Почта@COSMOS.RU", "+77777777777")


with psycopg2.connect(database=database_dbs, user=user_dbs, password=password_dbs) as connection:
    db_store.create_dbs(connection,False)
    db_store.add_client_dbs(connection, cl_5)
    db_store.add_client_dbs(connection,cl_1)
    db_store.add_client_dbs(connection,cl_2)
    db_store.add_client_dbs(connection,cl_3)
    db_store.add_client_phone_dbs(connection, 1, "+76666666666")
    db_store.adjust_client_dbs(connection, 2, cl_4)
    db_store.add_client_phone_dbs(connection, 1, "+79991112299")
    db_store.search_client_dbs(connection, "КоролёВ", "СЕРГЕЙ", "YG@COSMOS.RU", "+79991112255")
    db_store.search_client_dbs(connection, "", "", "", "")
    db_store.delete_client_phone_dbs(connection,1,"+79991112299")
    db_store.delete_client_dbs(connection, 1)

    # Введите нового заказчика
    db_store.add_client_dbs(connection,cl_0)

connection.close()

f=input("\nВведите любые данные для завершения")