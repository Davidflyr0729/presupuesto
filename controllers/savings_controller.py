from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from models.savings import SavingsModel
from utils.helpers import decimal_to_float
from datetime import datetime

class SavingsController:
    def __init__(self):
        self.bp = Blueprint('savings', '__name__', url_prefix='/savings')  # ← CORREGIDO: agregado url_prefix
        self.savings_model = SavingsModel()
        self.register_routes()

    def register_routes(self):
        self.bp.route('/')(self.index)  # ← CORREGIDO: cambiado de '/savings' a '/'
        self.bp.route('/add', methods=['POST'])(self.add)  # ← CORREGIDO: cambiado de '/savings/add' a '/add'
        self.bp.route('/add-money/<int:savings_id>', methods=['POST'])(self.add_money)
        self.bp.route('/update/<int:savings_id>', methods=['POST'])(self.update)
        self.bp.route('/delete/<int:savings_id>', methods=['POST'])(self.delete)
        self.bp.route('/api')(self.api_savings)  # ← CORREGIDO: cambiado de '/api/savings' a '/api'

    def index(self):
        """Página de listado de ahorros"""
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        
        user_id = session['user_id']
        savings = self.savings_model.get_by_user(user_id)
        summary = self.savings_model.get_savings_summary(user_id)
        
        return render_template('savings/index.html',
                             savings=savings,
                             summary=summary,
                             now=datetime.now())  # ← AGREGADO: para usar en el template

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
                # ✅ VALIDACIÓN: Limpiar formato del monto
                meta_total_limpio = meta_total.replace('.', '')  # Remover puntos de separadores de miles
                meta_total_float = float(meta_total_limpio)
                
                if meta_total_float <= 0:
                    flash('La meta total debe ser mayor a 0', 'error')
                    return redirect(url_for('savings.index'))
                
                savings_id = self.savings_model.create(
                    user_id, concepto, meta_total_float, fecha_objetivo, descripcion
                )
                flash('¡Meta de ahorro creada exitosamente!', 'success')
            except ValueError:
                flash('La meta total ingresada no es válida', 'error')
                return redirect(url_for('savings.index'))
            except Exception as e:
                flash('Error al crear la meta de ahorro: ' + str(e), 'error')
        
        return redirect(url_for('savings.index'))

    def add_money(self, savings_id):
        """Agregar dinero a una meta de ahorro"""
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'No autorizado'}), 401
        
        if request.method == 'POST':
            monto = request.form.get('monto')
            
            if not monto:
                return jsonify({'success': False, 'error': 'Monto requerido'}), 400
            
            try:
                user_id = session['user_id']
                
                # ✅ VALIDACIÓN: Limpiar formato del monto
                monto_limpio = monto.replace('.', '')  # Remover puntos de separadores de miles
                monto_float = float(monto_limpio)
                
                if monto_float <= 0:
                    return jsonify({'success': False, 'error': 'El monto debe ser mayor a 0'}), 400
                
                # ✅ NUEVA VALIDACIÓN: Verificar que no se supere la meta total
                # Obtener información de la meta de ahorro
                saving = self.savings_model.get_by_id(savings_id, user_id)
                if not saving:
                    return jsonify({'success': False, 'error': 'Meta de ahorro no encontrada'}), 404
                
                meta_total = float(saving['meta_total'])
                ahorrado_actual = float(saving['ahorrado_actual'])
                saldo_restante = meta_total - ahorrado_actual
                
                # Verificar si el monto a agregar supera la meta
                if monto_float > saldo_restante:
                    return jsonify({
                        'success': False, 
                        'error': f'No puedes ahorrar más de tu meta. Te faltan ${saldo_restante:,.0f} para completar los ${meta_total:,.0f}'
                    }), 400
                
                # Si pasa la validación, agregar el dinero
                self.savings_model.add_savings(savings_id, user_id, monto_float)
                flash('¡Dinero agregado exitosamente!', 'success')
                return jsonify({'success': True})
                
            except ValueError:
                return jsonify({'success': False, 'error': 'Monto inválido'}), 400
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
                # ✅ VALIDACIÓN: Limpiar formato del monto
                meta_total_limpio = meta_total.replace('.', '')  # Remover puntos de separadores de miles
                meta_total_float = float(meta_total_limpio)
                
                if meta_total_float <= 0:
                    return jsonify({'success': False, 'error': 'La meta total debe ser mayor a 0'}), 400
                
                # ✅ VALIDACIÓN: Verificar que la nueva meta no sea menor que lo ya ahorrado
                saving = self.savings_model.get_by_id(savings_id, user_id)
                if saving:
                    ahorrado_actual = float(saving['ahorrado_actual'])
                    if meta_total_float < ahorrado_actual:
                        return jsonify({
                            'success': False, 
                            'error': f'La nueva meta no puede ser menor a lo ya ahorrado (${ahorrado_actual:,.0f})'
                        }), 400
                
                self.savings_model.update(savings_id, user_id, concepto, meta_total_float, fecha_objetivo, descripcion)
                flash('¡Meta de ahorro actualizada exitosamente!', 'success')
                return jsonify({'success': True})
                
            except ValueError:
                return jsonify({'success': False, 'error': 'Meta total inválida'}), 400
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