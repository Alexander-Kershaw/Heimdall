.PHONY: up down logs ps reset

up:
	docker compose up -d

down:
	docker compose down

ps:
	docker compose ps

logs:
	docker compose logs -f --tail=200

reset:
	docker compose down -v


