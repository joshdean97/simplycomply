from core import create_app

app = create_app(phase="production")

if __name__ == "__main__":
    app.run()
