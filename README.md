# DEaDASS 2 - In case you didn't learn your lesson the firs time

Database Execution and Deletion Administrative Self Service

DEaDASS is a database management system to allow automated creation and deletion of various database instances, as well as eventually replicating and replacing the functionality of phpMyAdmin and phpPgAdmin. It is written in Flask.

## Spinning up

Docker is the recommended method of running this.

`docker build -t deadass .`

`docker run -p 8080:8080 deadass`

If you need credentials, contact an RTP.