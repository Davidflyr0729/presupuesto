from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from models.user import UserModel

class AdminController:
    def __init__(self):
        self.bp = Blueprint('admin', __name__, url_prefix='/admin')
        self.user_model = UserModel()
        self.register_routes()

    def register_routes(self):
        self.bp.route('/')(self.index)
        # Aquí agregaremos más rutas después

    def check_admin_access(self):
        """Verificar que el usuario sea administrador"""
        if 'user_id' not in session:
            flash('Debes iniciar sesión para acceder a esta página', 'error')
            return redirect(url_for('auth.login'))
        
        if session.get('user_role') != 1:  # 1 = Administrador
            flash('No tienes permisos para acceder a esta página', 'error')
            return redirect(url_for('dashboard.index'))
        
        return True

    def index(self):
        """Página principal de administración"""
        # Verificar acceso de administrador
        if not self.check_admin_access():
            return redirect(url_for('auth.login'))
        
        try:
            # Obtener estadísticas básicas
            total_usuarios = self.get_total_usuarios()
            usuarios = self.get_all_usuarios()  # ← NUEVO: Obtener lista de usuarios
            
            return render_template('admin/index.html',
                                 total_usuarios=total_usuarios,
                                 usuarios=usuarios,  # ← NUEVO: Pasar usuarios al template
                                 active_page='admin')
            
        except Exception as e:
            flash('Error al cargar el panel de administración', 'error')
            return redirect(url_for('dashboard.index'))

    def get_total_usuarios(self):
        """Obtener total de usuarios registrados"""
        try:
            query = "SELECT COUNT(*) as total FROM usuarios WHERE activo = 1"
            result = self.user_model.db.execute_query(query, fetch_one=True)
            return result['total'] if result else 0
        except Exception as e:
            print(f"Error al obtener total de usuarios: {e}")
            return 0

    def get_all_usuarios(self):
        """Obtener todos los usuarios registrados - Versión simple"""
        try:
            query = "SELECT * FROM usuarios ORDER BY id ASC"
            result = self.user_model.db.execute_query(query, fetch=True)
            print(f"DEBUG: Usuarios encontrados: {len(result) if result else 0}")
            
            # Si hay resultados, formatear las fechas manualmente
            if result:
                for usuario in result:
                    if usuario.get('fecha_creacion'):
                        usuario['fecha_creacion'] = usuario['fecha_creacion'].strftime('%d/%m/%Y')
                    else:
                        usuario['fecha_creacion'] = 'N/A'
            
            return result if result else []
        except Exception as e:
            print(f"Error al obtener usuarios: {e}")
            return []

# Crear instancia del controlador
admin_controller = AdminController()