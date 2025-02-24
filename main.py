from flask import Flask, render_template, redirect, request, session, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

app = Flask(__name__)
app.config["SECRET_KEY"] = "" #some key  
socketio = SocketIO(app)

rooms = {}

def generate_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        if code not in rooms:
            break
    return code

@app.route("/", methods=["GET", "POST"])
def home():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)
        
        if not name:
            return render_template("home.html", error="Please enter a name.", name=name, code=code)

        if create != False:
            room = generate_code(4)
            rooms[room] = {"members": 0, "messages": []}
        elif code not in rooms:
            return render_template("home.html", error="Room does not exist.", name=name, code=code)
        else:
            room = code
        
        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))

    return render_template("home.html")

@app.route("/room")
def room():
    room = session.get("room")
    name = session.get("name")
    if room is None or name is None or room not in rooms:
        return redirect(url_for("home"))
    return render_template("room.html", code=room, name=name,messages=rooms[room]["messages"])

@socketio.on("message")
def message(data):
     room = session.get("room")
     if room not in rooms :
          return
     content = {
          "name" : session.get("name"),
          "message" : data["data"]
     }
     send(content,to=room)
     rooms[room]["messages"].append(content)
     print(f"{session.get('name')} said : {data['data']}")

@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not name or not room :
        return
    if room not in rooms :
        leave_room(room)

    join_room(room)
    send({"name": name , "message" :"has joined the room !"},to=room)
    rooms[room]["members"]+=1
    print(f'{name} has entered the {room}!')

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"]-=1
        if rooms[room]["members"]<=0:
                       del rooms[room]
    send({"name": name , "message" :"has left the room !"},to=room)
    print(f'{name} has left the {room}!')


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)

