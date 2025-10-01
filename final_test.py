from models.user import UserModel

def test_login():
    """Probar el login con las credenciales correctas"""
    user_model = UserModel()
    
    # Credenciales correctas
    email = "nelson.galvez@flyr.com"
    password = "123456"
    
    print("🔐 Probando login...")
    print(f"📧 Email: {email}")
    print(f"🔑 Contraseña: {password}")
    
    user = user_model.login(email, password)
    
    if user:
        print("🎉 ¡LOGIN EXITOSO!")
        print(f"👤 Nombre: {user['nombre']}")
        print(f"🆔 ID: {user['id']}")
        print(f"📧 Email: {user['email']}")
        return True
    else:
        print("❌ LOGIN FALLIDO")
        return False

if __name__ == '__main__':
    success = test_login()
    if success:
        print("\n✅ ¡Todo funciona correctamente! Ahora puedes usar la aplicación.")
    else:
        print("\n❌ Aún hay problemas. Revisa la configuración.")