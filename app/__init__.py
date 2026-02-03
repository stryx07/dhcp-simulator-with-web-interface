from flask import Flask

def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = 'dev_key_for_academic_project'
    
    from .routes import main
    app.register_blueprint(main)
    
    return app
