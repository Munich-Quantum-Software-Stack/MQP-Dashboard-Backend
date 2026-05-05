
export PATH := /usr/local/bin:$(PATH)
# Load .env if present
ifneq (,$(wildcard .env))
	include .env
	export
endif

# Extract version in pyproject.toml
$(eval VERSION=$(shell grep -m 1 version pyproject.toml | tr -d '"' | cut -d' ' -f3 | tr -s ' ' | tr -d "'" ) )

DOCKER := /usr/local/bin/docker
IMAGE_NAME = bqp-dashboard-backend

.PHONY: build-image up down logs run-image tag-image push-image clean


build-image:
	$(DOCKER) build --no-cache \
		-t $(IMAGE_NAME) \
		-t $(IMAGE_NAME):${VERSION} .

up:
	docker compose -f docker-compose.yaml up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

run-image:
	$(DOCKER) run --rm -it \
	-p 5000:5000 \
	--env-file .env \
	$(IMAGE_NAME):$(VERSION)

tag-image:
	$(DOCKER) tag $(IMAGE_NAME):$(VERSION) $(IMAGE_NAME):latest

push-image:
	docker tag $(IMAGE_NAME):${VERSION} ${DOCKERHUB}/$(IMAGE_NAME):${VERSION}
	docker tag ${DOCKERHUB}/$(IMAGE_NAME):${VERSION} ${DOCKERHUB}/$(IMAGE_NAME):latest
	docker push ${DOCKERHUB}/$(IMAGE_NAME):${VERSION}
	docker push ${DOCKERHUB}/$(IMAGE_NAME):latest

clean:
	$(DOCKER) rmi $(IMAGE_NAME):$(VERSION) || true
	$(DOCKER) rmi $(IMAGE_NAME):latest || true
