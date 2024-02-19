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


INSERT INTO Rooms (maRoom, roomName, members) VALUES ('Abc','test', '0')
