dc := docker compose -f docker-compose.yml --env-file docker-env

.PHONY: build
build:
	$(dc) up -d --build;

.PHONY: up
up:
	$(dc) up -d;

.PHONY: stop
stop:
	$(dc) stop;

.PHONY: down
down:
	$(dc) down;

.PHONY: down-v
down-v:
	$(dc) down -v;

.PHONY: restart
restart:
	$(dc) stop && $(dc) up -d;
