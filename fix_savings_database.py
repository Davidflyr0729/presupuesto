from utils.database import Database

def fix_savings_table():
    """Corregir la tabla ahorros agregando la columna descripcion"""
    db = Database()
    
    print("🔄 Corrigiendo tabla de ahorros...")
    print("=" * 50)
    
    try:
        # 1. Verificar la estructura actual de la tabla
        print("📋 Estructura actual de la tabla 'ahorros':")
        describe_query = "DESCRIBE ahorros"
        columns = db.execute_query(describe_query, fetch=True)
        
        current_columns = []
        for column in columns:
            print(f"   ✅ {column['Field']} - {column['Type']}")
            current_columns.append(column['Field'])
        
        print()
        
        # 2. Verificar si la columna 'descripcion' existe
        if 'descripcion' not in current_columns:
            print("❌ Columna 'descripcion' no encontrada")
            print("🔄 Agregando columna 'descripcion'...")
            
            # Agregar la columna descripcion
            alter_query = """
            ALTER TABLE `ahorros` 
            ADD COLUMN `descripcion` TEXT NULL AFTER `fecha_objetivo`
            """
            db.execute_query(alter_query)
            print("✅ Columna 'descripcion' agregada exitosamente")
        else:
            print("✅ Columna 'descripcion' ya existe")
        
        print()
        
        # 3. Verificar estructura final
        print("📋 Estructura final de la tabla 'ahorros':")
        final_columns = db.execute_query(describe_query, fetch=True)
        for column in final_columns:
            print(f"   ✅ {column['Field']} - {column['Type']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error corrigiendo la tabla: {e}")
        return False

def test_savings_creation():
    """Probar la creación de una meta de ahorro después de la corrección"""
    from models.savings import SavingsModel
    from datetime import datetime, timedelta
    
    print("\n🧪 Probando creación de meta de ahorro...")
    print("=" * 50)
    
    savings_model = SavingsModel()
    
    try:
        # Crear una meta de ahorro de prueba
        user_id = 1
        fecha_objetivo = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        savings_id = savings_model.create(
            usuario_id=user_id,
            concepto="Prueba - Nuevo Laptop",
            meta_total=2500000,
            fecha_objetivo=fecha_objetivo,
            descripcion="Ahorrar para comprar un nuevo laptop para trabajo"
        )
        
        print(f"✅ Meta de ahorro creada exitosamente!")
        print(f"   🆔 ID: {savings_id}")
        print(f"   🎯 Concepto: Prueba - Nuevo Laptop")
        print(f"   💰 Meta: $2,500,000")
        print(f"   📅 Fecha objetivo: {fecha_objetivo}")
        print(f"   📝 Descripción: Ahorrar para comprar un nuevo laptop para trabajo")
        
        # Verificar que se guardó correctamente
        savings = savings_model.get_by_user(user_id)
        if savings:
            latest_saving = savings[0]  # La más reciente
            print(f"\n📊 Meta recuperada de la base de datos:")
            print(f"   🎯 Concepto: {latest_saving['concepto']}")
            print(f"   💰 Ahorrado: ${latest_saving['ahorrado_actual']:,.0f}")
            print(f"   🎯 Meta: ${latest_saving['meta_total']:,.0f}")
            print(f"   📊 Progreso: {latest_saving['porcentaje_completado']}%")
            print(f"   📝 Descripción: {latest_saving.get('descripcion', 'No disponible')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando meta de ahorro: {e}")
        return False

if __name__ == '__main__':
    print("🔧 INICIANDO CORRECCIÓN DE BASE DE DATOS")
    print("=" * 60)
    
    if fix_savings_table():
        print("\n" + "=" * 60)
        print("✅ Base de datos corregida exitosamente!")
        print("\n" + "=" * 60)
        test_savings_creation()
    else:
        print("\n❌ No se pudo corregir la base de datos")