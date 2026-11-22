from app.security import hash_password, verify_password


def test_password_hash_roundtrip():
    h = hash_password("hunter2hunter2")
    assert verify_password("hunter2hunter2", h)
    assert not verify_password("wrong", h)


def test_requires_login(client):
    assert client.get("/api/bootstrap").status_code == 401
    assert client.put("/api/notes", json=[]).status_code == 401


def test_signup_login_logout(client):
    body = {"name": "Ali", "email": "ali@example.com", "password": "supersecret1"}
    assert client.post("/api/auth/signup", json=body).status_code == 200
    assert client.post("/api/auth/signup", json=body).status_code == 409        # duplicate email
    client.post("/api/auth/logout")
    assert client.get("/api/bootstrap").status_code == 401
    assert client.post("/api/auth/login", json={"email": "ali@example.com", "password": "nope"}).status_code == 401
    assert client.post("/api/auth/login", json={"email": "ALI@example.com", "password": "supersecret1"}).status_code == 200
    assert client.get("/api/bootstrap").json()["session"]["name"] == "Ali"


def test_short_password_rejected(client):
    r = client.post("/api/auth/signup", json={"name": "X", "email": "x@example.com", "password": "short"})
    assert r.status_code == 422


def test_guest(client):
    r = client.post("/api/auth/guest")
    assert r.status_code == 200 and r.json()["guest"] == 1
    assert client.get("/api/bootstrap").status_code == 200


def test_subjects_notes_and_cascade(user):
    assert user.put("/api/subjects", json=[{"id": "s1", "name": "Biology"}, {"id": "s2", "name": "Maths"}]).status_code == 200
    note = {"id": "n1", "sid": "s1", "title": "Cells", "body": "mitochondria", "cr": 1, "upd": 2}
    assert user.put("/api/notes", json=[note]).status_code == 200
    # a note pointing to an unknown subject is refused
    bad = dict(note, id="n2", sid="nope")
    assert user.put("/api/notes", json=[note, bad]).status_code == 422
    # re-sending the same subjects must NOT wipe the notes
    user.put("/api/subjects", json=[{"id": "s1", "name": "Biology"}, {"id": "s2", "name": "Maths"}])
    assert len(user.get("/api/bootstrap").json()["notes"]) == 1
    # removing the subject removes its notes
    user.put("/api/subjects", json=[{"id": "s2", "name": "Maths"}])
    data = user.get("/api/bootstrap").json()
    assert [s["id"] for s in data["subs"]] == ["s2"] and data["notes"] == []


def test_events_goals_focus_prefs(user):
    ev = [{"id": "e1", "title": "Exam", "date": "2026-12-01", "time": "09:00", "type": "exam"}]
    assert user.put("/api/events", json=ev).status_code == 200
    assert user.put("/api/events", json=[dict(ev[0], type="party")]).status_code == 422
    goals = [{"id": "g1", "t": "Read ch.4", "done": 0}, {"id": "g2", "t": "Sleep", "done": 1}]
    assert user.put("/api/goals", json=goals).status_code == 200
    assert user.put("/api/focus", json={"2026-11-21": {"m": 50, "n": 2}}).status_code == 200
    assert user.put("/api/focus", json={"yesterday": {"m": 1, "n": 1}}).status_code == 422
    assert user.patch("/api/me/prefs", json={"theme": "dark", "fmt": "roadmap", "timer": {"f": 30, "b": 10},
                                             "meet": "meet.google.com/abc-defg-hij"}).status_code == 200
    d = user.get("/api/bootstrap").json()
    assert d["events"] == ev and [g["done"] for g in d["goals"]] == [0, 1]
    assert d["focus"] == {"2026-11-21": {"m": 50, "n": 2}}
    assert d["theme"] == "dark" and d["fmt"] == "roadmap" and d["timer"] == {"f": 30, "b": 10}


def test_users_are_isolated(client):
    client.post("/api/auth/signup", json={"name": "A", "email": "a@example.com", "password": "supersecret1"})
    client.put("/api/goals", json=[{"id": "g1", "t": "secret goal", "done": 0}])
    client.post("/api/auth/logout")
    client.post("/api/auth/signup", json={"name": "B", "email": "b@example.com", "password": "supersecret1"})
    assert client.get("/api/bootstrap").json()["goals"] == []


def test_lost_sample_history_and_delete(user):
    r = user.post("/api/lost", data={"format": "roadmap"})
    assert r.status_code == 200
    item = r.json()
    assert item["s"] is True and item["f"] == "roadmap" and item["c"]["steps"]
    assert user.post("/api/lost", data={"format": "bogus"}).status_code == 422
    assert len(user.get("/api/bootstrap").json()["hist"]) == 1
    assert user.delete(f"/api/summaries/{item['id']}").status_code == 200
    assert user.get("/api/bootstrap").json()["hist"] == []


def test_lost_with_audio_but_no_ai_key_is_an_error_not_fake_data(user):
    r = user.post("/api/lost", data={"format": "paragraph"}, files={"audio": ("a.webm", b"123", "audio/webm")})
    assert r.status_code == 502


def test_lost_with_text_is_saved_as_real_content(user):
    r = user.post("/api/lost", data={"text": "  Today we saw photosynthesis.  ", "title": "Biology"})
    assert r.status_code == 200
    item = r.json()
    assert item["s"] is False and item["t"] == "Biology" and item["f"] == "paragraph"
    assert item["c"]["p"] == "Today we saw photosynthesis."
    assert len(user.get("/api/bootstrap").json()["hist"]) == 1
    assert user.post("/api/lost", data={"text": "x" * 20001}).status_code == 413


def test_cross_origin_write_blocked(user):
    r = user.put("/api/goals", json=[], headers={"Origin": "https://evil.example"})
    assert r.status_code == 403


def test_delete_account(user):
    assert user.delete("/api/me").status_code == 200
    assert user.get("/api/bootstrap").status_code == 401
