# /bin/bash


# Build Docker image
docker build -t gem5 .

# Remove existing container if it exists
docker rm -f gem5_container || true


# Run Docker container
docker run -it --rm --name gem5_container gem5


## To execute a command inside the running container, use:
docker exec -it gem5_container /bin/bash