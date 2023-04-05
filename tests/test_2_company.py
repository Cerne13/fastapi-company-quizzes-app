from httpx import AsyncClient


async def test_create_company_unauthorized(ac: AsyncClient):
    payload = {
        "company_name": "company1",
        "description": "string"
    }
    response = await ac.post("/company/", json=payload)
    assert response.status_code == 403


async def test_bad_create_company__no_name(ac: AsyncClient, users_tokens):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    payload = {
        "company_name": "",
        "description": "description"
    }
    response = await ac.post("/company/", json=payload, headers=headers)
    assert response.status_code == 422


async def test_create_company_one(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    payload = {
        "company_name": "test_company_1",
        "description": "description_1"
    }
    response = await ac.post("/company/", json=payload, headers=headers)
    assert response.status_code == 201
    assert response.json().get("id") == 1


async def test_create_company_two(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }
    payload = {
        "company_name": "test_company_2",
    }
    response = await ac.post("/company/", json=payload, headers=headers)
    assert response.status_code == 201
    assert response.json().get("id") == 2


async def test_create_company_three(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test3@test.com']}",
    }
    payload = {
        "company_name": "test_company_3",
    }
    response = await ac.post("/company/", json=payload, headers=headers)
    assert response.status_code == 201
    assert response.json().get("id") == 3


async def test_get_all_companies(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/companies/", headers=headers)
    assert response.status_code == 200
    assert len(response.json().get('companies')) == 3


async def test_bad_get_company_by_id_not_found(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/company/4/", headers=headers)
    assert response.status_code == 404


async def test_get_company_by_id_one(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test3@test.com']}",
    }
    response = await ac.get("/company/1/", headers=headers)
    assert response.status_code == 200
    assert response.json().get("id") == 1
    assert response.json().get("company_name") == "test_company_1"
    assert response.json().get("description") == "description_1"
    assert response.json().get("owner_id") == 1


async def test_get_company_by_id_tw(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/company/2/", headers=headers)
    assert response.status_code == 200
    assert response.json().get("id") == 2
    assert response.json().get("company_name") == "test_company_2"
    assert response.json().get("description") == None
    assert response.json().get("owner_id") == 2


async def test_bad_update_company__unauthorized(ac: AsyncClient):
    payload = {
        "company_name": "company_name_1_NEW",
        "description": "description_1_NEW"
    }
    response = await ac.put("/company/1/", json=payload)
    assert response.status_code == 403


async def test_bad_update_company__not_found(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    payload = {
        "company_name": "company_name_1_NEW",
        "description": "description_1_NEW"
    }
    response = await ac.put("/company/100/", json=payload, headers=headers)
    assert response.status_code == 404


async def test_bad_update_company__not_your_company(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    payload = {
        "company_name": "company_name_2_NEW",
        "description": "description_2_NEW"
    }
    response = await ac.put("/company/2/", json=payload, headers=headers)
    assert response.status_code == 403


async def test_update_company(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    payload = {
        "company_name": "company_name_1_NEW",
        "description": "description_1_NEW"
    }
    response = await ac.put("/company/1/", json=payload, headers=headers)
    assert response.status_code == 200


async def test_get_company_by_id_one_updated(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/company/1/", headers=headers)
    assert response.status_code == 200
    assert response.json().get("id") == 1
    assert response.json().get("company_name") == "company_name_1_NEW"
    assert response.json().get("description") == "description_1_NEW"
    assert response.json().get("owner_id") == 1


async def test_bad_delete_company_one__user_not_owner(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test2@test.com']}",
    }
    response = await ac.delete("/company/1/", headers=headers)
    assert response.status_code == 403


async def test_delete_company_three(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test3@test.com']}",
    }
    response = await ac.delete("/company/3/", headers=headers)
    assert response.status_code == 200


async def test_get_all_companies_after_not_delete(users_tokens, ac: AsyncClient):
    headers = {
        "Authorization": f"Bearer {users_tokens['test1@test.com']}",
    }
    response = await ac.get("/companies/", headers=headers)
    assert response.status_code == 200
    assert len(response.json().get('companies')) == 2