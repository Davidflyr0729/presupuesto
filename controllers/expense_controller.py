from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from models.expense import ExpenseModel
from utils.helpers import decimal_to_float
from datetime import datetime

class ExpenseController:
    def __init__(self):
        self.bp = Blueprint('expenses', __name__, url_prefix='/expenses')
        self.expense_model = ExpenseModel()
        self.register_routes()

    def register_routes(self):
        self.bp.route('/')(self.index)
        self.bp.route('/add', methods=['POST'])(self.add)
        self.bp.route('/delete/<int:expense_id>', methods=['POST'])(self.delete)
        self.bp.route('/api')(self.api_expenses)

    def index(self):
        """Página de listado de gastos"""
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        
        user_id = session['user_id']
        
        # Obtener mes seleccionado (por defecto mes actual)
        mes_seleccionado = request.args.get('mes', datetime.now().strftime('%Y-%m'))
        
        try:
            año, mes = mes_seleccionado.split('-')
            año = int(año)
            mes = int(mes)
        except (ValueError, AttributeError):
            # Si hay error en el formato, usar mes actual
            ahora = datetime.now()
            mes_seleccionado = ahora.strftime('%Y-%m')
            año = ahora.year
            mes = ahora.month
        
        # Obtener datos del mes seleccionado
        expenses = self.expense_model.get_by_user(user_id, mes, año)
        categories = self.expense_model.get_categories()
        total_mes = self.expense_model.get_total(user_id, mes, año)
        
        # Obtener total general de todos los gastos (sin filtro de mes)
        total_general = self.expense_model.get_total(user_id)
        total_registros = len(expenses)
        
        # ✅ CALCULAR SALDO ACTUAL (INGRESOS TOTALES - GASTOS TOTALES) - NUEVO
        try:
            # Obtener total de ingresos
            ingresos_query = "SELECT COALESCE(SUM(monto), 0) as total_ingresos FROM ingresos WHERE usuario_id = %s"
            ingresos_result = self.expense_model.db.execute_query(ingresos_query, (user_id,), fetch_one=True)
            total_ingresos = float(ingresos_result['total_ingresos']) if ingresos_result and ingresos_result['total_ingresos'] else 0
            
            # Obtener total de gastos (usando el mismo método que en dashboard)
            gastos_query = "SELECT COALESCE(SUM(monto), 0) as total_gastos FROM gastos WHERE usuario_id = %s"
            gastos_result = self.expense_model.db.execute_query(gastos_query, (user_id,), fetch_one=True)
            total_gastos = float(gastos_result['total_gastos']) if gastos_result and gastos_result['total_gastos'] else 0
            
            # Calcular saldo actual
            saldo_actual = total_ingresos - total_gastos
            
            # Debug: imprimir valores para verificar
            print(f"DEBUG - User ID: {user_id}")
            print(f"DEBUG - Total Ingresos: {total_ingresos}")
            print(f"DEBUG - Total Gastos: {total_gastos}")
            print(f"DEBUG - Saldo Actual: {saldo_actual}")
            print(f"DEBUG - Total General (método anterior): {total_general}")
            
        except Exception as e:
            print(f"Error calculando saldo actual: {e}")
            saldo_actual = 0
    
        return render_template('transactions/expenses.html',
                             expenses=expenses,
                             categories=categories,
                             total_mes=total_mes,
                             total_general=total_general,
                             total_registros=total_registros,
                             saldo_actual=saldo_actual,  # ← NUEVO
                             mes_seleccionado=mes_seleccionado,
                             now=datetime.now())

    def add(self):
        """Agregar nuevo gasto"""
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        
        if request.method == 'POST':
            concepto = request.form.get('concepto')
            monto = request.form.get('monto')
            categoria_id = request.form.get('categoria_id')
            fecha = request.form.get('fecha')
            esencial = request.form.get('esencial', 'on') == 'on'
            descripcion = request.form.get('descripcion')
            
            if not all([concepto, monto, categoria_id, fecha]):
                flash('Por favor completa todos los campos obligatorios', 'error')
                return redirect(url_for('expenses.index'))
            
            try:
                user_id = session['user_id']
                expense_id = self.expense_model.create(
                    user_id, concepto, float(monto), 
                    int(categoria_id), fecha, esencial, descripcion
                )
                flash('¡Gasto agregado exitosamente!', 'success')
            except Exception as e:
                flash('Error al agregar gasto: ' + str(e), 'error')
        
        return redirect(url_for('expenses.index'))

    def delete(self, expense_id):
        """Eliminar gasto"""
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'No autorizado'}), 401
        
        try:
            # Verificar que el gasto pertenezca al usuario
            expense = self.expense_model.db.execute_query(
                "SELECT * FROM gastos WHERE id = %s AND usuario_id = %s",
                (expense_id, session['user_id']),
                fetch_one=True
            )
            
            if not expense:
                return jsonify({'success': False, 'error': 'Gasto no encontrado'}), 404
            
            delete_query = "DELETE FROM gastos WHERE id = %s"
            self.expense_model.db.execute_query(delete_query, (expense_id,))
            flash('Gasto eliminado exitosamente', 'success')
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    def api_expenses(self):
        """API para obtener gastos (AJAX)"""
        if 'user_id' not in session:
            return jsonify({'error': 'No autorizado'}), 401
        
        user_id = session['user_id']
        month = request.args.get('month', datetime.now().month, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        
        expenses = self.expense_model.get_by_user(user_id, month, year)
        
        # Convertir decimales a float
        for expense in expenses:
            expense['monto'] = decimal_to_float(expense['monto'])
            if expense['fecha']:
                expense['fecha'] = expense['fecha'].strftime('%Y-%m-%d')
        
        return jsonify(expenses)

# Crear instancia del controlador
expense_controller = ExpenseController()