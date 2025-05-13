import os
import time

import psycopg2.pool

host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")
dbname = os.getenv("DB_NAME")
while True:
    try:
        pool = psycopg2.pool.SimpleConnectionPool(1, 5,
                                          f"host={host} dbname={dbname} user={username} password={password} port={port}")
        break
    except psycopg2.OperationalError:
        print("Database is unreachable. Trying to reconnect")
        time.sleep(5)


def connect(func):
    def wrapper(*args, **kwargs):
        conn, curs = None, None
        try:
            conn = pool.getconn()
            curs = conn.cursor()

            kwargs['curs'] = curs
            result = func(*args, **kwargs)
            conn.commit()
        except psycopg2.OperationalError:
            raise psycopg2.OperationalError("Database is unreachable. Try later")
        finally:
            if curs:
                curs.close()
            if conn:
                pool.putconn(conn)
        return result

    return wrapper
