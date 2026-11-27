import _env  # noqa: F401  (debe ir antes de importar la app)
from app import app


def login(client, username, password):
    page = client.get("/login").get_data(as_text=True)
    token = page.split('name="csrf_token" value="')[1].split('"')[0]
    return client.post("/login", data={"username": username, "password": password, "csrf_token": token})


def new_client(username=None, password=None):
    app.config["TESTING"] = True
    client = app.test_client()
    if username:
        login(client, username, password)
    return client
