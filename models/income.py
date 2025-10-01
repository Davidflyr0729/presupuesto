from utils.database import Database
from datetime import datetime

class IncomeModel:
    def __init__(self):
        self.db = Database()
        self.table = "ingresos"

    def create(self, usuario_id, concepto, monto, categoria_id, fecha, descripcion=None):
        """Crear nuevo ingreso"""
        query = f"""
        INSERT INTO {self.table} (usuario_id, concepto, monto, categoria_id, fecha, descripcion)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        return self.db.execute_query(
            query, 
            (usuario_id, concepto, monto, categoria_id, fecha, descripcion)
        )

    def get_by_user(self, usuario_id, month=None, year=None):
        """Obtener ingresos del usuario"""
        query = f"""
        SELECT i.*, ci.nombre as categoria_nombre, ci.color, ci.icono
        FROM {self.table} i 
        LEFT JOIN categorias_ingresos ci ON i.categoria_id = ci.id 
        WHERE i.usuario_id = %s
        """
        params = [usuario_id]

        if month and year:
            query += " AND MONTH(i.fecha) = %s AND YEAR(i.fecha) = %s"
            params.extend([month, year])

        query += " ORDER BY i.fecha DESC"
        return self.db.execute_query(query, tuple(params), fetch=True)

    def get_total(self, usuario_id, month=None, year=None):
        """Obtener total de ingresos"""
        query = f"SELECT SUM(monto) as total FROM {self.table} WHERE usuario_id = %s"
        params = [usuario_id]

        if month and year:
            query += " AND MONTH(fecha) = %s AND YEAR(fecha) = %s"
            params.extend([month, year])

        result = self.db.execute_query(query, tuple(params), fetch_one=True)
        return result['total'] if result and result['total'] else 0

    def get_categories(self):
        """Obtener todas las categorías de ingresos"""
        query = "SELECT * FROM categorias_ingresos ORDER BY nombre"
        return self.db.execute_query(query, fetch=True)