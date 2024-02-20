SET schema 'ChatApp';
CREATE TABLE Users (
  UserID SERIAL PRIMARY KEY,
  firstName VARCHAR NOT NULL,
  lastName VARCHAR NOT NULL,
  email VARCHAR UNIQUE NOT NULL,
  password VARCHAR NOT NULL,
  online BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE Rooms (
    RoomID SERIAL PRIMARY KEY,
    maRoom VARCHAR UNIQUE NOT NULL,
    roomName VARCHAR NOT NULL,
	members INTEGER NOT NULL,
    timeCreate TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
);

CREATE TABLE Messages (
    MessageID SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users,
    room_id INTEGER REFERENCES rooms,
	chat VARCHAR,
	timeChat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Onlines(
	OnlineID SERIAL PRIMARY KEY,
	user_id INTEGER REFERENCES users
);



CREATE OR REPLACE FUNCTION delete_empty_room(func_room_id INTEGER)
RETURNS void AS $$
BEGIN
    IF EXISTS (SELECT * FROM Rooms WHERE RoomID = func_room_id AND members > 0) THEN
    RETURN;
  END IF;
	if exists (select * from messages where room_id = func_room_id) THEN
	 DELETE FROM messages WHERE room_id = func_room_id;
	 end if;
  DELETE FROM Rooms WHERE roomid = func_room_id AND members <= 0;
END;
$$ LANGUAGE plpgsql;
