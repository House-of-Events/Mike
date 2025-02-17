#!/bin/sh

echo "Waiting for the database to be ready... in entrypoint.sh"
while ! pg_isready -h db -p 5432 -U admin -d mike-docker
do
    echo "db:5432 - no response"
    sleep 2
done

echo "db:5432 - accepting connections"
echo "Database is ready. Running migrations and seeds..."

# Run migrations and seeds
yarn run db:migrate:dev
yarn run db:seed:dev

# Keep container running
echo "Starting application..."
tail -f /dev/null