# Documentation

## Read-only / educational access / MQP_EDU user

27-11-2024 In bqp_dashboard_backend/tokens.py, we hardcoded, that users in the user group MQP_EDU
(table users_in_user_groups in the quantum database) are returned only
"ThisIsAnEducationalTokenItCannotBeUsedToSubmitJobsThisIsAnEducat" as a token, which is not useable
to submit jobs. TODO If this token is encountered by the frontend, it will display a banner "This is
an educational token, it cannot be used to submit jobs".

# Unit testing with pytest

In order for the unit-tests to run, following environment-variables need to be set (test_db.db can
in principle be anything except already existing files):

```
export QUANTUM_DB_TESTING=1
export QUANTUM_DB_FILENAME=test_db.db
export QUANTUM_DS_HOST=ldap://localhost:8888
```

# Environmental Configuration
To run the project locally, you need to configure your environment variables:
    1. Locate the .env.example file in the project root
    2. Create a copy of this file and rename it to .env
    3. Open the .env file and update the configuration values to match your local setup.
    4. The application runs inside a container. To make these environment variables affect to the app, run this command: $make run-image