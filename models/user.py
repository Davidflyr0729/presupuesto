import bcrypt
from utils.database import Database

class UserModel:
    def __init__(self):
        self.db = Database()
        self.table = "usuarios"

    def create(self, nombre, email, clave, rol_id=2):
        """Crear nuevo usuario con contraseña hasheada"""
        hashed_password = bcrypt.hashpw(clave.encode('utf-8'), bcrypt.gensalt())
        
        query = f"""
        INSERT INTO {self.table} (nombre, email, clave, rol_id, activo) 
        VALUES (%s, %s, %s, %s, %s)
        """
        
        return self.db.execute_query(
            query, 
            (nombre, email, hashed_password.decode('utf-8'), rol_id, 1)
        )

    def get_by_email(self, email):
        """Obtener usuario por email"""
        query = f"SELECT * FROM {self.table} WHERE email = %s AND activo = 1"
        result = self.db.execute_query(query, (email,), fetch_one=True)
        return result

    def verify_password(self, plain_password, hashed_password):
        """Verificar contraseña - compatible con formatos $2y$ y $2b$"""
        try:
            # Convertir formato $2y$ a $2b$ si es necesario
            if hashed_password.startswith('$2y$'):
                hashed_password = '$2b$' + hashed_password[4:]
            
            result = bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
            return result
        except Exception as e:
            print(f"Error en verificación de contraseña: {e}")
            return False

    def login(self, email, password):
        """Autenticar usuario"""
        user = self.get_by_email(email)
        if user and self.verify_password(password, user['clave']):
            return user
        return None

    def email_exists(self, email):
        """Verificar si el email ya existe"""
        query = f"SELECT id FROM {self.table} WHERE email = %s"
        result = self.db.execute_query(query, (email,), fetch=True)
        return len(result) > 0

    def get_by_id(self, user_id):
        """Obtener usuario por ID"""
        query = f"SELECT id, nombre, email, rol_id FROM {self.table} WHERE id = %s AND activo = 1"
        return self.db.execute_query(query, (user_id,), fetch_one=True)