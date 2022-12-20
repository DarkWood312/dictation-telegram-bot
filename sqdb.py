from os import environ

import psycopg2


class Sqdb:
    def __init__(self, host, password, port, database, user):
        self.connection = psycopg2.connect(host=host,
                                           password=password,
                                           port=port,
                                           database=database,
                                           user=user)
        self.cursor = self.connection.cursor()

    def is_user_exists(self, user_id):
        with self.connection:
            self.cursor.execute(f"SELECT COUNT(*) from dict_users WHERE user_id = {user_id}")
            if_exist = self.cursor.fetchone()
            return if_exist[0]

    def add_user(self, user_id):
        if not (Sqdb(environ['SQL_HOST'], environ['SQL_PASSWORD'], environ['SQL_PORT'], environ['SQL_DATABASE'],
                     environ['SQL_USER']).is_user_exists(user_id)):
            with self.connection:
                self.cursor.execute(
                    f"INSERT INTO dict_users (user_id) VALUES ({user_id})")
                return True
        else:
            return False

    def upd_dict(self, user_id, dict_):
        dict_ = str(dict_).replace("'", '"')
        with self.connection:
            self.cursor.execute(f"""UPDATE dict_users SET dict = '{dict_}' WHERE user_id = {user_id}""")

    def upd_shuffle(self, user_id, value):
        with self.connection:
            self.cursor.execute(f"UPDATE dict_users SET shuffle = {value} WHERE user_id = {user_id}")

    def get_data(self, user_id, data):
        with self.connection:
            self.cursor.execute(f'SELECT {data} FROM dict_users WHERE user_id = {user_id}')
            return self.cursor.fetchone()[0]