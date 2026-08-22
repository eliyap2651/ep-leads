from app.models.enums import RecordType
from app.models.lead import Lead


async def test_export_csv_contains_lead_title(client, auth_headers, db_session):
    lead = Lead(title="מכרז ריהוט לבדיקה", record_type=RecordType.TENDER, score=70)
    db_session.add(lead)
    await db_session.commit()

    resp = await client.get("/api/export/leads.csv", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert "מכרז ריהוט לבדיקה" in resp.text


async def test_export_xlsx_returns_binary(client, auth_headers, db_session):
    lead = Lead(title="מכרז נוסף", record_type=RecordType.TENDER, score=50)
    db_session.add(lead)
    await db_session.commit()

    resp = await client.get("/api/export/leads.xlsx", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.content[:2] == b"PK"  # xlsx is a zip archive
