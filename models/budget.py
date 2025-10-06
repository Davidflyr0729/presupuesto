from utils.database import Database
from datetime import datetime

class BudgetModel:
    def __init__(self):
        self.db = Database()
        self.table = "presupuestos"

    def create(self, usuario_id, categoria_gasto_id, monto_maximo, mes_year):
        """Crear nuevo presupuesto"""
        query = f"""
        INSERT INTO {self.table} (usuario_id, categoria_gasto_id, monto_maximo, mes_year)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE monto_maximo = VALUES(monto_maximo)
        """
        return self.db.execute_query(
            query, 
            (usuario_id, categoria_gasto_id, monto_maximo, mes_year)
        )

    def get_by_user(self, usuario_id, month=None, year=None):
        """Obtener presupuestos del usuario"""
        if not month or not year:
            current_date = datetime.now()
            month = current_date.month
            year = current_date.year

        # Formatear el mes_year para comparar con el campo VARCHAR
        mes_year_str = f"{year}-{month:02d}"

        query = f"""
        SELECT p.*, cg.nombre as categoria_nombre, cg.color, cg.icono,
               COALESCE(SUM(g.monto), 0) as gasto_actual,
               (p.monto_maximo - COALESCE(SUM(g.monto), 0)) as saldo_restante,
           CASE 
               WHEN p.monto_maximo > 0 THEN 
                   ROUND((COALESCE(SUM(g.monto), 0) / p.monto_maximo) * 100, 2)
               ELSE 0 
           END as porcentaje_uso
        FROM {self.table} p
        LEFT JOIN categorias_gastos cg ON p.categoria_gasto_id = cg.id
        LEFT JOIN gastos g ON p.categoria_gasto_id = g.categoria_id 
            AND g.usuario_id = p.usuario_id 
            AND MONTH(g.fecha) = %s  -- Usar los parámetros month/year directamente
            AND YEAR(g.fecha) = %s
        WHERE p.usuario_id = %s 
            AND p.mes_year = %s  -- Comparar directamente con el campo VARCHAR
        GROUP BY p.id, p.monto_maximo, cg.nombre, cg.color, cg.icono
        ORDER BY cg.nombre
        """
        
        return self.db.execute_query(query, (month, year, usuario_id, mes_year_str), fetch=True)

    def get_budget_summary(self, usuario_id, month=None, year=None):
        """Obtener resumen general de presupuestos"""
        if not month or not year:
            current_date = datetime.now()
            month = current_date.month
            year = current_date.year

        # Formatear el mes_year para comparar con el campo VARCHAR
        mes_year_str = f"{year}-{month:02d}"

        query = """
        SELECT 
            COALESCE(SUM(p.monto_maximo), 0) as total_presupuestado,
            COALESCE(SUM(
                (SELECT COALESCE(SUM(g.monto), 0) 
                 FROM gastos g 
                 WHERE g.categoria_id = p.categoria_gasto_id 
                 AND g.usuario_id = p.usuario_id 
                 AND MONTH(g.fecha) = %s 
                 AND YEAR(g.fecha) = %s)
            ), 0) as total_gastado,
            COUNT(p.id) as total_categorias
        FROM presupuestos p
        WHERE p.usuario_id = %s 
            AND p.mes_year = %s  -- Comparar directamente con el campo VARCHAR
        """
        
        result = self.db.execute_query(query, (month, year, usuario_id, mes_year_str), fetch_one=True)
        
        if result:
            total_presupuestado = result['total_presupuestado'] or 0
            total_gastado = result['total_gastado'] or 0
            saldo_restante = total_presupuestado - total_gastado
            
            return {
                'total_presupuestado': total_presupuestado,
                'total_gastado': total_gastado,
                'saldo_restante': saldo_restante,
                'total_categorias': result['total_categorias'] or 0
            }
        
        return {
            'total_presupuestado': 0,
            'total_gastado': 0,
            'saldo_restante': 0,
            'total_categorias': 0
        }

    def get_by_id(self, presupuesto_id, usuario_id):
        """Obtener presupuesto por ID"""
        query = f"SELECT * FROM {self.table} WHERE id = %s AND usuario_id = %s"
        return self.db.execute_query(query, (presupuesto_id, usuario_id), fetch_one=True)

    def update(self, presupuesto_id, usuario_id, monto_maximo):
        """Actualizar presupuesto"""
        query = f"UPDATE {self.table} SET monto_maximo = %s WHERE id = %s AND usuario_id = %s"
        return self.db.execute_query(query, (monto_maximo, presupuesto_id, usuario_id))

    def delete(self, presupuesto_id, usuario_id):
        """Eliminar presupuesto"""
        query = f"DELETE FROM {self.table} WHERE id = %s AND usuario_id = %s"
        return self.db.execute_query(query, (presupuesto_id, usuario_id))

    def get_categories_without_budget(self, usuario_id, month, year):
        """Obtener categorías sin presupuesto asignado"""
        # Formatear el mes_year para comparar con el campo VARCHAR
        mes_year_str = f"{year}-{month:02d}"
        
        query = """
        SELECT cg.* 
        FROM categorias_gastos cg
        WHERE cg.id NOT IN (
            SELECT categoria_gasto_id 
            FROM presupuestos 
            WHERE usuario_id = %s 
            AND mes_year = %s  -- Comparar directamente con el campo VARCHAR
        )
        ORDER BY cg.nombre
        """
        return self.db.execute_query(query, (usuario_id, mes_year_str), fetch=True)

    def get_budget_by_category(self, usuario_id, categoria_gasto_id, month=None, year=None):
        """Obtener presupuesto específico de una categoría"""
        if not month or not year:
            current_date = datetime.now()
            month = current_date.month
            year = current_date.year

        # Formatear el mes_year para comparar con el campo VARCHAR
        mes_year_str = f"{year}-{month:02d}"

        query = f"""
        SELECT p.*, 
               COALESCE((
                   SELECT SUM(g.monto) 
                   FROM gastos g 
                   WHERE g.categoria_id = p.categoria_gasto_id 
                     AND g.usuario_id = p.usuario_id 
                     AND MONTH(g.fecha) = %s 
                     AND YEAR(g.fecha) = %s
               ), 0) as gasto_actual,
               (p.monto_maximo - COALESCE((
                   SELECT SUM(g.monto) 
                   FROM gastos g 
                   WHERE g.categoria_id = p.categoria_gasto_id 
                     AND g.usuario_id = p.usuario_id 
                     AND MONTH(g.fecha) = %s 
                     AND YEAR(g.fecha) = %s
               ), 0)) as saldo_restante
        FROM {self.table} p
        WHERE p.usuario_id = %s 
            AND p.categoria_gasto_id = %s
            AND p.mes_year = %s
        """
        
        return self.db.execute_query(query, (month, year, month, year, usuario_id, categoria_gasto_id, mes_year_str), fetch_one=True)