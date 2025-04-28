from flask import Flask
from config import Config
from models import db
from routes import bp as api_bp
from flask_cors import CORS

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
CORS(app)

app.register_blueprint(api_bp)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("✅ Tables created!")
    app.run(debug=True)
