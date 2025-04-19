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
    app.run(debug=True)
