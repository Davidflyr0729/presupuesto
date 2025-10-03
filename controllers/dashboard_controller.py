from flask import Blueprint, render_template, session, redirect, url_for
import mysql.connector
from datetime import datetime
from config import Config

class DashboardController:
    def __init__(self):
        self.bp = Blueprint('dashboard', __name__)
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
    
    def index(self):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        
        user_id = session['user_id']
        
        try:
            conn = self.get_db_connection()
            if not conn:
                return render_template('dashboard/index.html',
                                    total_ingresos=0, total_gastos=0, saldo=0,
                                    ingresos_mes=0, gastos_mes=0,
                                    ultimos_ingresos=[], ultimos_gastos=[],
                                    total_ahorros=0, meta_ahorros=0, metas_activas=[])
            
            cursor = conn.cursor(dictionary=True)
            
            # 1. Total ingresos
            cursor.execute("SELECT SUM(monto) as total FROM ingresos WHERE usuario_id = %s", (user_id,))
            total_ingresos_result = cursor.fetchone()
            total_ingresos = total_ingresos_result['total'] if total_ingresos_result['total'] else 0
            
            # 2. Total gastos
            cursor.execute("SELECT SUM(monto) as total FROM gastos WHERE usuario_id = %s", (user_id,))
            total_gastos_result = cursor.fetchone()
            total_gastos = total_gastos_result['total'] if total_gastos_result['total'] else 0
            
            # 3. Calcular saldo
            saldo = total_ingresos - total_gastos
            
            # 4. Ingresos del mes actual
            current_month = datetime.now().strftime('%Y-%m')
            cursor.execute("""
                SELECT SUM(monto) as total 
                FROM ingresos 
                WHERE usuario_id = %s AND DATE_FORMAT(fecha, '%%Y-%%m') = %s
            """, (user_id, current_month))
            ingresos_mes_result = cursor.fetchone()
            ingresos_mes = ingresos_mes_result['total'] if ingresos_mes_result['total'] else 0
            
            # 5. Gastos del mes actual
            cursor.execute("""
                SELECT SUM(monto) as total 
                FROM gastos 
                WHERE usuario_id = %s AND DATE_FORMAT(fecha, '%%Y-%%m') = %s
            """, (user_id, current_month))
            gastos_mes_result = cursor.fetchone()
            gastos_mes = gastos_mes_result['total'] if gastos_mes_result['total'] else 0
            
            # 6. Obtener datos de ahorros - CONSULTA CORREGIDA
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(ahorrado_actual), 0) as total_ahorrado,
                    COALESCE(SUM(meta_total), 0) as meta_total,
                    COUNT(*) as total_metas
                FROM ahorros 
                WHERE usuario_id = %s AND completado = 0
            """, (user_id,))
            ahorros_result = cursor.fetchone()
            total_ahorros = float(ahorros_result['total_ahorrado']) if ahorros_result and ahorros_result['total_ahorrado'] else 0
            meta_ahorros = float(ahorros_result['meta_total']) if ahorros_result and ahorros_result['meta_total'] else 0
            
            # 7. Obtener metas activas para mostrar (solo las no completadas)
            cursor.execute("""
                SELECT 
                    id,
                    concepto, 
                    meta_total, 
                    ahorrado_actual, 
                    ROUND((ahorrado_actual / meta_total) * 100, 0) as porcentaje_completado,
                    fecha_objetivo,
                    descripcion
                FROM ahorros 
                WHERE usuario_id = %s AND completado = 0
                ORDER BY fecha_objetivo ASC
                LIMIT 3
            """, (user_id,))
            metas_activas = cursor.fetchall()
            
            # Convertir decimales a float para las metas activas
            for meta in metas_activas:
                meta['meta_total'] = float(meta['meta_total'])
                meta['ahorrado_actual'] = float(meta['ahorrado_actual'])
                meta['porcentaje_completado'] = float(meta['porcentaje_completado'])
            
            # 8. Últimos 5 ingresos
            cursor.execute("""
                SELECT i.*, ci.nombre as categoria_nombre, ci.color, ci.icono
                FROM ingresos i 
                LEFT JOIN categorias_ingresos ci ON i.categoria_id = ci.id 
                WHERE i.usuario_id = %s
                ORDER BY i.fecha DESC, i.id DESC LIMIT 5
            """, (user_id,))
            ultimos_ingresos = cursor.fetchall()
            
            # 9. Últimos 5 gastos
            cursor.execute("""
                SELECT g.*, cg.nombre as categoria_nombre, cg.color, cg.icono
                FROM gastos g 
                LEFT JOIN categorias_gastos cg ON g.categoria_id = cg.id 
                WHERE g.usuario_id = %s
                ORDER BY g.fecha DESC, g.id DESC LIMIT 5
            """, (user_id,))
            ultimos_gastos = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            # Debug: Verificar datos de ahorros
            print(f"=== DATOS DE AHORROS ===")
            print(f"Total ahorrado: {total_ahorros}")
            print(f"Meta total: {meta_ahorros}")
            print(f"Metas activas encontradas: {len(metas_activas)}")
            for i, meta in enumerate(metas_activas):
                print(f"Meta {i+1}: {meta['concepto']} - {meta['porcentaje_completado']}%")
            
            return render_template('dashboard/index.html',
                                total_ingresos=total_ingresos,
                                total_gastos=total_gastos,
                                saldo=saldo,
                                ingresos_mes=ingresos_mes,
                                gastos_mes=gastos_mes,
                                ultimos_ingresos=ultimos_ingresos,
                                ultimos_gastos=ultimos_gastos,
                                # NUEVAS VARIABLES PARA AHORROS
                                total_ahorros=total_ahorros,
                                meta_ahorros=meta_ahorros,
                                metas_activas=metas_activas)
                                
        except Exception as e:
            print(f"Error en dashboard: {e}")
            import traceback
            traceback.print_exc()
            return render_template('dashboard/index.html',
                                total_ingresos=0, total_gastos=0, saldo=0,
                                ingresos_mes=0, gastos_mes=0,
                                ultimos_ingresos=[], ultimos_gastos=[],
                                total_ahorros=0, meta_ahorros=0, metas_activas=[])

dashboard_controller = DashboardController()