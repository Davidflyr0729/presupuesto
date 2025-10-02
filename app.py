from flask import Flask
from config import Config

def create_app():
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    app.config.from_object(Config)
    
    # Importar y registrar controladores
    from controllers.auth_controller import auth_controller
    from controllers.dashboard_controller import dashboard_controller
    from controllers.income_controller import income_controller
    from controllers.expense_controller import expense_controller
    from controllers.budget_controller import budget_controller
    from controllers.savings_controller import savings_controller  # ← NUEVO
    
    app.register_blueprint(auth_controller.bp)
    app.register_blueprint(dashboard_controller.bp)
    app.register_blueprint(income_controller.bp)
    app.register_blueprint(expense_controller.bp)
    app.register_blueprint(budget_controller.bp)
    app.register_blueprint(savings_controller.bp)  # ← NUEVO
    
    # Context processor para fechas
    @app.context_processor
    def utility_processor():
        from datetime import datetime
        return {'now': datetime.now()}
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)