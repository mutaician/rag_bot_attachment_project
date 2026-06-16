docker commands

```bash
docker compose up -d       # start the server
docker compose ps          # Is the container running?
docker compose logs <db_name>     # Postgres logs (errors, startup)
docker compose down        # Stop and remove container (volume data kept)
docker compose down -v     # Stop AND delete volume (wipes database)
docker compose exec postgres psql -U rag_user -d rag_db

```
