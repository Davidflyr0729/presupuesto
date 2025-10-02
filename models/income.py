from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# En lugar de from presupuesto_app import db
db = SQLAlchemy()  # O usa la instancia correcta

class Income(db.Model):
    __tablename__ = 'incomes'
    
    id = db.Column(db.Integer, primary_key=True)
    concepto = db.Column(db.String(200), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    categoria = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    recurrente = db.Column(db.Boolean, default=False)
    frecuencia = db.Column(db.String(50))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, concepto, monto, fecha, categoria, descripcion=None, recurrente=False, frecuencia=None):
        self.concepto = concepto
        self.monto = monto
        self.fecha = fecha
        self.categoria = categoria
        self.descripcion = descripcion
        self.recurrente = recurrente
        self.frecuencia = frecuencia
    
    @property
    def fecha_formateada(self):
        """Devuelve la fecha formateada como string"""
        if self.fecha:
            return self.fecha.strftime('%d/%m/%Y') if hasattr(self.fecha, 'strftime') else str(self.fecha)
        return "N/A"
    
    @property
    def monto_formateado(self):
        """Devuelve el monto formateado como string"""
        return f"${self.monto:,.0f}"
    
    @property
    def fecha_iso(self):
        """Devuelve la fecha en formato ISO para inputs date"""
        if self.fecha:
            return self.fecha.strftime('%Y-%m-%d') if hasattr(self.fecha, 'strftime') else ''
        return ''
    
    def __repr__(self):
        return f'<Income {self.concepto} - {self.monto_formateado}>'