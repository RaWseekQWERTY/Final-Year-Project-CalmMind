up:
	docker-compose up --build

down:
	docker-compose down -v

shell:
	docker-compose exec web bash

migrate:
	docker-compose exec web python manage.py migrate

createsuperuser:
	docker-compose exec web python manage.py createsuperuser

logs:
	docker-compose logs -f web

psql:
	docker-compose exec db psql -U $$DB_USER -d $$DB_NAME

