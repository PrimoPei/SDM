import os
from fastapi import Depends, FastAPI
import sqlite3
import requests
import uvicorn
from pathlib import Path
import json

app = FastAPI()
LIVEBLOCKS_SECRET = os.environ.get("LIVEBLOCKS_SECRET")


def get_db():
    db = sqlite3.connect(Path("./rooms.db"), check_same_thread=False)
    db.execute("CREATE TABLE IF NOT EXISTS rooms (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, room_id TEXT NOT NULL, users_count INTEGER NOT NULL DEFAULT 0)")
    print("Connected to database")
    db.commit()
    db.row_factory = sqlite3.Row
    try:
        yield db
    except Exception:
        db.rollback()
    finally:
        db.close()


app = FastAPI()

rooms = ["sd-multiplayer-room-" + str(i) for i in range(0, 20)]


@app.get("/")
async def read_root(db: sqlite3.Connection = Depends(get_db)):
    out = db.execute("SELECT * FROM rooms").fetchall()
    print(out)
    return out


@app.get("/create-rooms")
async def create_room(db: sqlite3.Connection = Depends(get_db)):
    for room_id in rooms:
        print(room_id)
        createRoom(room_id,  db)
    all = db.execute("SELECT * FROM rooms").fetchall()
    return all


def createRoom(room_id, db):
    payload = {"id": room_id, "defaultAccesses": ["room:write"]}

    response = requests.post(f"https://api.liveblocks.io/v2/rooms",
                             headers={"Authorization": f"Bearer {LIVEBLOCKS_SECRET}"}, json=payload)
    # if response.status_code == 200:
    data = response.json()
    print(data)
    if "error" in data and data["error"] == "ROOM_ALREADY_EXISTS":
        print("Room already exists")

    cursor = db.cursor()
    cursor.execute("INSERT INTO rooms (room_id) VALUES (?)", (room_id,))
    db.commit()
    print("Room created")

    print("Created room", room_id)
    return True


def generateAuthToken():
    response = requests.get(f"https://liveblocks.io/api/authorize",
                            headers={"Authorization": f"Bearer {LIVEBLOCKS_SECRET}"})
    if response.status_code == 200:
        data = response.json()
        return data["token"]
    else:
        raise Exception(response.status_code, response.text)


def get_room_count(room_id: str, jwtToken: str = ''):
    print("Getting room count" + room_id)
    response = requests.get(
        f"https://liveblocks.net/api/v1/room/{room_id}/users", headers={"Authorization": f"Bearer {jwtToken}", "Content-Type": "application/json"})
    if response.status_code == 200:
        res = response.json()
        if "data" in res:
            return len(res["data"])
        else:
            return 0
    raise Exception("Error getting room count")


@app.get("/sync-rooms")
async def sync_rooms(db: sqlite3.Connection = Depends(get_db)):
    try:
        jwtToken = generateAuthToken()
        rooms = db.execute("SELECT * FROM rooms").fetchall()
        for row in rooms:
            room_id = row["room_id"]
            users_count = get_room_count(room_id, jwtToken)
            print("Updating room", room_id, "with", users_count, "users")
            cursor = db.cursor()
            cursor.execute(
                "UPDATE rooms SET users_count = ? WHERE room_id = ?", (users_count, room_id))
            db.commit()
        data = db.execute("SELECT * FROM rooms").fetchall()
        return data
    except Exception as e:
        print(e)
        return {"error": str(e)}


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", log_level="debug", reload=True)
