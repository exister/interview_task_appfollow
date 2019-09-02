SHELL := /bin/bash

%:
	@:

runserver:
	docker-compose up

tests:
	docker-compose run server pytest
