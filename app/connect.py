import psycopg2
#Connect to database
def connectdb():
    try:
        conn = psycopg2.connect(
                                host = 'localhost',
                                database = 'CongNgheWebTest',
                                user = 'postgres',
                                password = '159357',
                                port = '5432')
        cur = conn.cursor()
        
        cur.execute("SET schema 'ChatApp';")
        print("Successfully connected")
    except Exception as error:
        print('error: ', error)

    return conn,cur


def call_postgres_function(func_name, params):
    conn, cur = connectdb()
    if conn is None:
        return None

    try:
        cur.callproc(func_name, params)
        # Fetch results if applicable (based on function's return type)
        if cur.description:
            results = cur.fetchall()
        else:
            results = None
        conn.commit()
        return results
    except Exception as error:
        print('Error:', error)
        conn.rollback()
        return None
    finally:
        if conn:
            conn.close()

func = "delete_empty_room"
parameters = ("23",)
results = call_postgres_function(func,parameters)
