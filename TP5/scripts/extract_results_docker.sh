#Get folders and files from Docker container

# Container name
CONTAINER_NAME="modest_torvalds"

# Copy se.py from docker container to current directory
if docker exec -it $CONTAINER_NAME ls "/workspace/gem5/configs/example/se.py" > /dev/null 2>&1; then
    docker cp "$CONTAINER_NAME:/workspace/gem5/configs/example/se.py" .
    echo "Copied se.py from container to current directory."
else
    echo "File se.py does not exist in the container."
fi



# Check if the folder exists in the container
if docker exec -it $CONTAINER_NAME ls "/workspace/TP5" > /dev/null 2>&1; then
    # Copy the folder from the container to the current directory
    docker cp "$CONTAINER_NAME:/workspace/TP5" ./results_TP5
    echo "Copied TP5 folder from container to current directory."
else
    echo "Folder TP5 does not exist in the container."
fi
