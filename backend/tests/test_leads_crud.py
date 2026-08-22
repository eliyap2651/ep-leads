from app.models.enums import Domain, RecordType, Region
from app.models.lead import Lead


async def _make_lead(db_session, **overrides):
    defaults = dict(title="מכרז ריהוט לבית ספר", record_type=RecordType.TENDER, domain=Domain.SCHOOL,
                     region=Region.CENTER, score=80)
    defaults.update(overrides)
    lead = Lead(**defaults)
    db_session.add(lead)
    await db_session.commit()
    await db_session.refresh(lead)
    return lead


async def test_list_leads_empty_by_default(client, auth_headers):
    resp = await client.get("/api/leads", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_create_and_list_lead(client, auth_headers, db_session):
    await _make_lead(db_session)
    resp = await client.get("/api/leads", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "מכרז ריהוט לבית ספר"


async def test_get_lead_detail(client, auth_headers, db_session):
    lead = await _make_lead(db_session)
    resp = await client.get(f"/api/leads/{lead.id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == str(lead.id)


async def test_get_missing_lead_returns_404(client, auth_headers):
    import uuid

    resp = await client.get(f"/api/leads/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404


async def test_update_lead_status_records_activity(client, auth_headers, db_session):
    lead = await _make_lead(db_session)
    resp = await client.patch(f"/api/leads/{lead.id}", json={"status": "contacted"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "contacted"

    activities_resp = await client.get(f"/api/leads/{lead.id}/activities", headers=auth_headers)
    assert any("contacted" in a["description"] for a in activities_resp.json())


async def test_filter_leads_by_domain(client, auth_headers, db_session):
    await _make_lead(db_session, title="בית ספר", domain=Domain.SCHOOL)
    await _make_lead(db_session, title="מלון", domain=Domain.HOTEL)
    resp = await client.get("/api/leads", params={"domain": "hotel"}, headers=auth_headers)
    assert resp.status_code == 200
    titles = [item["title"] for item in resp.json()]
    assert titles == ["מלון"]


async def test_add_and_list_note(client, auth_headers, db_session):
    lead = await _make_lead(db_session)
    resp = await client.post(f"/api/leads/{lead.id}/notes", json={"body": "לבדוק שוב מחר"}, headers=auth_headers)
    assert resp.status_code == 200
    list_resp = await client.get(f"/api/leads/{lead.id}/notes", headers=auth_headers)
    assert len(list_resp.json()) == 1
    assert list_resp.json()[0]["body"] == "לבדוק שוב מחר"
