import sqlite3


class BenchmarkLogger(object):
    def log_times(self, time_dict):
        pass

    def log_times_keeper(self, time_keeper):
        return self.log_times(time_keeper.logged_times)


class FileBenchmarkLogger(BenchmarkLogger):
    def __init__(self, filename, fields, seperator=', '):
        self.file = open(filename, 'w')
        self.fields = fields
        self.seperator = seperator
        self._write_headline()

    def _write_headline(self):
        return self.file.write("%s\n" % self.seperator.join(self.fields))

    def log_times(self, time_dict):
        result = [str(time_dict[column]) if column in time_dict else "None" for column in self.fields]
        self.file.write("%s\n" % self.seperator.join(result))

    def close(self):
        self.file.close()


def db_create_insert(table_name, fields):
    insert_quest = (len(fields)) * "?, "
    return "INSERT INTO %s VALUES (%s);" % (table_name, insert_quest[:-2])


def db_create_script(fields, name):
    script = "CREATE TABLE IF NOT EXISTS %s (" % name
    for column in fields:
        script += "%s REAL, " % column
    script = "%s);\n" % script[:-2]
    return script


def connect_db(db_filename):
    return sqlite3.connect(db_filename, timeout=2 ** 30)


class SQLLiteBenchmarkLogger(BenchmarkLogger):
    def __init__(self, db_name, fields, table_name):
        self.db_name = db_name
        self.table_name = table_name
        self.fields = fields
        self.log = []
        self.conn = connect_db(self.db_name)
        self._create_table()

    def _create_table(self):
        script = db_create_script(self.fields, self.table_name)
        lines = [l + ";" for l in script.split(";")]
        for line in lines:
            self.conn.execute(line)

    def log_times(self, time_dict):
        result = [time_dict[column] if column in time_dict else None for column in self.fields]
        self.log.append(tuple(result))

    def flush_to_db(self):
        conn = self.conn
        c = conn.cursor()
        try:
            insert_stmt = db_create_insert(self.table_name, self.fields)
            for result in self.log:
                c.execute(insert_stmt, result)
            conn.commit()
        finally:
            c.close()

    def close(self):
        try:
            self.flush_to_db()
        finally:
            self.conn.close()
