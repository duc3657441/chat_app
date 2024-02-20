from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase
from werkzeug.security import generate_password_hash, check_password_hash
from app.connect import connectdb, call_postgres_function
from functools import wraps


app = Flask(__name__)
app.config["SECRET_KEY"] = "Akjdkajdhakj"
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_COOKIE_AGE"] = 1800
# app.config["SESSION_PERMANENT"] = False
# Session(app)
socketio = SocketIO(app)

rooms = {}
# progre sql
# bảng onl id trong bảng user
# user (user_id, username, pass_hash, status) status -> true, logout ->false
# bảng rooms (room_id, user_id, messages)
#
# 3 trang web: 
#               đăng nhập: nếu người dùng đang đăng nhập thì từ chối (tạo 1 biến onl và off hoặc tạo 1 bảng những user đang login)
#               đăng ký tài khoản (code trang web, dựa trên bài cũ, copy code bỏ vào, nhớ kết nối sql)
#               nhập mã phòng hoặc tạo phòng (code trang web, code sever trong python)
#               room chat (có thêm tìm kiếm tin nhắn: bg thành màu vàng)

def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("email") is None:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)

        try:
            conn, cur = connectdb()
            insert_script = "SELECT RoomID FROM Rooms WHERE maRoom = %s"
            insert_value = (code,)
            cur.execute(insert_script,insert_value)
            Q = cur.fetchone()
            cur.close()
            conn.close()
        except Exception as e:
            return render_template("error.html",message = e)
        
        if Q is None:
            break

        if code not in rooms:
            break

    return code

@app.route("/register", methods=['POST', 'GET'])
def register():
    # if GET, show the registration form
    if request.method == 'GET':
        return render_template('register.html')
    
    # if POST, validate and commit to database 
    else:

        #if form values are empty show error
        if not request.form.get("first_name"):
            return render_template("error.html", message="Must provide First Name")
        elif not request.form.get("last_name"):
            return render_template("error.html", message="Must provide Last Name")
        elif  not request.form.get("email"):
            return render_template("error.html", message="Must provide E-mail")
        elif not request.form.get("password1") or not request.form.get("password2"):
            return render_template("error.html", message="Must provide password")
        elif request.form.get("password1") != request.form.get("password2"):
            return render_template("error.html", message="Password does not match")
        else :
            ## assign to variables
            first_name = request.form.get("first_name")
            last_name = request.form.get("last_name")
            email = request.form.get("email")
            password = request.form.get("password1")
            # try to commit to database, raise error if any

            try:
                conn, cur = connectdb()
                insert_script = "INSERT INTO users (firstname, lastname, email, password) VALUES (%s, %s, %s, %s)"
                insert_value = (first_name,last_name,email,generate_password_hash(password))
                cur.execute(insert_script,insert_value)
                conn.commit()
                cur.close()
                conn.close()
            except Exception as e:
                return render_template("error.html",message = e)

            return redirect(url_for("home"))


@app.route("/", methods = ["POST", "GET"])
@login_required
def home():
    # session.clear()
    if request.method == "POST":
        name = session["lastName"]
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)
        if join != False and not code:
            return render_template("home.html", error = "Please enter a room code", code = code, name = name)
        
        room = code
        # Khi tao room
        if create != False:
            room = generate_unique_code(6)
            try:
                conn, cur = connectdb()
                insert_script = "INSERT INTO Rooms (maRoom, roomName, members) VALUES (%s, %s, %s)"
                insert_value = (room, room, '0')
                cur.execute(insert_script,insert_value)
                conn.commit()
                cur.close()
                conn.close()
            except Exception as e:
                return render_template("error.html",message = e)
            
            rooms[room] = {"members" : 0, "messages" : []} # kết nối vô sql 
        #khi nhap ma room
        else:
            try:
                conn, cur = connectdb()
                insert_script = "SELECT * FROM Rooms WHERE maRoom = %s"
                insert_value = (code,)
                cur.execute(insert_script,insert_value)
                Q = cur.fetchone()
                cur.close()
                conn.close()
            except Exception as e:
                return render_template("error.html",message = e)
            
            if Q is None:
                return render_template("home.html", error = "Room does not exist", code = code, name = name)

        session["maRoom"] = room
        return redirect(url_for("room"))

    else: 
        name = session["lastName"]
        return render_template("home.html", name = name)

@app.route("/room")
@login_required
def room():
    room = session.get("maRoom")
    try:
        conn, cur = connectdb()
        insert_script = "SELECT RoomID FROM Rooms WHERE maRoom = %s"
        insert_value = (room,)
        cur.execute(insert_script,insert_value)
        Q = cur.fetchone()
        cur.close()
        conn.close()
    except Exception as e:
        return render_template("error.html",message = e)
    
    # if room is None or session.get("lastName") is None or room not in rooms:
    if room is None or session.get("lastName") is None or Q is None:
        return redirect(url_for("home"))
    
    session["room_id"] = Q[0]
    try:
        conn, cur = connectdb()
        insert_script = "select lastName, chat from users, messages where user_id = UserID and room_id = %s"
        insert_value = (session["room_id"],)
        cur.execute(insert_script,insert_value)
        results = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        return render_template("error.html",message = e)
    # return render_template("room.html", room = room, messages = rooms[room]["messages"])
    return render_template("room.html", room = room, messages = results)

@app.route("/login", methods = ["POST", "GET"])
def login():
    if request.method == 'GET':
        if "user_id" in session:
            return redirect(url_for("home"))
        return render_template("login.html")
    
    else :
        if not request.form.get("email"):
            return render_template("error.html", message="Must provide email")
        elif not request.form.get("password"):
            return render_template("error.html", message="Must provide password")
        else :
            ## assign to variables
            form_email = request.form.get("email")
            form_password = request.form.get("password")
            # try to commit to database, raise error if any

            try:
                conn, cur = connectdb()
                insert_script = "SELECT UserID, lastName, email, password FROM users WHERE email LIKE %s and online = %s "
                insert_value = (form_email, 'false')
                cur.execute(insert_script,insert_value)
                Q = cur.fetchone()
                cur.close()
                conn.close()
            except Exception as e:
                return render_template("error.html",message = e)
            
             # # User exists ?
            if Q is None:
                return render_template("error.html", message="User doesn't exists or account is being logged in elsewhere")
            # Valid password ?
            if not check_password_hash( Q[3], form_password):
                return  render_template("error.html", message = "Invalid password")
            
            session["user_id"] = Q[0]
            session["email"] = Q[2]
            session["lastName"] = Q[1]
            session["logged_in"] = True

            try:
                conn, cur = connectdb()
                insert_script = "update users set online = 'true' where email LIKE %s"
                insert_value = (form_email,)
                cur.execute(insert_script,insert_value)
                conn.commit()
                cur.close()
                conn.close()
            except Exception as e:
                return render_template("error.html",message = e)
            
            return redirect(url_for("home"))

@app.route("/logout")
def logout():
    try:
        conn, cur = connectdb()
        insert_script = "update users set online = 'false' where email LIKE %s"
        insert_value = (session["email"],)
        cur.execute(insert_script,insert_value)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        return render_template("error.html",message = e)
    
    session.clear()
    return redirect(url_for("login"))

@socketio.on("connect")
def connect(auth):
    room = session.get("maRoom")
    name = session.get("lastName")
    try:
        conn, cur = connectdb()
        insert_script = "SELECT RoomID FROM Rooms WHERE maRoom = %s"
        insert_value = (room,)
        cur.execute(insert_script,insert_value)
        Q = cur.fetchone()
        cur.close()
        conn.close()
    except Exception as e:
        return render_template("error.html",message = e)
    
    if not room or not name:
        return
    if Q is None:
        leave_room(room)
        return
    
    join_room(room)
    send({"name": name, "message": "has enter the room"}, to = room)
    try:
        conn, cur = connectdb()
        insert_script = "update rooms set members = members + 1 where RoomID = %s"
        insert_value = (session["room_id"],)
        cur.execute(insert_script,insert_value)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        return render_template("error.html",message = e)
    
    rooms[room]["members"] += 1
    print(f"{name} join room {room}")

@socketio.on("disconnect")
def disconnect():
    room = session.get("maRoom")
    name = session.get("lastName")
    leave_room(room)

    try:
        conn, cur = connectdb()
        insert_script = "update rooms set members = members - 1  where RoomID = %s"
        insert_value = (session["room_id"],)
        cur.execute(insert_script,insert_value)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        return render_template("error.html",message = e)
    
    func = "delete_empty_room"
    parameters = (session["room_id"],)
    results = call_postgres_function(func,parameters)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]

    try:
        conn, cur = connectdb()
        insert_script = "update users set online = 'false' where email LIKE %s"
        insert_value = (session["email"],)
        cur.execute(insert_script,insert_value)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        return render_template("error.html",message = e)

    send({"name": name, "message": "has left the room"}, to = room)
    print(f"{name} has left the room {room}")

@socketio.on("message")
def message(data):
    room = session["maRoom"]
    if room not in rooms:
        return
    
    content = {
        "name" : session.get("lastName"),
        "message" : data["data"]
    }

    send(content,to=room)
    try:
                conn, cur = connectdb()
                insert_script = "INSERT INTO Messages (user_id, room_id, chat) VALUES (%s, %s, %s)"
                insert_value = (session["user_id"], session["room_id"], content["message"])
                cur.execute(insert_script,insert_value)
                conn.commit()
                cur.close()
                conn.close()
    except Exception as e:
                return render_template("error.html",message = e)
    rooms[room]["messages"].append(content)
    print(f"{session.get("lastName")} said: {data['data']}")
    
if __name__ == "__main__":
    socketio.run(app, debug= True)