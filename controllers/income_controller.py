from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from models.income import IncomeModel
from utils.helpers import decimal_to_float
from datetime import datetime

class IncomeController:
    def __init__(self):
        self.bp = Blueprint('incomes', __name__)
        self.income_model = IncomeModel()
        self.register_routes()

    def register_routes(self):
        self.bp.route('/incomes')(self.index)
        self.bp.route('/incomes/add', methods=['POST'])(self.add)
        self.bp.route('/incomes/delete/<int:income_id>', methods=['POST'])(self.delete)
        self.bp.route('/api/incomes')(self.api_incomes)

    def index(self):
        """Página de listado de ingresos"""
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        
        user_id = session['user_id']
        month = request.args.get('month', datetime.now().month, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        
        incomes = self.income_model.get_by_user(user_id, month, year)
        categories = self.income_model.get_categories()
        total = self.income_model.get_total(user_id, month, year)
        
        return render_template('transactions/incomes.html',
                             incomes=incomes,
                             categories=categories,
                             total=total,
                             current_month=month,
                             current_year=year)

    def add(self):
        """Agregar nuevo ingreso"""
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        
        if request.method == 'POST':
            concepto = request.form.get('concepto')
            monto = request.form.get('monto')
            categoria_id = request.form.get('categoria_id')
            fecha = request.form.get('fecha')
            descripcion = request.form.get('descripcion')
            
            if not all([concepto, monto, categoria_id, fecha]):
                flash('Por favor completa todos los campos obligatorios', 'error')
                return redirect(url_for('incomes.index'))
            
            try:
                user_id = session['user_id']
                income_id = self.income_model.create(
                    user_id, concepto, float(monto), 
                    int(categoria_id), fecha, descripcion
                )
                flash('¡Ingreso agregado exitosamente!', 'success')
            except Exception as e:
                flash('Error al agregar ingreso: ' + str(e), 'error')
        
        return redirect(url_for('incomes.index'))

    def delete(self, income_id):
        """Eliminar ingreso"""
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'No autorizado'}), 401
        
        # TODO: Verificar que el ingreso pertenezca al usuario
        try:
            # Aquí deberías agregar verificación de propiedad
            delete_query = "DELETE FROM ingresos WHERE id = %s"
            self.income_model.db.execute_query(delete_query, (income_id,))
            flash('Ingreso eliminado exitosamente', 'success')
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    def api_incomes(self):
        """API para obtener ingresos (AJAX)"""
        if 'user_id' not in session:
            return jsonify({'error': 'No autorizado'}), 401
        
        user_id = session['user_id']
        month = request.args.get('month', datetime.now().month, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        
        incomes = self.income_model.get_by_user(user_id, month, year)
        
        # Convertir decimales a float
        for income in incomes:
            income['monto'] = decimal_to_float(income['monto'])
            if income['fecha']:
                income['fecha'] = income['fecha'].strftime('%Y-%m-%d')
        
        return jsonify(incomes)

# Crear instancia del controlador
income_controller = IncomeController()