from core import create_app

app = create_app(phase="development")

if __name__ == "__main__":
    app.run()
