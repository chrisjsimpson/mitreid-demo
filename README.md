# Mitreid Quickstart

How to run mitreid locally:

<a href="https://youtu.be/UFyUtZ6oMYE">Video Demo, locall install</a>

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
docker run --name=mitreid -p 5434:5432 --detach -e POSTGRES_PASSWORD=oic -e POSTGRES_USER=oic -e POSTGRES_DB=oic postgres:9.6-alpine
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

Now make sure Mitreid is configured to also use postgress following the instructions.

## Configure Mitreid to use postgress
By default Mitreid used Hbase for a cute play database. Now we need to change
it's config to use postgress instead:

Go to the `OpenID-Connect-Java-Spring-Server` directory then edit:
```
vi openid-connect-server-webapp/src/main/webapp/WEB-INF/data-context.xml
```
- Comment out or delete the entire Hbase (`hsql`) config section

Correct the database port: 

- Replace `jdbc:postgresql://localhost/oic` with `jdbc:postgresql://127.0.0.1:5434/oic`

Replace the `optionally initialize the database` part with the following:
Note that `loading_temp_tables.sql` needs to be copied from the hbase example.

Careful, it's really easy to make a syntax error here
```
  <jdbc:initialize-database data-source="dataSource">
    <jdbc:script location="classpath:/db/psql/psql_database_tables.sql"/> 
    <jdbc:script location="classpath:/db/hsql/loading_temp_tables.sql"/> 
    <jdbc:script location="classpath:/db/psql/security-schema.sql"/>
    <jdbc:script location="classpath:/db/psql/users.sql"/>
    <jdbc:script location="classpath:/db/psql/clients.sql"/>
    <jdbc:script location="classpath:/db/psql/scopes.sql"/>
    <jdbc:script location="classpath:/db/psql/psql_database_index.sql"/> 
  </jdbc:initialize-database>
```

- Save `data-context.xml`

Edit `vi openid-connect-server-webapp/pom.xml` to include postgres as a dependency:

```
<dependency>
        <groupId>org.postgresql</groupId>
        <artifactId>postgresql</artifactId>
        <version>42.0.0.jre7</version>
</dependency>
```

Now run Mitreid again: note, you *must* first go into `openid-connect-server-webapp` first:
```
cd openid-connect-server-webapp/
mvn jetty:run-war
```

Visit: http://localhost:8080/openid-connect-server-webapp
which will now be using the postgress database!

After running sucessfully once, you **must** disable (comment out) the 
`initialize-database` step in `data-context.xml` of the project.

Now the database is seeded, remove or comment out `initialize-database` section:

```
vi openid-connect-server-webapp/src/main/webapp/WEB-INF/data-context.xml
```

# Configure link between Open Bank Project database & mitreid

Now we want users registered via Open Bank Project, to also be users 
registered in mitreid. We're **not** going to duplicate the data. 
Instead, we're going to create a *link* between the two databases and
expose this as a database *view* to Mitreid. Mitreid will think it's
looking at it's default users table, but actually it's viewing 
Open Bank Project's database. Obviously we need to fill in gaps, Mitreid
provides much of the rest.

- We want to authenticate against the user accounts in the OBP-API databse


Get the IP address of your Open Bank Project postgress docker instance.
(Sorry, you only need to do this because this demo uses docker, if you're not
using docker for your postgres instances, obviously you don't need to do this):

```
# Save the output of 
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' obp
```
You'll need that IP when connecting from Mitreid's database to Open Bank 
Project's database.

Login to the mitreid postgres database:
```
docker exec -it mitreid bash
psql -U oic # login to postgres as oic user
# Create extension dblink
CREATE EXTENSION dblink;
```


Quickly test connection:
(Your IP address will be different, but the port the same) note that the port
is 5432, this is because we're connecting directly to the container and not via 
docker's port mappings.
```
SELECT dblink_connect('host=172.17.0.3:5432 user=obp password=password dbname=obp');
```
You should see:
```
 dblink_connect 
----------------
 OK
(1 row)
```

Create db wrapper to able to create views later:
(Note: your IP address will be different)
This essentially creates a named connection to the remote server.
```
CREATE FOREIGN DATA WRAPPER dbobpapi VALIDATOR postgresql_fdw_validator;
CREATE SERVER obpapiserver FOREIGN DATA WRAPPER dbobpapi OPTIONS (hostaddr '172.17.0.3', dbname 'obp');
CREATE USER MAPPING FOR oic SERVER obpapiserver OPTIONS (user 'obp', password 'password');
```

Test that the wrapper was created correctly:
```
SELECT dblink_connect('obpapiserver');
# Output:
 dblink_connect 
----------------
 OK
(1 row)
```

Grant usage privilege for user oic on the wrapper
```
GRANT USAGE ON FOREIGN SERVER obpapiserver TO oic;
```

## Create Database Views of the remote users 
We will drop certain tables created by MITREId Connect during initialization 
and create views insted.

All these views take what data we can from Open Bank Project, and for 
Oauth related objects, mitreid defaults are used (this is because *Mitreid still
needs to see a table (view) which is consistent with its existing datamodel*).

### Delete Mitreid generated tables
(we will re-create them as views to Open Bank Project):
```
drop table authorities;
drop table users;
drop table user_info;
drop table client_details;
```

#### Create the users view
```
CREATE VIEW users AS 
  SELECT * FROM public.dblink ('obpapiserver', 
    'select username, substring(concat(password_pw,password_slt), 3), 
    validated from public.authuser') 
  AS DATA(username VARCHAR, password VARCHAR, enabled VARCHAR);
```

### Create the authorities view
```
CREATE VIEW authorities AS 
  SELECT * FROM dblink ('obpapiserver', 
    'select username, 
    ''ROLE_USER'' authority from authuser') 
  AS DATA(username VARCHAR, authority VARCHAR);
```


Teardown:
```
docker stop obp
docker rm obp
docker stop mitreid
docker rm mitreid
```
