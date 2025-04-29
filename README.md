# Documentation
## Read-only / educational access / MQP_EDU user
27-11-2024 In bqp_dashboard_backend/tokens.py, we hardcoded, that users in the user group MQP_EDU (table users_in_user_groups in the quantum database) are returned only "ThisIsAnEducationalTokenItCannotBeUsedToSubmitJobsThisIsAnEducat" as a token, which is not useable to submit jobs. 
TODO If this token is encountered by the frontend, it will display a banner "This is an educational token, it cannot be used to submit jobs".

# Unit testing with pytest
In order for the unit-tests to run, following environment-variables need to be set (test_db.db can in principle be anything except already existing files): 
```
export QUANTUM_DB_TESTING=1
export QUANTUM_DB_FILENAME=test_db.db
export QUANTUM_DS_HOST=ldap://localhost:8888
```