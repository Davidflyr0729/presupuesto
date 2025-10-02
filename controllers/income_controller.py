from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
import mysql.connector
from datetime import datetime
from config import Config

class IncomeController:
    def __init__(self):
        self.bp = Blueprint('income', __name__, url_prefix='/income')
        self.register_routes()
    
    def get_db_connection(self):
        """Crear conexión a la base de datos"""
        try:
            conn = mysql.connector.connect(
                host=Config.MYSQL_HOST,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DB,
                port=Config.MYSQL_PORT
            )
            return conn
        except Exception as e:
            print(f"Error conectando a la BD: {e}")
            return None
    
    def register_routes(self):
        self.bp.route('/')(self.index)
        self.bp.route('/add', methods=['POST'])(self.add_income)
        self.bp.route('/delete/<int:income_id>', methods=['POST'])(self.delete_income)
    
    def index(self):
        """Página principal de ingresos"""
        if 'user_id' not in session:
            flash('Por favor inicia sesión', 'error')
            return redirect(url_for('auth.login'))
        
        try:
            user_id = session['user_id']
            conn = self.get_db_connection()
            if not conn:
                flash('Error de conexión a la base de datos', 'error')
                return render_template('incomes/index.html', incomes=[], categories=[])
            
            cursor = conn.cursor(dictionary=True)
            
            # Obtener ingresos del usuario
            cursor.execute("""
                SELECT i.*, ci.nombre as categoria_nombre, ci.color, ci.icono
                FROM ingresos i 
                LEFT JOIN categorias_ingresos ci ON i.categoria_id = ci.id 
                WHERE i.usuario_id = %s
                ORDER BY i.fecha DESC
            """, (user_id,))
            incomes = cursor.fetchall()
            
            # Obtener categorías
            cursor.execute("SELECT * FROM categorias_ingresos")
            categories = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return render_template('incomes/index.html', 
                                 incomes=incomes, 
                                 categories=categories,
                                 active_page='income')
            
        except Exception as e:
            print(f"Error en incomes: {e}")
            flash('Error al cargar los ingresos', 'error')
            return render_template('incomes/index.html', incomes=[], categories=[])
    
    def add_income(self):
        """Agregar nuevo ingreso"""
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'No autorizado'})
        
        try:
            user_id = session['user_id']
            concepto = request.form.get('concepto')
            monto = request.form.get('monto')
            categoria_id = request.form.get('categoria_id')
            fecha = request.form.get('fecha')
            descripcion = request.form.get('descripcion', '')
            
            # Validaciones
            if not concepto or not monto or not categoria_id:
                return jsonify({'success': False, 'error': 'Todos los campos son requeridos'})
            
            try:
                monto = float(monto)
                if monto <= 0:
                    return jsonify({'success': False, 'error': 'El monto debe ser mayor a 0'})
            except ValueError:
                return jsonify({'success': False, 'error': 'Monto inválido'})
            
            # Usar fecha actual si no se proporciona
            if not fecha:
                fecha = datetime.now().strftime('%Y-%m-%d')
            
            conn = self.get_db_connection()
            if not conn:
                return jsonify({'success': False, 'error': 'Error de conexión'})
            
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO ingresos (usuario_id, concepto, monto, categoria_id, fecha, descripcion)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, concepto, monto, categoria_id, fecha, descripcion))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Ingreso agregado correctamente'})
            
        except Exception as e:
            print(f"Error al agregar ingreso: {e}")
            return jsonify({'success': False, 'error': 'Error al agregar el ingreso'})
    
    def delete_income(self, income_id):
        """Eliminar ingreso"""
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'No autorizado'})
        
        try:
            user_id = session['user_id']
            conn = self.get_db_connection()
            if not conn:
                return jsonify({'success': False, 'error': 'Error de conexión'})
            
            cursor = conn.cursor()
            
            # Verificar que el ingreso pertenece al usuario
            cursor.execute("SELECT id FROM ingresos WHERE id = %s AND usuario_id = %s", 
                         (income_id, user_id))
            
            if not cursor.fetchone():
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'error': 'Ingreso no encontrado'})
            
            cursor.execute("DELETE FROM ingresos WHERE id = %s AND usuario_id = %s", 
                         (income_id, user_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Ingreso eliminado correctamente'})
            
        except Exception as e:
            print(f"Error al eliminar ingreso: {e}")
            return jsonify({'success': False, 'error': 'Error al eliminar el ingreso'})

# Crear instancia
income_controller = IncomeController()