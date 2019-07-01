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


Get the IP address of the postgre database for Open Bank Project:
```
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' obp
```


```
vim obp-api/src/main/resources/props/default.props
# Set (your ip address will be different)
db.url=jdbc:postgresql://172.17.0.3:5432/obp?user=obp&password=password
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
\c oic
--  Create extension dblink
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
    validated 
    from public.authuser') 
  AS DATA(username VARCHAR, password VARCHAR, enabled VARCHAR);
```

#### Create the authorities view
```
CREATE VIEW authorities AS 
  SELECT * FROM public.dblink ('obpapiserver', 
    'select username, ''ROLE_USER'' 
    authority from public.authuser') 
  AS DATA(username VARCHAR, authority VARCHAR);
```

#### Create user_info view
```
CREATE VIEW user_info AS 
  SELECT * FROM public.dblink ('obpapiserver', 
    'select id, NULL sub, username, concat(firstname, '' '', lastname), 
      firstname, lastname, NULL middle_name, NULL nickname, NULL profile, 
      NULL picture, NULL website, email, validated, NULL gender, 
      NULL zone_info, NULL locale, NULL phone_number, 
      NULL phone_number_verified, NULL address_id, NULL updated_time, 
      NULL birthdate, NULL src from public.authuser') 
  AS DATA(id INT, sub VARCHAR(256), preferred_username VARCHAR(256), 
          name VARCHAR(256), given_name VARCHAR(256), family_name VARCHAR(256),
          middle_name VARCHAR(256), nickname VARCHAR(256), profile VARCHAR(256),
          picture VARCHAR(256), website VARCHAR(256), email VARCHAR(256), 
          email_verified BOOLEAN, gender VARCHAR(256), zone_info VARCHAR(256), 
          locale VARCHAR(256), phone_number VARCHAR(256), 
          phone_number_verified BOOLEAN, address_id VARCHAR(256), 
          updated_time VARCHAR(256), birthdate VARCHAR(256), 
          src VARCHAR(4096));
```

#### Create view client_details
This essential re-creates the default `client_details` consistent with 
Mitreid's datamodel (so it's a valid `client_details` table. 
```
CREATE VIEW client_details AS SELECT * FROM public.dblink('obpapiserver', 'select id,
description,
''t'' reuse_refresh_tokens,
''f'' dynamically_registered,
''f'' allow_introspection,
''600'' id_token_validity_seconds,
NULL device_code_validity_seconds,
key_c,
secret,
''3600'' access_token_validity_seconds,
NULL refresh_token_validity_seconds,
NULL application_type,
name,
''SECRET_BASIC'' token_endpoint_auth_method,
NULL subject_type,
NULL logo_uri,
NULL policy_uri,
NULL client_uri,
NULL tos_uri,
NULL jwks_uri,
NULL jwks,
NULL sector_identifier_uri,
NULL request_object_signing_alg,
NULL user_info_signed_response_alg,
NULL user_info_encrypted_response_alg,
NULL user_info_encrypted_response_enc,
NULL id_token_signed_response_alg,
NULL id_token_encrypted_response_alg,
NULL id_token_encrypted_response_enc,
NULL token_endpoint_auth_signing_alg,
''60000'' default_max_age,
''t'' require_auth_time,
createdat,
NULL initiate_login_uri,
''t'' clear_access_tokens_on_refresh,
NULL software_statement,
NULL software_id,
NULL software_version,
NULL code_challenge_method from public.consumer') AS DATA (
id INT,
client_description VARCHAR(1024),
reuse_refresh_tokens BOOLEAN,
dynamically_registered BOOLEAN,
allow_introspection BOOLEAN,
id_token_validity_seconds BIGINT,
device_code_validity_seconds BIGINT,
client_id VARCHAR(256),
client_secret VARCHAR(2048),
access_token_validity_seconds BIGINT,
refresh_token_validity_seconds BIGINT,
application_type VARCHAR(256),
client_name VARCHAR(256),
token_endpoint_auth_method VARCHAR(256),
subject_type VARCHAR(256),
logo_uri VARCHAR(2048),
policy_uri VARCHAR(2048),
client_uri VARCHAR(2048),
tos_uri VARCHAR(2048),
jwks_uri VARCHAR(2048),
jwks VARCHAR(8192),
sector_identifier_uri VARCHAR(2048),
request_object_signing_alg VARCHAR(256),
user_info_signed_response_alg VARCHAR(256),
user_info_encrypted_response_alg VARCHAR(256),
user_info_encrypted_response_enc VARCHAR(256),
id_token_signed_response_alg VARCHAR(256),
id_token_encrypted_response_alg VARCHAR(256),
id_token_encrypted_response_enc VARCHAR(256),
token_endpoint_auth_signing_alg VARCHAR(256),
default_max_age BIGINT,
require_auth_time BOOLEAN,
created_at TIMESTAMP,
initiate_login_uri VARCHAR(2048),
clear_access_tokens_on_refresh BOOLEAN,
software_statement VARCHAR(4096),
software_id VARCHAR(2048),
software_version VARCHAR(2048),
code_challenge_method VARCHAR(256));

```

### Prepare remaining Oauth spesific views:

#### Drop existing tables
```
drop table client_contact;
drop table client_grant_type;
drop table client_scope;
drop table client_response_type;
drop table client_redirect_uri;
```

#### Create client_contact view:
```
CREATE VIEW client_contact AS 
  SELECT * FROM public.dblink('obpapiserver', 
    'select id, developeremail 
    from public.consumer') 
  AS DATA(owner_id INT, contact VARCHAR(256));
```

#### Create client_grant_type view:
```
CREATE VIEW client_grant_type AS 
  SELECT * FROM public.dblink('obpapiserver', 
    'select id, ''authorization_code'' grant_type 
    from public.consumer') 
  AS DATA (owner_id INT, grant_type VARCHAR(2000));
```

#### Create client_scope view:
Creates default scope of openid
```
CREATE VIEW client_scope AS 
    SELECT * FROM public.dblink('obpapiserver', 
      'select id, ''openid'' scope 
      from public.consumer') 
    AS DATA (owner_id INT, scope VARCHAR(2048));
```

#### Create client_response_type view:
```
CREATE VIEW client_response_type AS 
    SELECT * FROM public.dblink('obpapiserver', 
      'select id, ''code'' response_type 
      from public.consumer') 
    AS DATA (owner_id INT, response_type VARCHAR(2048));
```

#### Create client_redirect_uri view:
```
CREATE VIEW client_redirect_uri AS 
    SELECT * FROM public.dblink('obpapiserver', 
      'select id, redirecturl 
      from public.consumer') 
    AS DATA (owner_id INT, redirect_uri VARCHAR(2048));
```

### Enable password encryption using bcrypt in Mitreid

Edit the user-context to use bcrypt:
`vi openid-connect-server-webapp/src/main/webapp/WEB-INF/user-context.xml`
#Replace the `id="authenticationManager"` section with:
```
  <security:authentication-manager id="authenticationManager">
    <security:authentication-provider>
      <security:jdbc-user-service data-source-ref="dataSource"/>
      <security:password-encoder ref="bcrypt" />
    </security:authentication-provider>
  </security:authentication-manager>

  <bean id="bcrypt" class="org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder">
          <constructor-arg name="strength" value="10" />
  </bean>
```

Now run Mitreid again, which will now:

- Use the views we created
- Allow you to login via Mitreid

note, you *must* first go into `openid-connect-server-webapp` first:
```
cd openid-connect-server-webapp/
mvn jetty:run-war
```

Visit: 
http://localhost:8080/openid-connect-server-webapp
.. and login as an Open Bank Project User

- Users created on Open Bank Project will be able to login
  to Mitreid

Next steps: Configure an oauth client to login via Mitreid (identify)

## Login using oauth2 flow

The Mitreid authorization url is:

http://localhost:8080/openid-connect-server-webapp/authorize?response_type=code&client_id=CLIENT_ID&redirect_uri=REDIRECT_URI&scope=openid&state=1234zyx

Where:

- CLIENT_ID is generated upon registering a client (on Open Bank Project)
- Response_type is authorization_code
- REDIRECT_URI is the registerd clients redirect url 
  - Meaning, when you create a consumer on Open Bank Project, it is the redirect
    url set when registering an app.

#### How do I know the client_id?
```
select client_id from client_details;
```

#### How do I know my client_redirect_uri?
```
select * from client_redirect_uri;
```


http://localhost:8080/openid-connect-server-webapp/authorize?response_type=code&client_id=zylmowrrystppebu3cwd4zfmhxcj1epkjrp0qqvn&redirect_uri=http://127.0.0.1:5000&scope=openid&state=1234zyx



### Debug

#### Help I need to change the IP address of the dblink_connect server wrapper
See https://www.postgresql.org/docs/8.4/sql-alterserver.html
Example:
```
docker exec -it mitreid bash
psql -U oic
-- Alter:
ALTER SERVER obpapiserver OPTIONS (SET hostaddr '172.17.0.2'); # change ip
-- Verify:
SELECT dblink_connect('obpapiserver');
```

Teardown:
```
docker stop obp
docker rm obp
docker stop mitreid
docker rm mitreid
```

## Useful links

- Oauth2 spec: https://tools.ietf.org/html/rfc6749
- Oauth2 simplified https://aaronparecki.com/oauth-2-simplified/#authorization
