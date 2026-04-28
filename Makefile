
# Load .env if present
ifneq (,$(wildcard .env))
	include .env
	export
endif

# Extract version in pyproject.toml
$(eval VERSION=$(shell grep -m 1 version pyproject.toml | tr -d '"' | cut -d' ' -f3 | tr -s ' ' | tr -d "'" ) )

DOCKERHUB ?= $(DOCKERHUB)


build-image:
	docker build --no-cache \
		-t bqp-dashboard-backend \
		-t bqp-dashboard-backend:${VERSION} \
		--build-arg PYTHONUNBUFFERED="1" \
		--build-arg QUANTUM_DB_USER=$(QUANTUM_DB_USER) \
		--build-arg QUANTUM_DB_PASS=$(QUANTUM_DB_PASS) \
		--build-arg QUANTUM_DB_HOST="localhost" \
		--build-arg QUANTUM_DS_HOST=$(QUANTUM_DS_HOST) . 

push-image:
	docker tag bqp-dashboard-backend:${VERSION} ${DOCKERHUB}/bqp-dashboard-backend:${VERSION}
	docker tag ${DOCKERHUB}/bqp-dashboard-backend:${VERSION} ${DOCKERHUB}/bqp-dashboard-backend
	docker push ${DOCKERHUB}/bqp-dashboard-backend:${VERSION}
	docker push ${DOCKERHUB}/bqp-dashboard-backend 

