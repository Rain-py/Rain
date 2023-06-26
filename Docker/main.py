import docker

# Create a Docker client
client = docker.from_env()

# Pull a Docker image
client.images.pull('nginx:latest')

# Run a container
container = client.containers.run('nginx:latest', detach=True)

# Get container details
container.reload()
print('Container ID:', container.id)
print('Container Status:', container.status)

# Execute a command inside the container
output = container.exec_run('ls /')
print('Command Output:', output.output.decode())

# Stop and remove the container
container.stop()
container.remove()