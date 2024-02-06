from fastapi.testclient import TestClient
from src.profile.router import router

client = TestClient(app=router)


def test_get_profile_page():
    response = client.get("/profile")
    assert response.status_code == 200
