from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from models.savings import SavingsModel
from utils.helpers import decimal_to_float
from datetime import datetime

class SavingsController:
    def __init__(self):
        self.bp = Blueprint('savings', __name__)
        self.savings_model = SavingsModel()
        self.register_routes()

    def register_routes(self):
        self.bp.route('/savings')(self.index)
        self.bp.route('/savings/add', methods=['POST'])(self.add)
        self.bp.route('/savings/add-money/<int:savings_id>', methods=['POST'])(self.add_money)
        self.bp.route('/savings/update/<int:savings_id>', methods=['POST'])(self.update)
        self.bp.route('/savings/delete/<int:savings_id>', methods=['POST'])(self.delete)
        self.bp.route('/api/savings')(self.api_savings)

    def index(self):
        """Página de listado de ahorros"""
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        
        user_id = session['user_id']
        savings = self.savings_model.get_by_user(user_id)
        summary = self.savings_model.get_savings_summary(user_id)
        
        return render_template('savings/index.html',
                             savings=savings,
                             summary=summary)

    def add(self):
        """Agregar nueva meta de ahorro"""
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        
        if request.method == 'POST':
            concepto = request.form.get('concepto')
            meta_total = request.form.get('meta_total')
            fecha_objetivo = request.form.get('fecha_objetivo')
            descripcion = request.form.get('descripcion')
            
            if not all([concepto, meta_total]):
                flash('Por favor completa todos los campos obligatorios', 'error')
                return redirect(url_for('savings.index'))
            
            try:
                user_id = session['user_id']
                savings_id = self.savings_model.create(
                    user_id, concepto, float(meta_total), fecha_objetivo, descripcion
                )
                flash('¡Meta de ahorro creada exitosamente!', 'success')
            except Exception as e:
                flash('Error al crear la meta de ahorro: ' + str(e), 'error')
        
        return redirect(url_for('savings.index'))

    def add_money(self, savings_id):
        """Agregar dinero a una meta de ahorro"""
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'No autorizado'}), 401
        
        if request.method == 'POST':
            monto = request.form.get('monto')
            
            if not monto or float(monto) <= 0:
                return jsonify({'success': False, 'error': 'Monto inválido'}), 400
            
            try:
                user_id = session['user_id']
                self.savings_model.add_savings(savings_id, user_id, float(monto))
                flash('¡Dinero agregado exitosamente!', 'success')
                return jsonify({'success': True})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500

    def update(self, savings_id):
        """Actualizar meta de ahorro"""
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'No autorizado'}), 401
        
        if request.method == 'POST':
            concepto = request.form.get('concepto')
            meta_total = request.form.get('meta_total')
            fecha_objetivo = request.form.get('fecha_objetivo')
            descripcion = request.form.get('descripcion')
            
            if not all([concepto, meta_total]):
                return jsonify({'success': False, 'error': 'Campos obligatorios faltantes'}), 400
            
            try:
                user_id = session['user_id']
                self.savings_model.update(savings_id, user_id, concepto, float(meta_total), fecha_objetivo, descripcion)
                flash('¡Meta de ahorro actualizada exitosamente!', 'success')
                return jsonify({'success': True})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500

    def delete(self, savings_id):
        """Eliminar meta de ahorro"""
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'No autorizado'}), 401
        
        try:
            user_id = session['user_id']
            self.savings_model.delete(savings_id, user_id)
            flash('Meta de ahorro eliminada exitosamente', 'success')
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    def api_savings(self):
        """API para obtener ahorros (AJAX)"""
        if 'user_id' not in session:
            return jsonify({'error': 'No autorizado'}), 401
        
        user_id = session['user_id']
        savings = self.savings_model.get_by_user(user_id)
        
        # Convertir decimales a float
        for saving in savings:
            saving['meta_total'] = decimal_to_float(saving['meta_total'])
            saving['ahorrado_actual'] = decimal_to_float(saving['ahorrado_actual'])
            saving['porcentaje_completado'] = decimal_to_float(saving['porcentaje_completado'])
            if saving['fecha_inicio']:
                saving['fecha_inicio'] = saving['fecha_inicio'].strftime('%Y-%m-%d')
            if saving['fecha_objetivo']:
                saving['fecha_objetivo'] = saving['fecha_objetivo'].strftime('%Y-%m-%d')
        
        return jsonify(savings)

# Crear instancia del controlador
savings_controller = SavingsController()