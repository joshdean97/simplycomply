from core import create_app

if __name__ == "__main__":
    app = create_app(phase="development")
    app.run(debug=True, port=8000)
