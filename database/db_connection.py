import psycopg2.pool

pool = psycopg2.pool.SimpleConnectionPool(1, 5, user='postgres', password='postgres', database='tester')


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
