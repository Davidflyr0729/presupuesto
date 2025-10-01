from flask import Blueprint, render_template, request, request, session, redirect, url_for, jsonify
from models.dashboard import DashboardModel
from models.income import IncomeModel
from models.expense import ExpenseModel
from utils.helpers import decimal_to_float
from datetime import datetime

class DashboardController:
    def __init__(self):
        self.bp = Blueprint('dashboard', __name__)
        self.dashboard_model = DashboardModel()
        self.income_model = IncomeModel()
        self.expense_model = ExpenseModel()
        self.register_routes()

    def register_routes(self):
        self.bp.route('/')(self.index)
        self.bp.route('/api/summary')(self.api_summary)
        self.bp.route('/api/expenses-by-category')(self.api_expenses_by_category)

    def index(self):
        """Página principal del dashboard"""
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        
        user_id = session['user_id']
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Obtener datos para el dashboard
        summary = self.dashboard_model.get_monthly_summary(user_id, current_month, current_year)
        expenses_by_category = self.dashboard_model.get_expenses_by_category(user_id, current_month, current_year)
        recent_transactions = self.dashboard_model.get_recent_transactions(user_id, 5)
        
        # Obtener últimos ingresos y gastos
        recent_incomes = self.income_model.get_by_user(user_id, current_month, current_year)[:3]
        recent_expenses = self.expense_model.get_by_user(user_id, current_month, current_year)[:3]
        
        return render_template('dashboard/index.html',
                             summary=summary,
                             expenses_by_category=expenses_by_category,
                             recent_transactions=recent_transactions,
                             recent_incomes=recent_incomes,
                             recent_expenses=recent_expenses)

    def api_summary(self):
        """API para obtener resumen mensual (AJAX)"""
        if 'user_id' not in session:
            return jsonify({'error': 'No autorizado'}), 401
        
        user_id = session['user_id']
        month = request.args.get('month', datetime.now().month, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        
        summary = self.dashboard_model.get_monthly_summary(user_id, month, year)
        
        # Convertir decimales a float para JSON
        for key, value in summary.items():
            summary[key] = decimal_to_float(value)
        
        return jsonify(summary)

    def api_expenses_by_category(self):
        """API para obtener gastos por categoría (AJAX)"""
        if 'user_id' not in session:
            return jsonify({'error': 'No autorizado'}), 401
        
        user_id = session['user_id']
        month = request.args.get('month', datetime.now().month, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        
        expenses = self.dashboard_model.get_expenses_by_category(user_id, month, year)
        
        # Convertir decimales a float
        for expense in expenses:
            expense['total'] = decimal_to_float(expense['total'])
        
        return jsonify(expenses)

# Crear instancia del controlador
dashboard_controller = DashboardController()