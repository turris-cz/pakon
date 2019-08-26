import sqlite3


class Database:
    def __init__(self, path):
        try:
            self.connection = sqlite3.connect(path)
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()
        except sqlite3.Error as error:
            raise error

    def close(self):
        if self.connection:
            self.cursor.close()
            self.connection.close()

    def select(self, sql, values):
        if values:
            self.cursor.execute(sql, values)
        else:
            self.cursor.execute(sql)
        return self.cursor.fetchall()

    def attach_database(self, path, alias):
        self.connection.execute("attach database ? as ?", (path, alias,))

    def dettach_database(self, alias):
        self.connection.execute("detach database ?", (alias,))

    def execute_many(self, sql, values):
        if not values:
            raise Exception("No values to insert")
        self.cursor.executemany(sql, values)
        self.connection.commit()

    def update(self, sql, values):
        """update handle inserting, updating and removing
        """
        if values:
            self.cursor.execute(sql, values)
        else:
            self.cursor.execute(sql)
        self.connection.commit()
