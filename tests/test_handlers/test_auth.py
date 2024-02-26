from tests.conftest import client


def test_registration():
    response_reg = client.post('/auth/register', json={
        "email": "user@example.com",
        "password": "strings123",
        "is_active": True,
        "is_superuser": False,
        "is_verified": False,
        "username": "String"
    })
    assert response_reg.status_code == 201


# def test_login(test_client, test_user):
#     response = test_client.post("/auth/jwt/login", data=test_user)
#     assert response.status_code == 200
#     token = response.json()["access_token"]
#     assert token is not None
#     return token
#
#
# def test_get_list(test_client, test_user):
#     token = test_login(test_client, test_user)
#     response = test_client.get("/profile", headers={"Cookie": f"U_CONF={token}"})
#     assert response.status_code == 200
#     assert response.json()["id"] == 1
