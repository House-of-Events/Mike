#!/bin/sh

# Wait for the database to be ready
echo "Waiting for the database to be ready... in entrypoint.sh"
until pg_isready -h db -p 5432 -U admin; do
  sleep 1
done

echo "Database is ready. Running migrations and seeds..."

# Run migrations and seed the database
yarn db:migrate
yarn db:seed

# Start the application
exec yarn

