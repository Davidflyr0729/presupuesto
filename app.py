from flask import Flask
import os
from config import Config

def create_app():
    app = Flask(__name__, 
                template_folder='templates',  # ← Especificar carpeta de templates
                static_folder='static')       # ← Especificar carpeta static
    
    app.config.from_object(Config)
    
    # Importar y registrar controladores
    from controllers.auth_controller import auth_controller
    from controllers.dashboard_controller import dashboard_controller
    from controllers.income_controller import income_controller
    
    app.register_blueprint(auth_controller.bp)
    app.register_blueprint(dashboard_controller.bp)
    app.register_blueprint(income_controller.bp)
    
    # Ruta de prueba
    @app.route('/test')
    def test():
        return "¡La aplicación está funcionando!"
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Verificar que las carpetas existen
    print("Template folder:", app.template_folder)
    print("Static folder:", app.static_folder)
    
    app.run(debug=True, port=5000)