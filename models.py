from database import Database
from datetime import datetime

class PresupuestoModel:
    def __init__(self):
        self.db = Database()

    # ==================== AUTENTICACIÓN MEJORADA ====================
    def login_usuario(self, email, password):
        """Login de usuario - Versión corregida y robusta"""
        try:
            print(f"🔐 Intentando login para: {email}")
            print(f"🔑 Contraseña recibida: {'*' * len(password)} (longitud: {len(password)})")
            
            # Query MEJORADA - usar 'clave' en lugar de 'password'
            query = """
            SELECT id, nombre, email, clave, rol_id, activo
            FROM usuarios 
            WHERE email = %s AND activo = 1
            LIMIT 1
            """
            
            print(f"🔍 Ejecutando query para: {email}")
            resultado = self.db.ejecutar_consulta(query, (email,))
            
            if not resultado:
                print(f"❌ Usuario no encontrado o inactivo: {email}")
                return None, "Usuario no encontrado"
            
            usuario = resultado[0]
            print(f"✅ Usuario encontrado en BD: {usuario['nombre']}")
            print(f"📋 Datos usuario - ID: {usuario['id']}, Email: {usuario['email']}, Activo: {usuario['activo']}")
            print(f"🔑 Clave en BD: {usuario['clave']}")
            print(f"🔑 Clave recibida: {password}")
            
            # Comparación DIRECTA - verificar exactamente lo que hay en BD
            if password == usuario['clave']:
                print(f"✅✅✅ CONTRASEÑA CORRECTA para {email}")
                
                usuario_info = {
                    'id': usuario['id'],
                    'nombre': usuario['nombre'], 
                    'email': usuario['email'],
                    'rol_id': usuario['rol_id'],
                    'rol_nombre': 'Administrador' if usuario['rol_id'] == 1 else 'Usuario'
                }
                
                print(f"🎉 Login exitoso, retornando usuario: {usuario_info}")
                return usuario_info, "Login exitoso"
            else:
                print(f"❌❌❌ CONTRASEÑA INCORRECTA")
                print(f"   BD: '{usuario['clave']}'")
                print(f"   Recibida: '{password}'")
                print(f"   Coinciden: {password == usuario['clave']}")
                return None, "Contraseña incorrecta"
                
        except Exception as e:
            print(f"💥💥💥 Error CRÍTICO en login: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, f"Error del servidor: {str(e)}"

    def verificar_acceso(self, usuario_id):
        """Verificar si el usuario existe y tiene acceso"""
        try:
            query = "SELECT id, nombre, email FROM usuarios WHERE id = %s AND activo = 1"
            resultado = self.db.ejecutar_consulta(query, (usuario_id,))
            return resultado[0] if resultado else None
        except Exception as e:
            print(f"Error verificando acceso: {e}")
            return None

    # ==================== MÉTODOS PARA DEBUG ====================
    def debug_usuarios(self):
        """Método para debug - ver todos los usuarios"""
        try:
            query = "SELECT id, nombre, email, clave, rol_id, activo FROM usuarios"
            usuarios = self.db.ejecutar_consulta(query)
            print("=" * 50)
            print("👥 DEBUG - TODOS LOS USUARIOS EN BD:")
            for usuario in usuarios:
                print(f"  ID: {usuario['id']}, Nombre: {usuario['nombre']}, Email: {usuario['email']}, Clave: {usuario['clave']}, Activo: {usuario['activo']}")
            print("=" * 50)
            return usuarios
        except Exception as e:
            print(f"Error en debug_usuarios: {e}")
            return []

    def crear_usuario_prueba(self, email, password, nombre="Usuario Prueba"):
        """Crear usuario de prueba si no existe"""
        try:
            # Verificar si ya existe
            check_query = "SELECT id FROM usuarios WHERE email = %s"
            existe = self.db.ejecutar_consulta(check_query, (email,))
            
            if existe:
                print(f"✅ Usuario {email} ya existe")
                return True
                
            # Crear nuevo usuario
            insert_query = """
            INSERT INTO usuarios (nombre, email, clave, rol_id, activo) 
            VALUES (%s, %s, %s, %s, %s)
            """
            resultado = self.db.ejecutar_consulta(insert_query, (nombre, email, password, 2, 1))
            print(f"✅ Usuario {email} creado exitosamente")
            return True
            
        except Exception as e:
            print(f"❌ Error creando usuario: {e}")
            return False

    # ==================== MÉTODOS PRINCIPALES ====================
    def obtener_resumen(self, usuario_id=1, año=None, mes=None):
        """Obtener resumen financiero del usuario"""
        try:
            print(f"📊 Obteniendo resumen para usuario {usuario_id}")
            
            usuario = self.verificar_acceso(usuario_id)
            if not usuario:
                return {
                    'usuario': 'Usuario no encontrado',
                    'total_ingresos': 0,
                    'total_gastos': 0,
                    'saldo': 0,
                    'porcentaje_ahorro': 0,
                    'mes_actual': mes or datetime.now().month,
                    'año_actual': año or datetime.now().year
                }
            
            año_actual = año or datetime.now().year
            mes_actual = mes or datetime.now().month
        
            # Ingresos del mes
            query_ingresos = """
            SELECT COALESCE(SUM(monto), 0) as total 
            FROM ingresos 
            WHERE usuario_id = %s 
            AND YEAR(fecha) = %s 
            AND MONTH(fecha) = %s
            """
            resultado_ingresos = self.db.ejecutar_consulta(query_ingresos, (usuario_id, año_actual, mes_actual))
            total_ingresos = float(resultado_ingresos[0]['total']) if resultado_ingresos else 0
        
            # Gastos del mes
            query_gastos = """
            SELECT COALESCE(SUM(monto), 0) as total 
            FROM gastos 
            WHERE usuario_id = %s 
            AND YEAR(fecha) = %s 
            AND MONTH(fecha) = %s
            """
            resultado_gastos = self.db.ejecutar_consulta(query_gastos, (usuario_id, año_actual, mes_actual))
            total_gastos = float(resultado_gastos[0]['total']) if resultado_gastos else 0
        
            # Cálculos
            saldo = total_ingresos - total_gastos
            porcentaje_ahorro = (saldo / total_ingresos * 100) if total_ingresos > 0 else 0
        
            resumen = {
                'usuario': usuario['nombre'],
                'total_ingresos': total_ingresos,
                'total_gastos': total_gastos,
                'saldo': saldo,
                'porcentaje_ahorro': round(porcentaje_ahorro, 2),
                'mes_actual': mes_actual,
                'año_actual': año_actual
            }
            
            print(f"✅ Resumen obtenido: {resumen}")
            return resumen
            
        except Exception as e:
            print(f"❌ Error obteniendo resumen: {e}")
            return {
                'usuario': 'Usuario',
                'total_ingresos': 0,
                'total_gastos': 0,
                'saldo': 0,
                'porcentaje_ahorro': 0,
                'mes_actual': mes or datetime.now().month,
                'año_actual': año or datetime.now().year
            }
    
    def obtener_ingresos(self, usuario_id=1, limite=10, año=None, mes=None):
        """Obtener lista de ingresos del usuario"""
        try:
            if not self.verificar_acceso(usuario_id):
                return []
            
            query_base = """
            SELECT i.*, ci.nombre as categoria_nombre, ci.icono
            FROM ingresos i
            LEFT JOIN categorias_ingresos ci ON i.categoria_id = ci.id
            WHERE i.usuario_id = %s
            """
            params = [usuario_id]
            
            if año and mes:
                query_base += " AND YEAR(i.fecha) = %s AND MONTH(i.fecha) = %s"
                params.extend([año, mes])
            
            query_base += " ORDER BY i.fecha DESC, i.id DESC LIMIT %s"
            params.append(limite)
                
            ingresos = self.db.ejecutar_consulta(query_base, tuple(params))
            print(f"✅ Obtenidos {len(ingresos)} ingresos para usuario {usuario_id}")
            return ingresos
            
        except Exception as e:
            print(f"❌ Error obteniendo ingresos: {e}")
            return []
    
    def agregar_ingreso(self, concepto, monto, categoria_id, fecha=None, usuario_id=1):
        """Agregar un nuevo ingreso"""
        try:
            if not self.verificar_acceso(usuario_id):
                return None
                
            if fecha is None:
                fecha = datetime.now().date()
            elif isinstance(fecha, str):
                fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
            
            query = """
            INSERT INTO ingresos (usuario_id, concepto, monto, categoria_id, fecha) 
            VALUES (%s, %s, %s, %s, %s)
            """
            resultado = self.db.ejecutar_consulta(query, (usuario_id, concepto, float(monto), categoria_id, fecha))
            print(f"✅ Ingreso agregado: {concepto} - ${monto}")
            return resultado
            
        except Exception as e:
            print(f"❌ Error agregando ingreso: {e}")
            return None
    
    def obtener_gastos(self, usuario_id=1, limite=10, año=None, mes=None):
        """Obtener lista de gastos del usuario"""
        try:
            if not self.verificar_acceso(usuario_id):
                return []
            
            query_base = """
            SELECT g.*, cg.nombre as categoria_nombre, cg.icono
            FROM gastos g
            LEFT JOIN categorias_gastos cg ON g.categoria_id = cg.id
            WHERE g.usuario_id = %s
            """
            params = [usuario_id]
            
            if año and mes:
                query_base += " AND YEAR(g.fecha) = %s AND MONTH(g.fecha) = %s"
                params.extend([año, mes])
            
            query_base += " ORDER BY g.fecha DESC, g.id DESC LIMIT %s"
            params.append(limite)
                
            gastos = self.db.ejecutar_consulta(query_base, tuple(params))
            print(f"✅ Obtenidos {len(gastos)} gastos para usuario {usuario_id}")
            return gastos
            
        except Exception as e:
            print(f"❌ Error obteniendo gastos: {e}")
            return []
    
    def agregar_gasto(self, concepto, monto, categoria_id, fecha=None, esencial=True, usuario_id=1):
        """Agregar un nuevo gasto"""
        try:
            if not self.verificar_acceso(usuario_id):
                return None
                
            if fecha is None:
                fecha = datetime.now().date()
            elif isinstance(fecha, str):
                fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
            
            query = """
            INSERT INTO gastos (usuario_id, concepto, monto, categoria_id, fecha, esencial) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            resultado = self.db.ejecutar_consulta(query, (usuario_id, concepto, float(monto), categoria_id, fecha, esencial))
            print(f"✅ Gasto agregado: {concepto} - ${monto}")
            return resultado
            
        except Exception as e:
            print(f"❌ Error agregando gasto: {e}")
            return None
    
    def obtener_categorias_ingresos(self):
        """Obtener categorías de ingresos"""
        try:
            categorias = self.db.ejecutar_consulta("SELECT * FROM categorias_ingresos ORDER BY nombre")
            print(f"✅ Obtenidas {len(categorias)} categorías de ingresos")
            return categorias
        except Exception as e:
            print(f"❌ Error obteniendo categorías de ingresos: {e}")
            return []
    
    def obtener_categorias_gastos(self):
        """Obtener categorías de gastos"""
        try:
            categorias = self.db.ejecutar_consulta("SELECT * FROM categorias_gastos ORDER BY nombre")
            print(f"✅ Obtenidas {len(categorias)} categorías de gastos")
            return categorias
        except Exception as e:
            print(f"❌ Error obteniendo categorías de gastos: {e}")
            return []

    # ==================== INICIALIZACIÓN AUTOMÁTICA ====================
    def inicializar_usuarios_prueba(self):
        """Inicializar usuarios de prueba automáticamente"""
        try:
            print("🔄 Inicializando usuarios de prueba...")
            
            usuarios_prueba = [
                {
                    'email': 'nelson.galvez@flyr.com',
                    'password': '123456',
                    'nombre': 'Nelson Galvez'
                },
                {
                    'email': 'admin@demo.com', 
                    'password': 'admin123',
                    'nombre': 'Administrador Demo'
                },
                {
                    'email': 'usuario@demo.com',
                    'password': 'user123', 
                    'nombre': 'Usuario Demo'
                }
            ]
            
            for usuario in usuarios_prueba:
                self.crear_usuario_prueba(
                    usuario['email'],
                    usuario['password'],
                    usuario['nombre']
                )
            
            # Mostrar todos los usuarios después de inicializar
            self.debug_usuarios()
            
        except Exception as e:
            print(f"❌ Error inicializando usuarios: {e}")

# Inicializar automáticamente al importar el módulo
if __name__ == "__main__":
    modelo = PresupuestoModel()
    modelo.inicializar_usuarios_prueba()