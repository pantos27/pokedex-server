
# Pokedex API

A Flask-based API for Pokemon data.

## Setup and Installation

### Option 1: Local Development

```shell
pip install -r requirements.txt
python run.py
```

### Option 2: Docker Development

This project includes Docker support with hot-reloading, which means the application will automatically update when you make changes to the code.

#### Prerequisites
- Docker and Docker Compose installed on your system

#### Running with Docker Compose

1. Build and start the container:
```shell
docker-compose up --build
```

2. Access the API at http://localhost:5000

3. For subsequent runs (if Dockerfile hasn't changed):
```shell
docker-compose up
```

4. To stop the container:
```shell
docker-compose down
```

#### How Hot-Reloading Works

The Docker setup includes:
- Volume mounting of the project directory to the container
- Flask's debug mode enabled to detect file changes
- Container configured to restart automatically

When you modify any Python file in the project, Flask will detect the change and automatically restart the server, making your changes immediately available.

## Testing

This project uses pytest for testing. The tests are located in the `tests` directory and are organized as follows:

- `conftest.py`: Contains pytest fixtures for setting up the test environment
- `test_repository.py`: Tests for the data access layer
- `test_api.py`: Tests for the API endpoints

### Running Tests

To run the tests, execute the following command from the project root:

```shell
python -m pytest
```

This will run all tests and display the results, including test coverage information.

### Test Coverage

The tests cover the following functionality:

- Repository layer: Data access functions for Pokemon, users, and captures
- API endpoints: All endpoints for retrieving Pokemon data, user management, and Pokemon captures

Current test coverage is over 90%, ensuring that most of the codebase is tested.

### Adding New Tests

When adding new features, please also add corresponding tests to maintain high test coverage. Follow the existing patterns in the test files for consistency.
