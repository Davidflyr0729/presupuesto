from utils.database import Database
from datetime import datetime

class SavingsModel:
    def __init__(self):
        self.db = Database()
        self.table = "ahorros"

    def create(self, usuario_id, concepto, meta_total, fecha_objetivo=None, descripcion=None):
        """Crear nueva meta de ahorro"""
        query = f"""
        INSERT INTO {self.table} (usuario_id, concepto, meta_total, ahorrado_actual, fecha_inicio, fecha_objetivo, descripcion)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        return self.db.execute_query(
            query, 
            (usuario_id, concepto, meta_total, 0.00, datetime.now().date(), fecha_objetivo, descripcion)
        )

    def get_by_user(self, usuario_id):
        """Obtener ahorros del usuario"""
        query = f"""
        SELECT *,
               CASE 
                   WHEN meta_total > 0 THEN 
                       ROUND((ahorrado_actual / meta_total) * 100, 2)
                   ELSE 0 
               END as porcentaje_completado,
               DATEDIFF(COALESCE(fecha_objetivo, DATE_ADD(fecha_inicio, INTERVAL 3 MONTH)), CURDATE()) as dias_restantes
        FROM {self.table} 
        WHERE usuario_id = %s 
        ORDER BY completado ASC, fecha_objetivo ASC
        """
        return self.db.execute_query(query, (usuario_id,), fetch=True)

    def get_by_id(self, ahorro_id, usuario_id):
        """Obtener ahorro por ID"""
        query = f"SELECT * FROM {self.table} WHERE id = %s AND usuario_id = %s"
        return self.db.execute_query(query, (ahorro_id, usuario_id), fetch_one=True)

    def add_savings(self, ahorro_id, usuario_id, monto):
        """Agregar dinero al ahorro"""
        # Primero obtener el estado actual del ahorro
        current_saving = self.get_by_id(ahorro_id, usuario_id)
        if not current_saving:
            raise Exception("Ahorro no encontrado")
        
        ahorrado_actual = float(current_saving['ahorrado_actual'])
        meta_total = float(current_saving['meta_total'])
        nuevo_ahorrado = ahorrado_actual + monto
        
        # ✅ CORREGIDO: Usar cálculo preciso para determinar si está completado
        # Usamos una pequeña tolerancia para evitar problemas de redondeo
        completado = 1 if (nuevo_ahorrado + 0.001) >= meta_total else 0
        
        query = f"""
        UPDATE {self.table} 
        SET ahorrado_actual = %s,
            completado = %s
        WHERE id = %s AND usuario_id = %s
        """
        return self.db.execute_query(query, (nuevo_ahorrado, completado, ahorro_id, usuario_id))

    def update(self, ahorro_id, usuario_id, concepto, meta_total, fecha_objetivo, descripcion):
        """Actualizar meta de ahorro"""
        # Primero obtener el estado actual del ahorro
        current_saving = self.get_by_id(ahorro_id, usuario_id)
        if not current_saving:
            raise Exception("Ahorro no encontrado")
        
        ahorrado_actual = float(current_saving['ahorrado_actual'])
        
        # ✅ CORREGIDO: Usar cálculo preciso para determinar si está completado
        completado = 1 if (ahorrado_actual + 0.001) >= meta_total else 0
        
        query = f"""
        UPDATE {self.table} 
        SET concepto = %s, meta_total = %s, fecha_objetivo = %s, descripcion = %s,
            completado = %s
        WHERE id = %s AND usuario_id = %s
        """
        return self.db.execute_query(query, (concepto, meta_total, fecha_objetivo, descripcion, completado, ahorro_id, usuario_id))

    def delete(self, ahorro_id, usuario_id):
        """Eliminar meta de ahorro"""
        query = f"DELETE FROM {self.table} WHERE id = %s AND usuario_id = %s"
        return self.db.execute_query(query, (ahorro_id, usuario_id))

    def get_savings_summary(self, usuario_id):
        """Obtener resumen de ahorros"""
        query = """
        SELECT 
            COUNT(*) as total_metas,
            SUM(meta_total) as total_meta,
            SUM(ahorrado_actual) as total_ahorrado,
            SUM(CASE WHEN completado = 1 THEN 1 ELSE 0 END) as metas_completadas,
            SUM(CASE WHEN completado = 0 AND fecha_objetivo < CURDATE() THEN 1 ELSE 0 END) as metas_vencidas
        FROM ahorros 
        WHERE usuario_id = %s
        """
        
        result = self.db.execute_query(query, (usuario_id,), fetch_one=True)
        
        if result:
            total_meta = result['total_meta'] or 0
            total_ahorrado = result['total_ahorrado'] or 0
            porcentaje_total = (total_ahorrado / total_meta * 100) if total_meta > 0 else 0
            
            return {
                'total_metas': result['total_metas'] or 0,
                'total_meta': total_meta,
                'total_ahorrado': total_ahorrado,
                'porcentaje_total': round(porcentaje_total, 2),
                'metas_completadas': result['metas_completadas'] or 0,
                'metas_vencidas': result['metas_vencidas'] or 0
            }
        
        return {
            'total_metas': 0,
            'total_meta': 0,
            'total_ahorrado': 0,
            'porcentaje_total': 0,
            'metas_completadas': 0,
            'metas_vencidas': 0
        }