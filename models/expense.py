from utils.database import Database

class ExpenseModel:
    def __init__(self):
        self.db = Database()
        self.table = "gastos"

    def create(self, usuario_id, concepto, monto, categoria_id, fecha, esencial=True, descripcion=None):
        """Crear nuevo gasto"""
        query = f"""
        INSERT INTO {self.table} (usuario_id, concepto, monto, categoria_id, fecha, esencial, descripcion)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        return self.db.execute_query(
            query, 
            (usuario_id, concepto, monto, categoria_id, fecha, 1 if esencial else 0, descripcion)
        )

    def get_by_user(self, usuario_id, month=None, year=None):
        """Obtener gastos del usuario - ORDENADO POR FECHA DESCENDENTE (más reciente primero)"""
        query = f"""
        SELECT g.*, cg.nombre as categoria_nombre, cg.color, cg.icono
        FROM {self.table} g 
        LEFT JOIN categorias_gastos cg ON g.categoria_id = cg.id 
        WHERE g.usuario_id = %s
        """
        params = [usuario_id]

        if month and year:
            query += " AND MONTH(g.fecha) = %s AND YEAR(g.fecha) = %s"
            params.extend([month, year])

        # ORDENAR POR FECHA DESCENDENTE Y ID DESCENDENTE (para consistencia)
        query += " ORDER BY g.fecha DESC, g.id DESC"
        return self.db.execute_query(query, tuple(params), fetch=True)

    def get_total(self, usuario_id, month=None, year=None):
        """Obtener total de gastos"""
        query = f"SELECT SUM(monto) as total FROM {self.table} WHERE usuario_id = %s"
        params = [usuario_id]

        if month and year:
            query += " AND MONTH(fecha) = %s AND YEAR(fecha) = %s"
            params.extend([month, year])

        result = self.db.execute_query(query, tuple(params), fetch_one=True)
        return result['total'] if result and result['total'] else 0

    def get_categories(self):
        """Obtener todas las categorías de gastos"""
        query = "SELECT * FROM categorias_gastos ORDER BY nombre"
        return self.db.execute_query(query, fetch=True)