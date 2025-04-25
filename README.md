
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
