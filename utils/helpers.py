from datetime import datetime
import decimal

def format_currency(value):
    """Formatear valor como moneda"""
    if value is None:
        return "$0"
    return f"${value:,.0f}"

def format_date(date_string):
    """Formatear fecha"""
    if isinstance(date_string, str):
        date_obj = datetime.strptime(date_string, '%Y-%m-%d')
    else:
        date_obj = date_string
    return date_obj.strftime('%d/%m/%Y')

def decimal_to_float(value):
    """Convertir decimal a float para JSON"""
    if isinstance(value, decimal.Decimal):
        return float(value)
    return value