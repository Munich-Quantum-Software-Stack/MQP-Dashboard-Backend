
$(eval VERSION=$(shell grep -m 1 version pyproject.toml | tr -d '"' | cut -d' ' -f3 | tr -s ' ' | tr -d "'" ) )

DOCKERHUB=dockerhub.quantum.lrz.de


build-image:
	docker build --no-cache -t bqp-dashboard-backend -t bqp-dashboard-backend:${VERSION} --build-arg PYTHONUNBUFFERED="1" --build-arg QUANTUM_DB_USER="dashboard" --build-arg QUANTUM_DB_PASS="FopiWunoDiwe" --build-arg QUANTUM_DB_HOST="localhost" --build-arg QUANTUM_DS_HOST="ldaps://auth.sim.lrz.de:636" . 

push-image:
	docker tag bqp-dashboard-backend:${VERSION} ${DOCKERHUB}/bqp-dashboard-backend:${VERSION}
	docker tag ${DOCKERHUB}/bqp-dashboard-backend:${VERSION} ${DOCKERHUB}/bqp-dashboard-backend
	docker push ${DOCKERHUB}/bqp-dashboard-backend:${VERSION}
	docker push ${DOCKERHUB}/bqp-dashboard-backend 

