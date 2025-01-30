from core import create_app
from core.functions import create_database

if __name__ == "__main__":
    app = create_app(phase="development")
    create_database(app)
    app.run(debug=True, port=8000)
