import sqlite3
import uuid

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.auth import hash_password, verify_password, make_token, current_user
# from app.config import GUEST_FREE_USES
from app.config import GUEST_FREE_USES, USER_DAILY_LIMIT
from app.db import init_db, get_conn
from app.graph.builder import build_graph
#from app.schemas import ResearchRequest, SignupRequest, LoginRequest
from app.schemas import (ResearchRequest, SignupRequest, LoginRequest,
                         NameRequest, PasswordRequest, DeleteRequest, RelatedRequest)
from app.services.topics import CURATED, suggest_topics, related_questions 
# from app.services.topics import CURATED, suggest_topics

app = FastAPI(title="Research Agent")
init_db()
graph = build_graph()


@app.post("/api/signup")
def signup(body: SignupRequest):
    email = body.email.strip().lower()
    if "@" not in email or len(body.password) < 8 or not body.name.strip():
        raise HTTPException(400, "Enter a name, a valid email, and a password of 8+ characters.")
    try:
        with get_conn() as c:
            c.execute("INSERT INTO users(name, email, password_hash) VALUES (?,?,?)",
                      (body.name.strip(), email, hash_password(body.password)))
    except sqlite3.IntegrityError:
        raise HTTPException(409, "This email is already registered.")
    return {"ok": True}


@app.post("/api/login")
def login(body: LoginRequest, response: Response):
    with get_conn() as c:
        row = c.execute("SELECT * FROM users WHERE email=?", (body.email.strip().lower(),)).fetchone()
    if not row or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(401, "Wrong email or password.")
    response.set_cookie("token", make_token(row["id"]), httponly=True, samesite="lax", max_age=60 * 60 * 24 * 7)
    return {"ok": True, "name": row["name"]}


@app.post("/api/logout")
def logout(response: Response):
    response.delete_cookie("token")
    return {"ok": True}


@app.get("/api/me")
def me(request: Request):
    user = current_user(request)
    if not user:
        raise HTTPException(401, "Not logged in")
    return dict(user)


@app.post("/api/research")
def research(req: ResearchRequest, request: Request):
    user = current_user(request)
    new_guest_id = None
    if user:
       with get_conn() as c:
            used = c.execute(
                "SELECT COUNT(*) FROM history WHERE user_id=? AND created_at >= datetime('now','-1 day')",
                (user["id"],),
            ).fetchone()[0]
    if used >= USER_DAILY_LIMIT:
            return JSONResponse({"detail": "daily_limit"}, status_code=429)

    if not user:   # guest: limited free uses
        guest_id = request.cookies.get("guest_id") or uuid.uuid4().hex
        with get_conn() as c:
            c.execute("INSERT OR IGNORE INTO guests(guest_id, uses) VALUES (?, 0)", (guest_id,))
            uses = c.execute("SELECT uses FROM guests WHERE guest_id=?", (guest_id,)).fetchone()["uses"]
            if uses >= GUEST_FREE_USES:
                return JSONResponse({"detail": "guest_limit"}, status_code=403)
            c.execute("UPDATE guests SET uses = uses + 1 WHERE guest_id=?", (guest_id,))
        if not request.cookies.get("guest_id"):
            new_guest_id = guest_id

    uid = user["id"] if user else None
    def stream():
        state = req.model_dump()
        final = {}
        for update in graph.stream(state, stream_mode="updates"):
            for node, out in update.items():
                yield f"{node} done\n"
                final.update(out)
        #yield "\n---REPORT---\n"
        #yield final.get("report", "No report generated.")
        report = final.get("report", "No report generated.")
        if uid and final.get("report"):
            with get_conn() as c:
                c.execute(
                    "INSERT INTO history(user_id, mode, input, length, style, report) VALUES (?,?,?,?,?,?)",
                    (uid, req.mode, req.input, req.length, req.style, report),
                )
        yield "\n---REPORT---\n"
        yield report

    resp = StreamingResponse(stream(), media_type="text/plain")
    if new_guest_id:
        resp.set_cookie("guest_id", new_guest_id, httponly=True, samesite="lax", max_age=60 * 60 * 24 * 365)
    return resp

def _require_user(request: Request):
    user = current_user(request)
    if not user:
        raise HTTPException(401, "Not logged in")
    return user

_sugg_cache = {}


@app.get("/api/trending")
def trending():
    # only topics researched by 2+ different users are shown (privacy)
    with get_conn() as c:
        rows = c.execute(
            "SELECT input, COUNT(DISTINCT user_id) AS n FROM history "
            "WHERE mode='topic' AND length(input) < 100 "
            "GROUP BY lower(input) HAVING n >= 2 ORDER BY n DESC LIMIT 5").fetchall()
    return {"curated": CURATED, "popular": [{"topic": r["input"], "users": r["n"]} for r in rows]}


@app.get("/api/suggestions")
def suggestions(request: Request):
    user = _require_user(request)
    with get_conn() as c:
        rows = c.execute(
            "SELECT mode, input, report FROM history WHERE user_id=? ORDER BY id DESC LIMIT 5",
            (user["id"],)).fetchall()
    starter = [x["topic"] for x in CURATED[:5]]
    if not rows:
        return {"personal": False, "topics": starter}

    key = tuple(r["input"] for r in rows)
    cached = _sugg_cache.get(user["id"])
    if cached and cached[0] == key:
        return {"personal": True, "topics": cached[1]}

    recent = [r["input"] if r["mode"] == "topic" else r["report"][:200] for r in rows]
    try:
        topics = suggest_topics(recent)
    except Exception:
        return {"personal": False, "topics": starter}
    _sugg_cache[user["id"]] = (key, topics)
    return {"personal": True, "topics": topics}

@app.get("/api/history")
def history(request: Request):
    user = _require_user(request)
    with get_conn() as c:
        rows = c.execute(
            "SELECT id, mode, input, length, style, created_at FROM history "
            "WHERE user_id=? ORDER BY id DESC LIMIT 50", (user["id"],)).fetchall()
    return [dict(r) for r in rows]


@app.get("/api/history/{item_id}")
def history_item(item_id: int, request: Request):
    user = _require_user(request)
    with get_conn() as c:
        row = c.execute("SELECT * FROM history WHERE id=? AND user_id=?", (item_id, user["id"])).fetchone()
    if not row:
        raise HTTPException(404, "Not found")
    return dict(row)



@app.delete("/api/history/{item_id}")
def history_delete(item_id: int, request: Request):
    user = _require_user(request)
    with get_conn() as c:
        c.execute("DELETE FROM history WHERE id=? AND user_id=?", (item_id, user["id"]))
    return {"ok": True}

@app.post("/api/history/{item_id}/save")
def history_save(item_id: int, request: Request):
    user = _require_user(request)
    with get_conn() as c:
        row = c.execute("SELECT saved FROM history WHERE id=? AND user_id=?", (item_id, user["id"])).fetchone()
        if not row:
            raise HTTPException(404, "Not found")
        new = 0 if row["saved"] else 1
        c.execute("UPDATE history SET saved=? WHERE id=?", (new, item_id))
    return {"saved": bool(new)}


@app.get("/api/saved")
def saved_list(request: Request):
    user = _require_user(request)
    with get_conn() as c:
        rows = c.execute(
            "SELECT id, mode, input, length, created_at FROM history "
            "WHERE user_id=? AND saved=1 ORDER BY id DESC", (user["id"],)).fetchall()
    return [dict(r) for r in rows]


@app.get("/api/usage")
def usage(request: Request):
    user = _require_user(request)
    with get_conn() as c:
        today = c.execute("SELECT COUNT(*) FROM history WHERE user_id=? AND created_at >= datetime('now','-1 day')",
                          (user["id"],)).fetchone()[0]
        total = c.execute("SELECT COUNT(*) FROM history WHERE user_id=?", (user["id"],)).fetchone()[0]
        saved = c.execute("SELECT COUNT(*) FROM history WHERE user_id=? AND saved=1", (user["id"],)).fetchone()[0]
    return {"today": today, "limit": USER_DAILY_LIMIT, "total": total, "saved": saved}


@app.post("/api/settings/name")
def set_name(body: NameRequest, request: Request):
    user = _require_user(request)
    name = body.name.strip()
    if not name:
        raise HTTPException(400, "Name cannot be empty.")
    with get_conn() as c:
        c.execute("UPDATE users SET name=? WHERE id=?", (name, user["id"]))
    return {"ok": True, "name": name}


@app.post("/api/settings/password")
def set_password(body: PasswordRequest, request: Request):
    user = _require_user(request)
    with get_conn() as c:
        row = c.execute("SELECT password_hash FROM users WHERE id=?", (user["id"],)).fetchone()
        if not verify_password(body.current, row["password_hash"]):
            raise HTTPException(401, "Current password is wrong.")
        if len(body.new) < 8:
            raise HTTPException(400, "New password must be 8+ characters.")
        c.execute("UPDATE users SET password_hash=? WHERE id=?", (hash_password(body.new), user["id"]))
    return {"ok": True}


@app.post("/api/account/delete")
def delete_account(body: DeleteRequest, request: Request, response: Response):
    user = _require_user(request)
    with get_conn() as c:
        row = c.execute("SELECT password_hash FROM users WHERE id=?", (user["id"],)).fetchone()
        if not verify_password(body.password, row["password_hash"]):
            raise HTTPException(401, "Password is wrong.")
        c.execute("DELETE FROM history WHERE user_id=?", (user["id"],))
        c.execute("DELETE FROM users WHERE id=?", (user["id"],))
    response.delete_cookie("token")
    return {"ok": True}


@app.post("/api/related")
def related(body: RelatedRequest, request: Request):
    _require_user(request)
    try:
        return {"questions": related_questions(body.text[:3000])}
    except Exception:
        return {"questions": []}

app.mount("/", StaticFiles(directory="app/static", html=True), name="static")