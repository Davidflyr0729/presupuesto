import pymysql
from config import Config

class Database:
    def get_connection(self):
        """Obtener conexión a la base de datos"""
        return pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            port=Config.MYSQL_PORT,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

    def execute_query(self, query, params=None, fetch=False, fetch_one=False):
        """Ejecutar consulta en la base de datos"""
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params or ())
                
                if fetch:
                    result = cursor.fetchall()
                elif fetch_one:
                    result = cursor.fetchone()
                else:
                    result = cursor.lastrowid
                
                if not fetch and not fetch_one:
                    connection.commit()
                
                return result
        except Exception as e:
            connection.rollback()
            raise e
        finally:
            connection.close()