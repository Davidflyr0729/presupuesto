from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from models.budget import BudgetModel
from models.expense import ExpenseModel
from utils.helpers import decimal_to_float
from datetime import datetime

class BudgetController:
    def __init__(self):
        self.bp = Blueprint('budgets', __name__, url_prefix='/budgets')
        self.budget_model = BudgetModel()
        self.expense_model = ExpenseModel()
        self.register_routes()

    def register_routes(self):
        self.bp.route('/')(self.index)
        self.bp.route('/add', methods=['POST'])(self.add)
        self.bp.route('/update/<int:budget_id>', methods=['POST'])(self.update)
        self.bp.route('/delete/<int:budget_id>', methods=['POST'])(self.delete)
        self.bp.route('/api')(self.api_budgets)
        self.bp.route('/api/progress')(self.api_budget_progress)

    def index(self):
        """Página de listado de presupuestos"""
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        
        user_id = session['user_id']
        month = request.args.get('month', datetime.now().month, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        
        budgets = self.budget_model.get_by_user(user_id, month, year)
        
        # Obtener TODAS las categorías de gastos
        all_categories = self.expense_model.get_categories()
        
        # Obtener el resumen general
        summary = self.budget_model.get_budget_summary(user_id, month, year)
        
        return render_template('budgets/index.html',
                             budgets=budgets,
                             categories=all_categories,  # ← CAMBIO: Ahora pasamos TODAS las categorías
                             expense_categories=all_categories,
                             summary=summary,
                             current_month=month,
                             current_year=year,
                             now=datetime.now())

    def add(self):
        """Agregar nuevo presupuesto"""
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        
        if request.method == 'POST':
            categoria_gasto_id = request.form.get('categoria_gasto_id')
            monto_maximo = request.form.get('monto_maximo')
            mes_year = request.form.get('mes_year')
            
            if not all([categoria_gasto_id, monto_maximo, mes_year]):
                flash('Por favor completa todos los campos obligatorios', 'error')
                return redirect(url_for('budgets.index'))
            
            try:
                user_id = session['user_id']
                # Limpiar formato del monto (remover puntos de separadores de miles)
                monto_maximo_limpio = monto_maximo.replace('.', '')
                budget_id = self.budget_model.create(
                    user_id, int(categoria_gasto_id), float(monto_maximo_limpio), mes_year
                )
                flash('¡Presupuesto agregado exitosamente!', 'success')
            except Exception as e:
                flash('Error al agregar presupuesto: ' + str(e), 'error')
        
        return redirect(url_for('budgets.index'))

    def update(self, budget_id):
        """Actualizar presupuesto"""
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'No autorizado'}), 401
        
        if request.method == 'POST':
            monto_maximo = request.form.get('monto_maximo')
            
            if not monto_maximo:
                return jsonify({'success': False, 'error': 'Monto requerido'}), 400
            
            try:
                user_id = session['user_id']
                # Limpiar formato del monto (remover puntos de separadores de miles)
                monto_maximo_limpio = monto_maximo.replace('.', '')
                self.budget_model.update(budget_id, user_id, float(monto_maximo_limpio))
                flash('¡Presupuesto actualizado exitosamente!', 'success')
                return jsonify({'success': True})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500

    def delete(self, budget_id):
        """Eliminar presupuesto"""
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'No autorizado'}), 401
        
        try:
            user_id = session['user_id']
            self.budget_model.delete(budget_id, user_id)
            flash('Presupuesto eliminado exitosamente', 'success')
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    def api_budgets(self):
        """API para obtener presupuestos (AJAX)"""
        if 'user_id' not in session:
            return jsonify({'error': 'No autorizado'}), 401
        
        user_id = session['user_id']
        month = request.args.get('month', datetime.now().month, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        
        budgets = self.budget_model.get_by_user(user_id, month, year)
        
        # Convertir decimales a float
        for budget in budgets:
            budget['monto_maximo'] = decimal_to_float(budget['monto_maximo'])
            budget['gasto_actual'] = decimal_to_float(budget['gasto_actual'])
            budget['saldo_restante'] = decimal_to_float(budget['saldo_restante'])
            budget['porcentaje_uso'] = decimal_to_float(budget['porcentaje_uso'])
        
        return jsonify(budgets)

    def api_budget_progress(self):
        """API para obtener progreso de presupuestos (AJAX)"""
        if 'user_id' not in session:
            return jsonify({'error': 'No autorizado'}), 401
        
        user_id = session['user_id']
        month = request.args.get('month', datetime.now().month, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        
        budgets = self.budget_model.get_by_user(user_id, month, year)
        
        # Preparar datos para gráfico
        progress_data = []
        for budget in budgets:
            progress_data.append({
                'categoria': budget['categoria_nombre'],
                'presupuesto': decimal_to_float(budget['monto_maximo']),
                'gastado': decimal_to_float(budget['gasto_actual']),
                'porcentaje': decimal_to_float(budget['porcentaje_uso']),
                'color': budget['color']
            })
        
        return jsonify(progress_data)

# Crear instancia del controlador
budget_controller = BudgetController()