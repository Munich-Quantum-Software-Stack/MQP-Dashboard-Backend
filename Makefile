
# Load .env if present
ifneq (,$(wildcard .env))
	include .env
	export
endif

# Extract version in pyproject.toml
$(eval VERSION=$(shell grep -m 1 version pyproject.toml | tr -d '"' | cut -d' ' -f3 | tr -s ' ' | tr -d "'" ) )

DOCKER := /usr/local/bin/docker
IMAGE_NAME = mqp-dashboard-backend

.PHONY: build up down logs run-image tag-image push-image clean

build:
	$(DOCKER) compose -f docker-compose.yaml build --no-cache

tag-image:
	$(DOCKER) tag $(IMAGE_NAME):$(VERSION) $(IMAGE_NAME):latest

up:
	$(DOCKER) compose up -d

#build-image:
#	$(DOCKER) build --no-cache \
#		-t $(IMAGE_NAME) \
#		-t $(IMAGE_NAME):${VERSION} .

run-image:
	$(DOCKER) run --rm -it --detach \
	-p 5000:5000 \
	--env-file .env \
	$(IMAGE_NAME):$(VERSION)

down:
	docker compose down

logs:
	docker compose logs -f

push-image:
	docker tag $(IMAGE_NAME):${VERSION} ${DOCKERHUB}/$(IMAGE_NAME):${VERSION}
	docker tag ${DOCKERHUB}/$(IMAGE_NAME):${VERSION} ${DOCKERHUB}/$(IMAGE_NAME):latest
	docker push ${DOCKERHUB}/$(IMAGE_NAME):${VERSION}
	docker push ${DOCKERHUB}/$(IMAGE_NAME):latest

clean:
	$(DOCKER) rmi $(IMAGE_NAME):$(VERSION) || true
	$(DOCKER) rmi $(IMAGE_NAME):latest || true
