import psycopg2


class Sqdb:
    def __init__(self, host, password, port, database, user):
        self.connection = psycopg2.connect(host=host,
                                           password=password,
                                           port=port,
                                           database=database,
                                           user=user)
        # self.postgresql_pool = psycopg2.pool.ThreadedConnectionPool(1, 20,
        #                                                             host=host,
        #                                                             password=password,
        #                                                             port=port,
        #                                                             database=database,
        #                                                             user=user)
        # self.connection = self.postgresql_pool.getconn()
        self.cursor = self.connection.cursor()

    async def is_user_exists(self, user_id):
        with self.connection:
            self.cursor.execute(f"SELECT COUNT(*) from dict_users WHERE user_id = {user_id}")
            if_exist = self.cursor.fetchone()
            return if_exist[0]

    async def add_user(self, user_id):
        with self.connection:
            self.cursor.execute(f"SELECT COUNT(*) from dict_users WHERE user_id = {user_id}")
            if_exist = self.cursor.fetchone()[0]
            if not if_exist:
                self.cursor.execute(
                    f"INSERT INTO dict_users (user_id) VALUES ({user_id})")
                return True
            else:
                return False

    async def upd_dict(self, user_id, dict_):
        dict_ = str(dict_).replace("'", '"')
        with self.connection:
            self.cursor.execute(f"""UPDATE dict_users SET dict = '{dict_}' WHERE user_id = {user_id}""")

    async def upd_data(self, user_id, key, value):
        with self.connection:
            self.cursor.execute(
                f"""UPDATE dict_users SET {key} = {f"'{value}'" if isinstance(key, str) else value} WHERE user_id = {user_id}""")

    async def get_admins(self):
        with self.connection:
            self.cursor.execute('SELECT user_id FROM dict_users WHERE admin = TRUE')
            return [i[0] for i in self.cursor.fetchall()]

    async def get_data(self, user_id, data):
        with self.connection:
            self.cursor.execute(f'SELECT {data} FROM dict_users WHERE user_id = {user_id}')
            return self.cursor.fetchone()[0]
