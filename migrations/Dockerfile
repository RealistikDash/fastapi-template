FROM ubuntu:24.04

# Apt dependencies
RUN apt update && apt install default-mysql-client wget -y

# Setup Go Migrate
RUN wget https://github.com/golang-migrate/migrate/releases/download/v4.18.3/migrate.linux-amd64.tar.gz && \
    tar zxvf migrate.linux-amd64.tar.gz && \
    mv migrate /usr/local/bin/go-migrate && \
    chmod u+x /usr/local/bin/go-migrate && \
    rm migrate.linux-amd64.tar.gz


# Configure the migrator service.
WORKDIR /app
COPY perform_migrations.sh /app/perform_migrations.sh
RUN chmod +x /app/perform_migrations.sh
COPY ./migrations /migrations

ENTRYPOINT [ "/app/perform_migrations.sh" ]
