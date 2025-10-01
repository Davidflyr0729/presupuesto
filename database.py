import mysql.connector
from mysql.connector import Error
import time

class Database:
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        """Conectar a la base de datos con manejo robusto de errores"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                print(f"🔗 Intentando conectar a MySQL (intento {attempt + 1})...")
                
                self.connection = mysql.connector.connect(
                    host='localhost',
                    user='root',
                    password='',
                    database='presupuesto_db',
                    autocommit=True,
                    connection_timeout=10,
                    buffered=True
                )
                
                if self.connection.is_connected():
                    print("✅ Conectado a la base de datos MySQL")
                    # Verificar la conexión
                    cursor = self.connection.cursor()
                    cursor.execute("SELECT 1")
                    cursor.close()
                    print("✅ Conexión verificada correctamente")
                    return
                    
            except Error as e:
                print(f"❌ Error conectando a MySQL (intento {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    print(f"⏳ Reintentando en {retry_delay} segundos...")
                    time.sleep(retry_delay)
                else:
                    print("💥 No se pudo conectar después de varios intentos")
                    self.connection = None
    
    def ejecutar_consulta(self, query, params=None):
        """Ejecutar consulta con manejo robusto de errores"""
        try:
            # Verificar y reconectar si es necesario
            if not self.connection or not self.connection.is_connected():
                print("🔄 Reconectando a la base de datos...")
                self.connect()
                if not self.connection:
                    print("💥 No hay conexión a la base de datos")
                    return None
            
            cursor = self.connection.cursor(dictionary=True)
            
            # Ejecutar consulta
            cursor.execute(query, params or ())
            
            # Procesar resultado según el tipo de consulta
            if query.strip().upper().startswith('SELECT'):
                result = cursor.fetchall()
            else:
                self.connection.commit()
                result = cursor.lastrowid  # Para INSERTs
            
            cursor.close()
            return result
            
        except Error as e:
            print(f"❌ Error en consulta MySQL: {e}")
            print(f"🔍 Query: {query}")
            print(f"🔍 Parámetros: {params}")
            
            # Intentar reconectar en caso de error de conexión
            if "MySQL Connection not available" in str(e) or "Lost connection" in str(e):
                print("🔄 Intentando reconectar...")
                self.connect()
            
            return None
        except Exception as e:
            print(f"💥 Error inesperado en consulta: {e}")
            return None