from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User


async def _make_agent(db_session, email="agent@test.local"):
    user = User(email=email, hashed_password=hash_password("AgentPass123!"), full_name="Agent", role=UserRole.SALES_AGENT)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _login(client, email, password):
    resp = await client.post("/api/auth/login", json={"email": email, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_sales_agent_cannot_create_users(client, db_session):
    await _make_agent(db_session)
    headers = await _login(client, "agent@test.local", "AgentPass123!")
    resp = await client.post(
        "/api/auth/users",
        json={"email": "new@test.local", "password": "Password123!", "full_name": "New", "role": "viewer"},
        headers=headers,
    )
    assert resp.status_code == 403


async def test_admin_can_create_users(client, auth_headers):
    resp = await client.post(
        "/api/auth/users",
        json={"email": "new2@test.local", "password": "Password123!", "full_name": "New", "role": "viewer"},
        headers=auth_headers,
    )
    assert resp.status_code == 200


async def test_sales_agent_only_sees_assigned_leads(client, db_session):
    from app.models.enums import RecordType
    from app.models.lead import Lead

    agent = await _make_agent(db_session)
    other_agent = await _make_agent(db_session, email="other@test.local")

    mine = Lead(title="שלי", record_type=RecordType.TENDER, assigned_to_id=agent.id)
    not_mine = Lead(title="לא שלי", record_type=RecordType.TENDER, assigned_to_id=other_agent.id)
    db_session.add_all([mine, not_mine])
    await db_session.commit()

    headers = await _login(client, "agent@test.local", "AgentPass123!")
    resp = await client.get("/api/leads", headers=headers)
    titles = [item["title"] for item in resp.json()]
    assert titles == ["שלי"]


async def test_viewer_cannot_delete_lead(client, db_session):
    from app.models.enums import RecordType
    from app.models.lead import Lead

    viewer = User(email="viewer@test.local", hashed_password=hash_password("ViewerPass123!"), full_name="Viewer", role=UserRole.VIEWER)
    db_session.add(viewer)
    lead = Lead(title="ליד לבדיקה", record_type=RecordType.TENDER)
    db_session.add(lead)
    await db_session.commit()
    await db_session.refresh(lead)

    headers = await _login(client, "viewer@test.local", "ViewerPass123!")
    resp = await client.delete(f"/api/leads/{lead.id}", headers=headers)
    assert resp.status_code == 403
