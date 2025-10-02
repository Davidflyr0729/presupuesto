from flask import Blueprint, render_template, request, jsonify
from datetime import datetime
from presupuesto_app import db
from presupuesto_app.models.income import Income

class IncomeController:
    def __init__(self):
        self.bp = Blueprint('income', __name__, url_prefix='/income')
        self.register_routes()
    
    def register_routes(self):
        self.bp.route('/')(self.index)
        self.bp.route('/add', methods=['POST'])(self.add)
        self.bp.route('/update/<int:income_id>', methods=['POST'])(self.update)
        self.bp.route('/delete/<int:income_id>', methods=['POST'])(self.delete)
        self.bp.route('/get/<int:income_id>')(self.get_income)
    
    def index(self):
        try:
            # Obtener todos los ingresos ordenados por fecha (más recientes primero)
            incomes = Income.query.order_by(Income.fecha.desc()).all()
            
            # Calcular resumen
            total_ingresos = sum(income.monto for income in incomes)
            total_ingresos_mes = sum(income.monto for income in incomes 
                                    if income.fecha and income.fecha.month == datetime.now().month)
            total_recurrentes = sum(income.monto for income in incomes if income.recurrente)
            
            # Agrupar por categoría
            ingresos_por_categoria = {}
            for income in incomes:
                if income.categoria in ingresos_por_categoria:
                    ingresos_por_categoria[income.categoria] += income.monto
                else:
                    ingresos_por_categoria[income.categoria] = income.monto
            
            summary = {
                'total_ingresos': total_ingresos,
                'total_ingresos_mes': total_ingresos_mes,
                'total_recurrentes': total_recurrentes,
                'total_registros': len(incomes),
                'ingresos_por_categoria': ingresos_por_categoria
            }
            
            return render_template('incomes/index.html',
                                 incomes=incomes,
                                 summary=summary)
                                 
        except Exception as e:
            print(f"Error en incomes index: {e}")
            return render_template('incomes/index.html',
                                 incomes=[],
                                 summary={'total_ingresos': 0, 'total_ingresos_mes': 0, 
                                         'total_recurrentes': 0, 'total_registros': 0,
                                         'ingresos_por_categoria': {}})
    
    def add(self):
        try:
            concepto = request.form.get('concepto')
            monto = float(request.form.get('monto'))
            fecha_str = request.form.get('fecha')
            categoria = request.form.get('categoria')
            descripcion = request.form.get('descripcion')
            recurrente = bool(request.form.get('recurrente'))
            frecuencia = request.form.get('frecuencia')
            
            # Convertir fecha string a objeto date
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else datetime.now().date()
            
            # Validaciones básicas
            if not concepto or monto <= 0:
                return jsonify({'success': False, 'error': 'Datos inválidos'})
            
            # Crear nuevo ingreso
            nuevo_ingreso = Income(
                concepto=concepto,
                monto=monto,
                fecha=fecha,
                categoria=categoria,
                descripcion=descripcion,
                recurrente=recurrente,
                frecuencia=frecuencia if recurrente else None
            )
            
            db.session.add(nuevo_ingreso)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Ingreso agregado correctamente'})
            
        except Exception as e:
            db.session.rollback()
            print(f"Error al agregar ingreso: {e}")
            return jsonify({'success': False, 'error': 'Error al agregar el ingreso'})
    
    def update(self, income_id):
        try:
            income = Income.query.get_or_404(income_id)
            
            concepto = request.form.get('concepto')
            monto = float(request.form.get('monto'))
            fecha_str = request.form.get('fecha')
            categoria = request.form.get('categoria')
            descripcion = request.form.get('descripcion')
            recurrente = bool(request.form.get('recurrente'))
            frecuencia = request.form.get('frecuencia')
            
            # Convertir fecha string a objeto date
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else datetime.now().date()
            
            # Validaciones básicas
            if not concepto or monto <= 0:
                return jsonify({'success': False, 'error': 'Datos inválidos'})
            
            # Actualizar ingreso
            income.concepto = concepto
            income.monto = monto
            income.fecha = fecha
            income.categoria = categoria
            income.descripcion = descripcion
            income.recurrente = recurrente
            income.frecuencia = frecuencia if recurrente else None
            
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Ingreso actualizado correctamente'})
            
        except Exception as e:
            db.session.rollback()
            print(f"Error al actualizar ingreso: {e}")
            return jsonify({'success': False, 'error': 'Error al actualizar el ingreso'})
    
    def delete(self, income_id):
        try:
            income = Income.query.get_or_404(income_id)
            
            db.session.delete(income)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Ingreso eliminado correctamente'})
            
        except Exception as e:
            db.session.rollback()
            print(f"Error al eliminar ingreso: {e}")
            return jsonify({'success': False, 'error': 'Error al eliminar el ingreso'})
    
    def get_income(self, income_id):
        try:
            income = Income.query.get_or_404(income_id)
            
            return jsonify({
                'success': True,
                'income': {
                    'id': income.id,
                    'concepto': income.concepto,
                    'monto': income.monto,
                    'fecha': income.fecha_iso,
                    'categoria': income.categoria,
                    'descripcion': income.descripcion or '',
                    'recurrente': income.recurrente,
                    'frecuencia': income.frecuencia or ''
                }
            })
            
        except Exception as e:
            print(f"Error al obtener ingreso: {e}")
            return jsonify({'success': False, 'error': 'Error al obtener el ingreso'})

# Crear instancia del controlador
income_controller = IncomeController()