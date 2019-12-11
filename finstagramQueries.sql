CREATE TABLE Person(
    username VARCHAR(20), 
    password CHAR(64), 
    firstName VARCHAR(20),
    lastName VARCHAR(20),
    bio VARCHAR(1000),
    PRIMARY KEY (username)
);

CREATE TABLE Friendgroup(
    groupOwner VARCHAR(20),
    groupName VARCHAR(20),
    description VARCHAR(1000),
    PRIMARY KEY (groupOwner, groupName),
    FOREIGN KEY (groupOwner) REFERENCES Person(username)
);

CREATE TABLE Photo (
    photoID int AUTO_INCREMENT,
    postingdate DATETIME,
    filepath VARCHAR(100),
    allFollowers Boolean,
    caption VARCHAR(100),
    photoPoster VARCHAR(20),
    PRIMARY KEY (photoID),
    FOREIGN KEY(photoPoster) REFERENCES Person(username)
);

CREATE TABLE Likes (
    username VARCHAR(20),
    photoID int,
    liketime DATETIME,
    rating int,
    PRIMARY KEY(username, photoID),
    FOREIGN KEY(username) REFERENCES Person(username),
    FOREIGN KEY(photoID) REFERENCES Photo(photoID)
);

CREATE TABLE Tagged (
    username VARCHAR(20),
    photoID int,
    tagstatus Boolean,
    PRIMARY KEY(username, photoID),
    FOREIGN KEY(username) REFERENCES Person(username),
    FOREIGN KEY(photoID)REFERENCES Photo(photoID)
);

CREATE TABLE SharedWith (
    groupOwner VARCHAR(20),
    groupName VARCHAR(20),
    photoID int,
    PRIMARY KEY(groupOwner, groupName, photoID),
    FOREIGN KEY(groupOwner, groupName) REFERENCES Friendgroup(groupOwner, groupName),
    FOREIGN KEY (photoID) REFERENCES Photo(photoID)
);

CREATE TABLE BelongTo (
    member_username VARCHAR(20),
    owner_username VARCHAR(20),
    groupName VARCHAR(20),
    PRIMARY KEY(member_username, owner_username, groupName),
    FOREIGN KEY(member_username) REFERENCES Person(username),
    FOREIGN KEY(owner_username, groupName)REFERENCES Friendgroup(groupOwner, groupName)
);

CREATE TABLE Follow (
    username_followed VARCHAR(20),
    username_follower VARCHAR(20),
    followstatus Boolean,
    PRIMARY KEY(username_followed , username_follower),
    FOREIGN KEY(username_followed) REFERENCES Person(username),
    FOREIGN KEY(username_follower) REFERENCES Person(username)
);

# Query to find photoIDs of photos that are visible to the user whose username is TestUser.
# A photo is visible to TestUser if...
#   1. allFollowers == True for the photo and TestUser has been accepted as a follower by the photoPoster OR...
#   2. the photo is shared with a FriendGroup to which TestUser belongs to where the FriendGroup is identified by its
#      groupName and groupOwner, the username of the owner of the group.

SELECT photoID
FROM photo AS p1
WHERE (allFollowers = TRUE
       AND 'TestUser' = (SELECT username_follower
                         FROM follow
                         WHERE username_followed = p1.photoPoster
                         AND username_follower = 'TestUser'
                         AND followStatus = TRUE))
OR ('TestUser' IN (SELECT member_username
                   FROM belongto
                   WHERE (owner_username, groupName) IN (SELECT groupOwner, groupName
                                                         FROM sharedwith
                                                         WHERE photoID = p1.photoID)))

# Query for feature 1

SELECT *
FROM photo AS p1
WHERE (allFollowers = TRUE
       AND %s = (SELECT username_follower
                 FROM follow
                 WHERE username_followed = p1.photoPoster
                 AND username_follower = %s
                 AND followStatus = TRUE))
OR (%s IN (SELECT member_username
           FROM belongto
           WHERE (owner_username, groupName) IN (SELECT groupOwner, groupName
                                                 FROM sharedwith WHERE photoID = p1.photoID)))
ORDER BY postingdate DESC