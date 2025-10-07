from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.user import UserModel

class AuthController:
    def __init__(self):
        self.bp = Blueprint('auth', __name__)
        self.user_model = UserModel()
        self.register_routes()

    def register_routes(self):
        self.bp.route('/login', methods=['GET', 'POST'])(self.login)
        self.bp.route('/register', methods=['GET', 'POST'])(self.register)
        self.bp.route('/logout')(self.logout)

    def login(self):
        """Manejar inicio de sesión"""
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            
            if not email or not password:
                flash('Por favor completa todos los campos', 'error')
                return render_template('auth/login.html')
            
            user = self.user_model.login(email, password)
            
            if user:
                # Configurar sesión NO permanente (se cierra al cerrar navegador)
                session.permanent = False
                session['user_id'] = user['id']
                session['user_name'] = user['nombre']
                session['user_email'] = user['email']
                session['user_role'] = user['rol_id']
                flash('¡Inicio de sesión exitoso!', 'success')
                return redirect(url_for('dashboard.index'))
            else:
                flash('Email o contraseña incorrectos', 'error')
        
        return render_template('auth/login.html')

    def register(self):
        """Manejar registro de usuarios"""
        if request.method == 'POST':
            nombre = request.form.get('nombre')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
            # Validaciones
            if not all([nombre, email, password, confirm_password]):
                flash('Por favor completa todos los campos', 'error')
                return render_template('auth/register.html')
            
            if password != confirm_password:
                flash('Las contraseñas no coinciden', 'error')
                return render_template('auth/register.html')
            
            if len(password) < 6:
                flash('La contraseña debe tener al menos 6 caracteres', 'error')
                return render_template('auth/register.html')
            
            if self.user_model.email_exists(email):
                flash('El email ya está registrado', 'error')
                return render_template('auth/register.html')
            
            try:
                user_id = self.user_model.create(nombre, email, password)
                flash('¡Registro exitoso! Ahora puedes iniciar sesión', 'success')
                return redirect(url_for('auth.login'))
            except Exception as e:
                flash('Error en el registro: ' + str(e), 'error')
        
        return render_template('auth/register.html')

    def logout(self):
        """Cerrar sesión"""
        session.clear()
        flash('Sesión cerrada exitosamente', 'success')
        return redirect(url_for('auth.login'))

# Crear instancia del controlador
auth_controller = AuthController()