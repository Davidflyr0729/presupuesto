import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'presupuesto_secret_key_2025')
    MYSQL_HOST = os.getenv('MYSQL_HOST', '127.0.0.1')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DB = os.getenv('MYSQL_DB', 'presupuesto_db')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))