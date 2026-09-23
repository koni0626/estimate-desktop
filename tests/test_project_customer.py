def test_customer_info_roundtrip_and_scope(clients):
    client = clients("staff")
    customer = client.get("/api/customers").json()[0]
    body = {"title": "相手先情報テスト", "customer_id": customer["id"], "customer_contact": "山田 太郎", "customer_corporate_number": "1234567890123"}
    result = client.post("/api/projects", json=body)
    assert result.status_code == 201, result.text
    project = result.json()
    path = f"/api/projects/{project['id']}"
    saved = client.get(path).json()
    assert saved["customer_name"] == customer["name"]
    assert saved["customer_contact"] == body["customer_contact"]
    assert saved["customer_corporate_number"] == body["customer_corporate_number"]
    for user in ("sales", "solo"):
        assert clients(user).get(path).status_code == 404
        assert clients(user).put(path, json={**body, "lock_version": 1}).status_code == 404
    updated = client.put(path, json={**body, "customer_contact": "佐藤 花子", "customer_corporate_number": "", "lock_version": 1})
    assert updated.status_code == 200
    assert updated.json()["customer_contact"] == "佐藤 花子"
    assert client.get(path).json()["customer_corporate_number"] == ""
    assert client.put(path, json={**body, "lock_version": 1}).status_code == 409
    assert next(c for c in client.get("/api/customers").json() if c["id"] == customer["id"]) == customer


def test_customer_info_optional_and_validation(clients):
    client = clients("solo")
    body = {"title": "個人事業主の案件", "customer_id": client.get("/api/customers").json()[0]["id"]}
    result = client.post("/api/projects", json=body)
    assert result.status_code == 201
    assert result.json()["customer_contact"] == ""
    assert result.json()["customer_corporate_number"] == ""
    for value in ("123", "T1234567890123", "１２３４５６７８９０１２３", "12345678901234"):
        assert client.post("/api/projects", json={**body, "customer_corporate_number": value}).status_code == 422
    assert client.post("/api/projects", json={**body, "customer_contact": "あ" * 121}).status_code == 422
