# Mitreid Quickstart

How to run mitreid locally:


## Build 
```
git clone https://github.com/mitreid-connect/OpenID-Connect-Java-Spring-Server.git
cd OpenID-Connect-Java-Spring-Server
git checkout mitreid-connect-1.3.3

mvn -DskipTests package
```

## Run

You *must* first go into `openid-connect-server-webapp` first:

```
cd openid-connect-server-webapp/
mvn jetty:run-war
```

Visit: 
http://localhost:8080/openid-connect-server-webapp

Login:
User: admin
Password: password

## Advanced

Scenario: You already have a users database, and you want mitreid to lookup
users on a table in a different database.

- Authenticate against a different user database, perhaps remotely

For this will will use Open Bank Project as an example.
Users may create accounts at the Open Bank Project application, and 
oauth clients may be created via the Open Bank Project application.

## Quickly start two postgress instances

- One for Open Bank Project
- Another for Mitreid
- This simulates connecting to a remote database (we still need to link them)

Ports:
- Mitreid will listen on 8080
- Open Bank Project on: 8081

Run postgress instance locally on port 5433 for Open Bank Project
```
docker run --name=obp -p 5433:5432 --detach -e POSTGRES_PASSWORD=password -e POSTGRES_USER=obp -e POSTGRES_DB=obp postgres:9.6-alpine
```

#### You can view logs of either postgress instance with:
```
docker logs -f obp
```

Run *another* postgress instance locally on a different port (5434) for Mitreid

```
docker run --name=mitreid -p 5434:5432 --detach -e POSTGRES_PASSWORD=password -e POSTGRES_USER=mitreid -e POSTGRES_DB=mitreid postgres:9.6-alpine
```

Success looks like this: A postgres instance for Open Bank Project and another for Mitreid
```
docker ps

CONTAINER ID        IMAGE                 COMMAND                  CREATED             STATUS              PORTS                    NAMES
16aa373a6bfb        postgres:9.6-alpine   "docker-entrypoint.s…"   3 seconds ago       Up 2 seconds        0.0.0.0:5434->5432/tcp   mitreid
4b472d471525        postgres:9.6-alpine   "docker-entrypoint.s…"   9 seconds ago       Up 8 seconds        0.0.0.0:5433->5432/tcp   obp
```

## Configure Open Bank Project to use postgress

Clone open bank project yourself, and copy the `obp-api/src/main/resources/props/default.props.template`
to `obp-api/src/main/resources/props/default.props`.

Edit `obp-api/src/main/resources/props/default.props` to contain the database credentials of obp:

```
vim obp-api/src/main/resources/props/default.props
# Set 
db.url=jdbc:postgresql://127.0.0.1:5433/obp?user=obp&password=password
# Save
```
Set the post to 8081:
```
hostname=http://127.0.0.1:8081
dev.port=8081
```


Start Open Bank Project, which will now use the postgress database:
```
mvn install -pl .,obp-commons && mvn -DskipTests -D jetty.port=8081 jetty:run -pl obp-api
```

Once Open Bank Project is running, visit http://127.0.0.1:8081/user_mgt/sign_up
and create an account for yourself.

Teardown:
```
docker stop obp
docker rm obp
docker stop mitreid
docker rm mitreid
```
