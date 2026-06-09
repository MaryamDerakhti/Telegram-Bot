def test_imports():
    import app.models
    import app.services
    assert app.models.User.__tablename__ == "users"
