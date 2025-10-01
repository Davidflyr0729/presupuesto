from utils.database import Database
from datetime import datetime

class DashboardModel:
    def __init__(self):
        self.db = Database()

    def get_monthly_summary(self, usuario_id, month=None, year=None):
        """Obtener resumen mensual"""
        if not month or not year:
            current_date = datetime.now()
            month = current_date.month
            year = current_date.year

        # Obtener ingresos y gastos del mes
        income_query = """
        SELECT COALESCE(SUM(monto), 0) as total 
        FROM ingresos 
        WHERE usuario_id = %s AND MONTH(fecha) = %s AND YEAR(fecha) = %s
        """
        income_result = self.db.execute_query(income_query, (usuario_id, month, year), fetch_one=True)
        
        expense_query = """
        SELECT COALESCE(SUM(monto), 0) as total 
        FROM gastos 
        WHERE usuario_id = %s AND MONTH(fecha) = %s AND YEAR(fecha) = %s
        """
        expense_result = self.db.execute_query(expense_query, (usuario_id, month, year), fetch_one=True)

        total_income = income_result['total'] if income_result else 0
        total_expense = expense_result['total'] if expense_result else 0
        balance = total_income - total_expense
        savings_rate = (balance / total_income * 100) if total_income > 0 else 0

        return {
            'total_income': total_income,
            'total_expense': total_expense,
            'balance': balance,
            'savings_rate': round(savings_rate, 2)
        }

    def get_expenses_by_category(self, usuario_id, month=None, year=None):
        """Obtener gastos agrupados por categoría"""
        if not month or not year:
            current_date = datetime.now()
            month = current_date.month
            year = current_date.year

        query = """
        SELECT cg.nombre, cg.color, COALESCE(SUM(g.monto), 0) as total
        FROM categorias_gastos cg
        LEFT JOIN gastos g ON cg.id = g.categoria_id 
            AND g.usuario_id = %s 
            AND MONTH(g.fecha) = %s 
            AND YEAR(g.fecha) = %s
        GROUP BY cg.id, cg.nombre, cg.color
        HAVING total > 0
        ORDER BY total DESC
        """
        
        return self.db.execute_query(query, (usuario_id, month, year), fetch=True)

    def get_recent_transactions(self, usuario_id, limit=5):
        """Obtener transacciones recientes"""
        query = """
        (SELECT 'income' as tipo, id, concepto, monto, fecha, fecha_registro
         FROM ingresos WHERE usuario_id = %s)
        UNION ALL
        (SELECT 'expense' as tipo, id, concepto, monto, fecha, fecha_registro
         FROM gastos WHERE usuario_id = %s)
        ORDER BY fecha_registro DESC
        LIMIT %s
        """
        
        return self.db.execute_query(query, (usuario_id, usuario_id, limit), fetch=True)