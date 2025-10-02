from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from models.expense import ExpenseModel
from utils.helpers import decimal_to_float
from datetime import datetime

class ExpenseController:
    def __init__(self):
        self.bp = Blueprint('expenses', __name__)
        self.expense_model = ExpenseModel()
        self.register_routes()

    def register_routes(self):
        self.bp.route('/expenses')(self.index)
        self.bp.route('/expenses/add', methods=['POST'])(self.add)
        self.bp.route('/expenses/delete/<int:expense_id>', methods=['POST'])(self.delete)
        self.bp.route('/api/expenses')(self.api_expenses)

    def index(self):
        """Página de listado de gastos"""
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        
        user_id = session['user_id']
        month = request.args.get('month', datetime.now().month, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        
        expenses = self.expense_model.get_by_user(user_id, month, year)
        categories = self.expense_model.get_categories()
        total = self.expense_model.get_total(user_id, month, year)
        
        return render_template('transactions/expenses.html',
                             expenses=expenses,
                             categories=categories,
                             total=total,
                             current_month=month,
                             current_year=year)

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