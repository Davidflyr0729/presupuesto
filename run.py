from app import app

if __name__ == '__main__':
    print("🚀 Iniciando Servidor de Presupuesto Personal (PRODUCCIÓN)...")
    print("🌐 Servidor corriendo en: http://localhost:5000")
    print("=" * 50)
    
    app.run(
        debug=False,
        port=5000,
        host='0.0.0.0',
        threaded=True
    )