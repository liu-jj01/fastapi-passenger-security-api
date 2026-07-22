import json

import pytest
from fastapi.testclient import TestClient

from app import database
from app.config import settings
from app.main import app


@pytest.fixture(autouse=True)
def use_temporary_database(tmp_path):
    test_db = tmp_path / "test_passenger.db"
    database.configure_database(
        f"sqlite:///{test_db.as_posix()}"
    )
    database.init_database()


@pytest.fixture
def client():
    with TestClient(
        app,
        headers={
            "X-API-Key": settings.api_key,
        },
    ) as test_client:
        yield test_client


def make_request_body(
    *,
    flt_no="CA1234T",
    flt_date="2026-07-20",
    cert_no="110101198410063535",
    name="姚明",
    seat="12A",
    remark=None,
):
    passenger = {
        "fltNo": flt_no,
        "fltDate": flt_date,
        "brdno": "1",
        "dept": "CTU",
        "seat": seat,
        "certType": "NI",
        "certNo": cert_no,
        "psrName": name,
        "psrCName": "YAOMING",
        "suspect": "0",
        "monitortips": "......",
        "securityResult": "0",
        "bagId": "3999782710",
        "bagStatus": "C",
        "bagrStatus": "N",
        "cbagStatus": "C",
        "sbagStatus": "C",
        "face": ".................",
    }

    if remark is not None:
        passenger["remark"] = remark

    return {
        "mainType": "SCRC",
        "subType": "PSIF",
        "sender": "SECURITYCHECK",
        "message": json.dumps(passenger, ensure_ascii=False),
    }


def create_passenger(client, **kwargs):
    return client.post(
        "/security/passenger",
        json=make_request_body(**kwargs),
    )


def test_create_passenger_success(client):
    response = create_passenger(client)

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == "0000"
    assert body["data"]["passenger"]["fltNo"] == "CA1234T"
    assert body["data"]["passenger"]["seat"] == "12A"
    assert body["data"]["passenger"]["remark"] is None
    assert body["data"]["total"] == 1


def test_duplicate_passenger_returns_409(client):
    first_response = create_passenger(client)
    second_response = create_passenger(client)

    assert first_response.status_code == 200
    assert second_response.status_code == 409
    assert second_response.json() == {
        "code": "4009",
        "message": "该旅客在该航班日期的数据已经存在",
        "data": None,
    }


def test_query_single_passenger(client):
    create_passenger(client, flt_no="MU2468T", seat="16B")

    response = client.get(
        "/security/passenger",
        params={
            "certNo": "110101198410063535",
            "fltNo": "MU2468T",
            "fltDate": "2026-07-20",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == "0000"
    assert body["data"]["fltNo"] == "MU2468T"
    assert body["data"]["seat"] == "16B"


def test_query_missing_passenger_returns_404(client):
    response = client.get(
        "/security/passenger",
        params={
            "certNo": "110101198410063535",
            "fltNo": "AA0000",
            "fltDate": "2026-07-20",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "code": "4004",
        "message": "没有找到对应的旅客航班数据",
        "data": None,
    }


def test_update_passenger(client):
    create_passenger(client, flt_no="CZ1357T", seat="15A")

    response = client.put(
        "/security/passenger",
        params={
            "certNo": "110101198410063535",
            "fltNo": "CZ1357T",
            "fltDate": "2026-07-20",
        },
        json={
            "seat": "18C",
            "securityResult": "1",
            "bagStatus": "N",
        },
    )

    assert response.status_code == 200
    updated = response.json()["data"]
    assert updated["seat"] == "18C"
    assert updated["securityResult"] == "1"
    assert updated["bagStatus"] == "N"


def test_delete_passenger(client):
    create_passenger(client, flt_no="CA5678T")

    params = {
        "certNo": "110101198410063535",
        "fltNo": "CA5678T",
        "fltDate": "2026-07-20",
    }
    delete_response = client.delete("/security/passenger", params=params)

    assert delete_response.status_code == 200
    assert client.get("/security/passenger", params=params).status_code == 404


def test_invalid_flight_date_is_rejected(client):
    response = create_passenger(
        client,
        flt_no="CA9999T",
        flt_date="2026-02-30",
    )

    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "4000"
    assert body["message"] == "请求处理失败"
    assert any(
        "航班日期不是有效日期" in error["msg"]
        for error in body["data"]
    )


def test_missing_query_parameters_returns_422(client):
    response = client.get("/security/passenger")

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "4220"
    assert len(body["data"]) == 3


def test_passenger_list_pagination_filter_and_sort(client):
    create_passenger(client, flt_no="CA1234T", name="姚明", seat="12A")
    create_passenger(client, flt_no="CA5678T", name="姚明", seat="16B")
    create_passenger(client, flt_no="MU2468T", name="张三", seat="17C")
    create_passenger(client, flt_no="CZ1357T", name="李四", seat="18D")

    first_page = client.get(
        "/security/passengers",
        params={
            "page": 1,
            "pageSize": 2,
            "sortBy": "id",
            "sortOrder": "asc",
        },
    )
    first_data = first_page.json()["data"]

    assert first_page.status_code == 200
    assert first_data["total"] == 4
    assert first_data["totalPages"] == 2
    assert [item["fltNo"] for item in first_data["list"]] == [
        "CA1234T",
        "CA5678T",
    ]

    name_filter = client.get(
        "/security/passengers",
        params={"psrName": "姚"},
    )
    filtered_data = name_filter.json()["data"]
    assert filtered_data["total"] == 2


def test_invalid_sort_parameter_returns_422(client):
    response = client.get(
        "/security/passengers",
        params={"sortBy": "seat"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "4220"


def test_create_query_and_list_remark(client):
    create_response = create_passenger(
        client,
        flt_no="HO2026T",
        remark="需要人工复核",
    )

    assert create_response.status_code == 200
    assert (
        create_response.json()["data"]["passenger"]["remark"]
        == "需要人工复核"
    )

    params = {
        "certNo": "110101198410063535",
        "fltNo": "HO2026T",
        "fltDate": "2026-07-20",
    }
    query_response = client.get(
        "/security/passenger",
        params=params,
    )
    assert query_response.json()["data"]["remark"] == "需要人工复核"

    list_response = client.get(
        "/security/passengers",
        params={"fltNo": "HO2026T"},
    )
    passenger_list = list_response.json()["data"]["list"]
    assert len(passenger_list) == 1
    assert passenger_list[0]["remark"] == "需要人工复核"


def test_update_and_clear_remark(client):
    create_passenger(
        client,
        flt_no="ZH2026T",
        remark="初始备注",
    )

    params = {
        "certNo": "110101198410063535",
        "fltNo": "ZH2026T",
        "fltDate": "2026-07-20",
    }

    update_response = client.put(
        "/security/passenger",
        params=params,
        json={"remark": "备注已更新"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["remark"] == "备注已更新"

    clear_response = client.put(
        "/security/passenger",
        params=params,
        json={"remark": None},
    )
    assert clear_response.status_code == 200
    assert clear_response.json()["data"]["remark"] is None

    query_response = client.get(
        "/security/passenger",
        params=params,
    )
    assert query_response.json()["data"]["remark"] is None

def test_missing_api_key_returns_401():
    with TestClient(app) as unauthorized_client:
        response = unauthorized_client.get(
            "/security/passengers"
        )

    assert response.status_code == 401
    assert response.json() == {
        "code": "4001",
        "message": "缺少 X-API-Key 请求头",
        "data": None,
    }


def test_invalid_api_key_returns_403():
    with TestClient(
        app,
        headers={
            "X-API-Key": "wrong-api-key",
        },
    ) as unauthorized_client:
        response = unauthorized_client.get(
            "/security/passengers"
        )

    assert response.status_code == 403
    assert response.json() == {
        "code": "4003",
        "message": "API Key 不正确",
        "data": None,
    }