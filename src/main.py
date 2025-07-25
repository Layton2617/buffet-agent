import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.conversation import db
from src.routes.buffett_routes import buffett_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'buffett-agent-secret-key-2025'

CORS(app, origins="*")

app.register_blueprint(buffett_bp, url_prefix='/api')

if os.environ.get('RENDER'):
    db_path = '/tmp/app.db'
else:
    db_dir = os.path.join(os.path.dirname(__file__), 'database')
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, 'app.db')

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    try:
        db.create_all()
        print(f"Database initialized successfully at: {db_path}")
    except Exception as e:
        print(f"Database initialization error: {e}")
        app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
        db.init_app(app)
        with app.app_context():
            db.create_all()
        print("Using in-memory database as fallback")

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
