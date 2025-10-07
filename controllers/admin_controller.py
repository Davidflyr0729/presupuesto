from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from models.user import UserModel
import bcrypt
from datetime import datetime, timedelta

class AdminController:
    def __init__(self):
        self.bp = Blueprint('admin', __name__, url_prefix='/admin')
        self.user_model = UserModel()
        self.register_routes()

    def register_routes(self):
        self.bp.route('/')(self.index)
        self.bp.route('/usuarios')(self.admin_usuarios)
        self.bp.route('/editar_usuario/<int:user_id>', methods=['GET', 'POST'])(self.editar_usuario)
        self.bp.route('/eliminar_usuario/<int:user_id>')(self.eliminar_usuario)
        self.bp.route('/estadisticas')(self.estadisticas)  # NUEVA RUTA

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
            usuarios = self.get_all_usuarios()
            ingresos_totales = self.get_ingresos_totales()
            gastos_totales = self.get_gastos_totales()
            
            # Debug prints
            print(f"DEBUG - Total usuarios: {total_usuarios}")
            print(f"DEBUG - Ingresos totales: {ingresos_totales}")
            print(f"DEBUG - Gastos totales: {gastos_totales}")
            
            return render_template('admin/index.html',
                                 total_usuarios=total_usuarios,
                                 usuarios=usuarios,
                                 ingresos_totales=ingresos_totales,
                                 gastos_totales=gastos_totales,
                                 active_page='admin')
            
        except Exception as e:
            flash('Error al cargar el panel de administración', 'error')
            return redirect(url_for('dashboard.index'))

    def admin_usuarios(self):
        """Página de gestión de usuarios"""
        if not self.check_admin_access():
            return redirect(url_for('auth.login'))
        
        try:
            usuarios = self.get_all_usuarios()
            return render_template('admin/usuarios.html', 
                                 usuarios=usuarios,
                                 active_page='admin_usuarios')
        except Exception as e:
            flash('Error al cargar la gestión de usuarios', 'error')
            return redirect(url_for('admin.index'))

    def estadisticas(self):
        """Página de estadísticas del sistema"""
        if not self.check_admin_access():
            return redirect(url_for('auth.login'))
        
        try:
            # Estadísticas básicas
            total_usuarios = self.get_total_usuarios()
            ingresos_totales = self.get_ingresos_totales()
            gastos_totales = self.get_gastos_totales()
            
            # Estadísticas avanzadas
            usuarios_activos = self.get_usuarios_activos()
            promedio_ingresos = self.get_promedio_ingresos()
            promedio_gastos = self.get_promedio_gastos()
            balance_total = ingresos_totales - gastos_totales
            
            # Estadísticas por categorías
            top_categorias_ingresos = self.get_top_categorias_ingresos()
            top_categorias_gastos = self.get_top_categorias_gastos()
            
            # Estadísticas temporales
            ingresos_ultimo_mes = self.get_ingresos_ultimo_mes()
            gastos_ultimo_mes = self.get_gastos_ultimo_mes()
            variacion_ingresos = self.get_variacion_ingresos()
            variacion_gastos = self.get_variacion_gastos()
            
            return render_template('admin/statistics.html',
                                 total_usuarios=total_usuarios,
                                 ingresos_totales=ingresos_totales,
                                 gastos_totales=gastos_totales,
                                 usuarios_activos=usuarios_activos,
                                 promedio_ingresos=promedio_ingresos,
                                 promedio_gastos=promedio_gastos,
                                 balance_total=balance_total,
                                 top_categorias_ingresos=top_categorias_ingresos,
                                 top_categorias_gastos=top_categorias_gastos,
                                 ingresos_ultimo_mes=ingresos_ultimo_mes,
                                 gastos_ultimo_mes=gastos_ultimo_mes,
                                 variacion_ingresos=variacion_ingresos,
                                 variacion_gastos=variacion_gastos,
                                 active_page='estadisticas')
            
        except Exception as e:
            print(f"Error al cargar estadísticas: {str(e)}")
            flash('Error al cargar las estadísticas del sistema', 'error')
            return redirect(url_for('admin.index'))

    def editar_usuario(self, user_id):
        """Editar usuario"""
        if not self.check_admin_access():
            return redirect(url_for('auth.login'))

        if request.method == 'POST':
            try:
                nombre = request.form['nombre']
                email = request.form['email']
                rol = request.form['rol_id']
                activo = request.form.get('activo', 1)
                password = request.form.get('password', '')
                
                print(f"DEBUG: Actualizando usuario {user_id} - nombre: {nombre}, email: {email}, rol: {rol}, activo: {activo}, password_provided: {bool(password)}")
                
                # Construir la consulta dinámicamente según si se proporcionó contraseña
                if password:
                    # Usar bcrypt para el hash (igual que en UserModel.create)
                    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                    
                    query = """
                        UPDATE usuarios 
                        SET nombre = %s, email = %s, rol_id = %s, activo = %s, clave = %s
                        WHERE id = %s
                    """
                    params = (nombre, email, rol, activo, hashed_password.decode('utf-8'), user_id)
                else:
                    # Si no se proporcionó contraseña, mantener la actual
                    query = """
                        UPDATE usuarios 
                        SET nombre = %s, email = %s, rol_id = %s, activo = %s
                        WHERE id = %s
                    """
                    params = (nombre, email, rol, activo, user_id)
                
                # Ejecutar la consulta
                self.user_model.db.execute_query(query, params)
                
                flash('Usuario actualizado correctamente', 'success')
                return jsonify({'success': True}), 200
                
            except Exception as e:
                print(f"ERROR al actualizar usuario: {str(e)}")
                flash(f'Error al actualizar el usuario: {str(e)}', 'error')
                return jsonify({'success': False, 'error': str(e)}), 500
        
        # GET: Mostrar formulario de edición (esto ya no se usa con el modal)
        try:
            query = "SELECT * FROM usuarios WHERE id = %s"
            usuario = self.user_model.db.execute_query(query, (user_id,), fetch_one=True)
            
            if not usuario:
                flash('Usuario no encontrado', 'error')
                return redirect(url_for('admin.index'))
            
            return render_template('admin/editar_usuario.html', 
                                 usuario=usuario,
                                 active_page='admin_usuarios')
        except Exception as e:
            flash('Error al cargar el usuario', 'error')
            return redirect(url_for('admin.index'))

    def eliminar_usuario(self, user_id):
        """Eliminar usuario"""
        if not self.check_admin_access():
            return redirect(url_for('auth.login'))

        try:
            # Verificar que no se pueda eliminar a sí mismo
            if user_id == session.get('user_id'):
                flash('No puedes eliminar tu propio usuario', 'error')
                return redirect(url_for('admin.index'))
            
            query = "DELETE FROM usuarios WHERE id = %s"
            self.user_model.db.execute_query(query, (user_id,))
            
            flash('Usuario eliminado correctamente', 'success')
            
        except Exception as e:
            flash(f'Error al eliminar el usuario: {str(e)}', 'error')
        
        # CORREGIDO: Redirigir a admin.index en lugar de admin.admin_usuarios
        return redirect(url_for('admin.index'))

    def get_total_usuarios(self):
        """Obtener total de usuarios registrados"""
        try:
            query = "SELECT COUNT(*) as total FROM usuarios WHERE activo = 1"
            result = self.user_model.db.execute_query(query, fetch_one=True)
            return result['total'] if result else 0
        except Exception as e:
            print(f"Error al obtener total de usuarios: {e}")
            return 0

    def get_usuarios_activos(self):
        """Obtener número de usuarios activos (con movimientos recientes)"""
        try:
            # Usuarios que han tenido actividad en los últimos 30 días
            query = """
                SELECT COUNT(DISTINCT usuario_id) as total 
                FROM (
                    SELECT usuario_id FROM ingresos WHERE fecha >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                    UNION 
                    SELECT usuario_id FROM gastos WHERE fecha >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                ) as actividad
            """
            result = self.user_model.db.execute_query(query, fetch_one=True)
            return result['total'] if result else 0
        except Exception as e:
            print(f"Error al obtener usuarios activos: {e}")
            return self.get_total_usuarios()  # Fallback al total

    def get_promedio_ingresos(self):
        """Obtener promedio de ingresos por usuario"""
        try:
            total_usuarios = self.get_total_usuarios()
            if total_usuarios == 0:
                return 0
            ingresos_totales = self.get_ingresos_totales()
            return ingresos_totales / total_usuarios
        except Exception as e:
            print(f"Error al obtener promedio ingresos: {e}")
            return 0

    def get_promedio_gastos(self):
        """Obtener promedio de gastos por usuario"""
        try:
            total_usuarios = self.get_total_usuarios()
            if total_usuarios == 0:
                return 0
            gastos_totales = self.get_gastos_totales()
            return gastos_totales / total_usuarios
        except Exception as e:
            print(f"Error al obtener promedio gastos: {e}")
            return 0

    def get_ingresos_totales(self):
        """Obtener total de ingresos de todos los usuarios"""
        try:
            query = """
                SELECT COALESCE(SUM(monto), 0) as total 
                FROM ingresos
            """
            result = self.user_model.db.execute_query(query, fetch_one=True)
            return float(result['total']) if result and result['total'] else 0.0
        except Exception as e:
            print(f"Error al obtener ingresos totales: {e}")
            return 0.0

    def get_gastos_totales(self):
        """Obtener total de gastos de todos los usuarios"""
        try:
            query = """
                SELECT COALESCE(SUM(monto), 0) as total 
                FROM gastos
            """
            result = self.user_model.db.execute_query(query, fetch_one=True)
            return float(result['total']) if result and result['total'] else 0.0
        except Exception as e:
            print(f"Error al obtener gastos totales: {e}")
            return 0.0

    def get_ingresos_ultimo_mes(self):
        """Obtener ingresos del último mes"""
        try:
            query = """
                SELECT COALESCE(SUM(monto), 0) as total 
                FROM ingresos 
                WHERE fecha >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            """
            result = self.user_model.db.execute_query(query, fetch_one=True)
            return float(result['total']) if result and result['total'] else 0.0
        except Exception as e:
            print(f"Error al obtener ingresos último mes: {e}")
            return 0.0

    def get_gastos_ultimo_mes(self):
        """Obtener gastos del último mes"""
        try:
            query = """
                SELECT COALESCE(SUM(monto), 0) as total 
                FROM gastos 
                WHERE fecha >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            """
            result = self.user_model.db.execute_query(query, fetch_one=True)
            return float(result['total']) if result and result['total'] else 0.0
        except Exception as e:
            print(f"Error al obtener gastos último mes: {e}")
            return 0.0

    def get_variacion_ingresos(self):
        """Obtener variación de ingresos vs mes anterior"""
        try:
            # Ingresos mes actual
            ingresos_mes_actual = self.get_ingresos_ultimo_mes()
            
            # Ingresos mes anterior
            query = """
                SELECT COALESCE(SUM(monto), 0) as total 
                FROM ingresos 
                WHERE fecha BETWEEN DATE_SUB(NOW(), INTERVAL 60 DAY) AND DATE_SUB(NOW(), INTERVAL 30 DAY)
            """
            result = self.user_model.db.execute_query(query, fetch_one=True)
            ingresos_mes_anterior = float(result['total']) if result and result['total'] else 0.0
            
            if ingresos_mes_anterior == 0:
                return 0
                
            variacion = ((ingresos_mes_actual - ingresos_mes_anterior) / ingresos_mes_anterior) * 100
            return round(variacion, 1)
        except Exception as e:
            print(f"Error al obtener variación ingresos: {e}")
            return 0

    def get_variacion_gastos(self):
        """Obtener variación de gastos vs mes anterior"""
        try:
            # Gastos mes actual
            gastos_mes_actual = self.get_gastos_ultimo_mes()
            
            # Gastos mes anterior
            query = """
                SELECT COALESCE(SUM(monto), 0) as total 
                FROM gastos 
                WHERE fecha BETWEEN DATE_SUB(NOW(), INTERVAL 60 DAY) AND DATE_SUB(NOW(), INTERVAL 30 DAY)
            """
            result = self.user_model.db.execute_query(query, fetch_one=True)
            gastos_mes_anterior = float(result['total']) if result and result['total'] else 0.0
            
            if gastos_mes_anterior == 0:
                return 0
                
            variacion = ((gastos_mes_actual - gastos_mes_anterior) / gastos_mes_anterior) * 100
            return round(variacion, 1)
        except Exception as e:
            print(f"Error al obtener variación gastos: {e}")
            return 0

    def get_top_categorias_ingresos(self):
        """Obtener top categorías de ingresos"""
        try:
            query = """
                SELECT c.nombre, COUNT(*) as cantidad, SUM(i.monto) as total
                FROM ingresos i
                JOIN categorias_ingresos c ON i.categoria_id = c.id
                GROUP BY c.id, c.nombre
                ORDER BY total DESC
                LIMIT 5
            """
            result = self.user_model.db.execute_query(query, fetch=True)
            return result if result else []
        except Exception as e:
            print(f"Error al obtener top categorías ingresos: {e}")
            return []

    def get_top_categorias_gastos(self):
        """Obtener top categorías de gastos"""
        try:
            query = """
                SELECT c.nombre, COUNT(*) as cantidad, SUM(g.monto) as total
                FROM gastos g
                JOIN categorias_gastos c ON g.categoria_id = c.id
                GROUP BY c.id, c.nombre
                ORDER BY total DESC
                LIMIT 5
            """
            result = self.user_model.db.execute_query(query, fetch=True)
            return result if result else []
        except Exception as e:
            print(f"Error al obtener top categorías gastos: {e}")
            return []

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