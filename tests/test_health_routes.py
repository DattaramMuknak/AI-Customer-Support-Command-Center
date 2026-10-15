from app.api.health_routes import health


def test_health_returns_ok_status():
    response = health()

    assert response["status"] == "ok"
    assert response["app"]
    assert response["version"]
