#!/bin/sh

function test_db_connection() {
  # "docker-compose up -d" often failed for me despite using "depends_on".
  # The db was not ready when the app launched resulting in connection errors.
  # This function tests whether it is possible to reach the db.

  printf "\nTesting DB connection..."

  local host="${1:-localhost}"
  local port="${2:-5432}"
  local max_attempts="10"
  local sleep_interval="2"

  local attempt=1
  local ready_text="database system is ready to accept connections"

  while [ $attempt -le $max_attempts ]; do
    result=$(docker compose logs -n 3 | grep -c "$ready_text")

    if [ $result -eq 1 ]; then
        printf "\nDB is ready to accept connections.\n"
        return
    else
        echo "DB is not yet ready to accept connections. Retrying in $sleep_interval seconds..."
        sleep $sleep_interval
        ((attempt++))
    fi
  done

  echo "Maximum number of attempts waiting for DB reached."
  echo "Stopping build process."

  exit 1
}


printf "\nStarting DB service...\n\n"
docker compose up -d db
printf "\nDB service started\n"

printf "\nStarting Email service...\n\n"
docker compose up -d mail
printf "\nEmail service started\n"


printf "\nBuilding app image...\n\n"
docker compose build app
printf "\nBuilding app image finished.\n"


test_db_connection


#printf "\nStarting migrations...\n\n"
#python manage.py makemigrations
#python manage.py migrate
#printf "\nMigrations finished.\n"


printf "\nStarting app service...\n\n"
docker compose up -d app
printf "\nStarting app service finished. \n"


echo "Build process finished."
