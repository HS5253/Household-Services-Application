
from flask import Flask, render_template
from backend.models import db

app = None

def setup_app():
    app = Flask(__name__,static_folder='static')
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///household_services.sqlite3"
    db.init_app(app)
    app.app_context().push()
    app.debug = True
    print("Household services app has started")

#Call the setup
setup_app()

from backend.controllers import *
if __name__ == "__main__":
    app.run(debug=True)

