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



