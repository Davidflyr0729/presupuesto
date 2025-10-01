from flask import Flask, jsonify, request, send_from_directory, session
from flask_cors import CORS
from models import PresupuestoModel
from datetime import datetime
import os

app = Flask(__name__, static_folder='static')
app.secret_key = 'presupuesto_secret_key_2024_secure'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
app.config['JSON_SORT_KEYS'] = False

# Configuración de CORS
CORS(app, 
     origins=["http://localhost:5000", "http://127.0.0.1:5000", "http://localhost:3000"],
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

modelo = PresupuestoModel()

# ==================== MANEJO GLOBAL DE OPTIONS ====================
@app.before_request
def handle_options():
    """Manejar solicitudes OPTIONS globalmente"""
    if request.method == 'OPTIONS':
        response = jsonify({"success": True, "message": "Preflight OK"})
        return response

# ==================== RUTAS PARA ARCHIVOS ESTÁTICOS ====================
@app.route('/')
def serve_index():
    """Servir la página principal"""
    try:
        return send_from_directory(app.static_folder, 'index.html')
    except Exception as e:
        print(f"❌ Error sirviendo index.html: {e}")
        return f"""
        <html>
            <body>
                <h1>Error: Archivo no encontrado</h1>
                <p>No se pudo cargar index.html</p>
                <p>Error: {str(e)}</p>
            </body>
        </html>
        """, 404

@app.route('/<path:filename>')
def serve_static(filename):
    """Servir todos los archivos estáticos"""
    try:
        # Si es un archivo directo (como dashboard.html)
        if '.' in filename:
            return send_from_directory(app.static_folder, filename)
        # Si es una ruta de subdirectorio (como js/auth.js)
        else:
            return send_from_directory(app.static_folder, filename)
    except Exception as e:
        print(f"❌ Error sirviendo {filename}: {e}")
        return jsonify({"error": f"Archivo {filename} no encontrado"}), 404

# ==================== MIDDLEWARE DE AUTENTICACIÓN ====================
def requiere_autenticacion(f):
    def decorador(*args, **kwargs):
        try:
            # Por ahora, usar parámetro usuario_id para compatibilidad
            usuario_id = request.args.get('usuario_id', 1, type=int)
            print(f"🔍 Verificando acceso para usuario: {usuario_id}")
            
            usuario = modelo.verificar_acceso(usuario_id)
            
            if not usuario:
                print(f"❌ Usuario no autorizado: {usuario_id}")
                return jsonify({"success": False, "error": "Usuario no autorizado"}), 401
            
            request.user_id = usuario_id
            return f(*args, **kwargs)
            
        except Exception as e:
            print(f"💥 Error en middleware de autenticación: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500
    
    decorador.__name__ = f.__name__
    return decorador

# ==================== RUTAS DE API - AUTENTICACIÓN ====================
@app.route('/api/health', methods=['GET', 'OPTIONS'])
def health_check():
    """Endpoint de salud"""
    if request.method == 'OPTIONS':
        return jsonify({"success": True})
    
    return jsonify({
        "success": True,
        "status": "healthy",
        "timestamp": str(datetime.now()),
        "static_folder": app.static_folder
    })

@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    """Login de usuario"""
    if request.method == 'OPTIONS':
        return jsonify({"success": True})
        
    try:
        print("🔄 Procesando login...")
        
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No se recibieron datos"}), 400
            
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        print(f"🔐 Login para: {email}")
        
        if not email or not password:
            return jsonify({"success": False, "error": "Email y contraseña requeridos"}), 400
        
        # Procesamiento del login
        usuario, mensaje = modelo.login_usuario(email, password)
        
        if usuario:
            print(f"✅ Login exitoso: {email}")
            return jsonify({
                "success": True,
                "mensaje": mensaje,
                "usuario": usuario
            })
        else:
            print(f"❌ Login fallido: {mensaje}")
            return jsonify({"success": False, "error": mensaje}), 401
            
    except Exception as e:
        print(f"💥 Error en login: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": "Error en el servidor"}), 500

@app.route('/api/auth/logout', methods=['POST', 'OPTIONS'])
def logout():
    """Logout"""
    if request.method == 'OPTIONS':
        return jsonify({"success": True})
    
    try:
        print("🚪 Logout solicitado")
        return jsonify({
            "success": True,
            "message": "Sesión cerrada correctamente"
        })
    except Exception as e:
        print(f"Error en logout: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== RUTAS PROTEGIDAS - RESUMEN ====================
@app.route('/api/resumen', methods=['GET', 'OPTIONS'])
@requiere_autenticacion
def obtener_resumen():
    """Obtener resumen financiero del mes"""
    if request.method == 'OPTIONS':
        return jsonify({"success": True})
    
    try:
        usuario_id = request.user_id
        mes = request.args.get('mes', type=int)
        año = request.args.get('año', type=int)
        
        print(f"📊 Solicitando resumen - Usuario: {usuario_id}, Mes: {mes}, Año: {año}")
        
        resumen = modelo.obtener_resumen(usuario_id, año, mes)
        return jsonify({"success": True, "resumen": resumen})
    except Exception as e:
        print(f"❌ Error obteniendo resumen: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== RUTAS PROTEGIDAS - INGRESOS ====================
@app.route('/api/ingresos', methods=['GET', 'POST', 'OPTIONS'])
@requiere_autenticacion
def manejar_ingresos():
    """Obtener y agregar ingresos"""
    if request.method == 'OPTIONS':
        return jsonify({"success": True})
    
    try:
        usuario_id = request.user_id
        
        if request.method == 'GET':
            limite = request.args.get('limite', 10, type=int)
            mes = request.args.get('mes', type=int)
            año = request.args.get('año', type=int)
            
            print(f"📥 Obteniendo ingresos - Usuario: {usuario_id}, Límite: {limite}, Mes: {mes}, Año: {año}")
            
            ingresos = modelo.obtener_ingresos(usuario_id, limite, año, mes)
            return jsonify({"success": True, "ingresos": ingresos})
        
        elif request.method == 'POST':
            data = request.get_json()
            print(f"📝 Agregando ingreso: {data}")
            
            resultado = modelo.agregar_ingreso(
                concepto=data['concepto'],
                monto=data['monto'],
                categoria_id=data['categoria_id'],
                fecha=data.get('fecha'),
                usuario_id=usuario_id
            )
            
            if resultado:
                return jsonify({"success": True, "message": "Ingreso agregado correctamente"})
            else:
                return jsonify({"success": False, "error": "No se pudo agregar el ingreso"}), 500
    
    except Exception as e:
        print(f"❌ Error en ingresos: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== RUTAS PROTEGIDAS - GASTOS ====================
@app.route('/api/gastos', methods=['GET', 'POST', 'OPTIONS'])
@requiere_autenticacion
def manejar_gastos():
    """Obtener y agregar gastos"""
    if request.method == 'OPTIONS':
        return jsonify({"success": True})
    
    try:
        usuario_id = request.user_id
        
        if request.method == 'GET':
            limite = request.args.get('limite', 10, type=int)
            mes = request.args.get('mes', type=int)
            año = request.args.get('año', type=int)
            
            print(f"💸 Obteniendo gastos - Usuario: {usuario_id}, Límite: {limite}, Mes: {mes}, Año: {año}")
            
            gastos = modelo.obtener_gastos(usuario_id, limite, año, mes)
            return jsonify({"success": True, "gastos": gastos})
        
        elif request.method == 'POST':
            data = request.get_json()
            print(f"📝 Agregando gasto: {data}")
            
            resultado = modelo.agregar_gasto(
                concepto=data['concepto'],
                monto=data['monto'],
                categoria_id=data['categoria_id'],
                fecha=data.get('fecha'),
                esencial=data.get('esencial', True),
                usuario_id=usuario_id
            )
            
            if resultado:
                return jsonify({"success": True, "message": "Gasto agregado correctamente"})
            else:
                return jsonify({"success": False, "error": "No se pudo agregar el gasto"}), 500
    
    except Exception as e:
        print(f"❌ Error en gastos: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== RUTAS PÚBLICAS - CATEGORÍAS ====================
@app.route('/api/categorias/ingresos', methods=['GET', 'OPTIONS'])
def obtener_categorias_ingresos():
    """Obtener categorías de ingresos"""
    if request.method == 'OPTIONS':
        return jsonify({"success": True})
    
    try:
        print("📂 Obteniendo categorías de ingresos")
        categorias = modelo.obtener_categorias_ingresos()
        return jsonify({"success": True, "categorias": categorias})
    except Exception as e:
        print(f"❌ Error obteniendo categorías de ingresos: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/categorias/gastos', methods=['GET', 'OPTIONS'])
def obtener_categorias_gastos():
    """Obtener categorías de gastos"""
    if request.method == 'OPTIONS':
        return jsonify({"success": True})
    
    try:
        print("📂 Obteniendo categorías de gastos")
        categorias = modelo.obtener_categorias_gastos()
        return jsonify({"success": True, "categorias": categorias})
    except Exception as e:
        print(f"❌ Error obteniendo categorías de gastos: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== MANEJO DE ERRORES ====================
@app.errorhandler(404)
def not_found(error):
    """Manejar errores 404"""
    if request.path.startswith('/api/'):
        return jsonify({
            "success": False, 
            "error": "Endpoint no encontrado",
            "path": request.path
        }), 404
    else:
        # Para rutas no-API, intentar servir archivos estáticos
        try:
            return send_from_directory(app.static_folder, 'index.html')
        except:
            return jsonify({
                "success": False, 
                "error": "Página no encontrada"
            }), 404

@app.errorhandler(500)
def internal_error(error):
    """Manejar errores 500"""
    print(f"💥 Error 500: {error}")
    return jsonify({
        "success": False,
        "error": "Error interno del servidor"
    }), 500

# ==================== INICIALIZACIÓN ====================
if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Iniciando Servidor de Presupuesto Personal...")
    print("=" * 60)
    print("📁 Static folder:", os.path.abspath(app.static_folder))
    print("🌐 Frontend: http://localhost:5000")
    print("🔧 API Base:  http://localhost:5000/api")
    print("🏥 Health Check: http://localhost:5000/api/health")
    print("=" * 60)
    
    # Verificar que existe la carpeta static
    if not os.path.exists(app.static_folder):
        print(f"❌ ADVERTENCIA: No existe la carpeta '{app.static_folder}'")
        print("💡 Creando estructura de directorios...")
        os.makedirs(app.static_folder, exist_ok=True)
        os.makedirs(os.path.join(app.static_folder, 'js'), exist_ok=True)
        os.makedirs(os.path.join(app.static_folder, 'css'), exist_ok=True)
    
    print("✅ Servidor listo para recibir conexiones")
    print("=" * 60)
    
    app.run(
        debug=True,
        port=5000,
        host='0.0.0.0',
        threaded=True
    )