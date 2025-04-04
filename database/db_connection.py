import psycopg2.pool
import os

# эту часть в консоли прописать сначала или где-то задать?
os.environ["DB_HOST"] = 'localhost'
os.environ["DB_PORT"] = '5432'
os.environ["DB_USERNAME"] = 'postgres'
os.environ["DB_PASSWORD"] = 'postgres'
os.environ["DB_NAME"] = 'tester'

host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")
dbname = os.getenv("DB_NAME")
pool = psycopg2.pool.SimpleConnectionPool(1, 5,
                                          f"host={host} dbname={dbname} user={username} password={password} port={port}")


# pool = psycopg2.pool.SimpleConnectionPool(1, 5, user='postgres', password='postgres', database='tester')


def connect(func):
    def wrapper(*args, **kwargs):
        conn, curs = None, None
        try:
            conn = pool.getconn()
            curs = conn.cursor()

            kwargs['curs'] = curs
            result = func(*args, **kwargs)
            conn.commit()
        finally:
            if curs:
                curs.close()
            if conn:
                pool.putconn(conn)
        return result

    return wrapper
