from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'my-secret-key-12345'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)

    # Register Blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.transactions import transactions_bp
    from app.routes.budgets import budgets_bp

    app.register_blueprint(main_bp)                          # Mounts at /
    app.register_blueprint(auth_bp, url_prefix='/auth')     # Mounts at /auth
    app.register_blueprint(transactions_bp, url_prefix='/transactions')  # Mounts at /transactions
    app.register_blueprint(budgets_bp, url_prefix='/budgets')  # Mounts at /budgets

    with app.app_context():
        from app import models
        db.create_all()

    return app