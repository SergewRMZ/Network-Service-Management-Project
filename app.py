from flask import Flask, jsonify

from routes.users import users_bp
from routes.routers import routers_bp
from routes.topology import topology_bp

app = Flask(__name__)

app.register_blueprint(users_bp, url_prefix="/usuarios")
app.register_blueprint(routers_bp, url_prefix="/routers")
app.register_blueprint(topology_bp, url_prefix="/topologia")

if __name__ == '__main__':
    app.run(debug=True)