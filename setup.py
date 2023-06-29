import asyncio

async def run_command(command):
    # Run the command in a subprocess
    process = await asyncio.create_subprocess_shell(command)
    await process.communicate()

async def run_commands_concurrently(commands):
    # Create tasks for running each command concurrently
    tasks = [run_command(command) for command in commands]
    await asyncio.gather(*tasks)

# Example commands to run concurrently
commands = [
    'python3 ./provisioner.py',
    'cd ./Worker/ && python3 ./worker.py',
    'cd ./Coordinator && python3 ./coordinator.py ',
    ]

# Run the commands concurrently
asyncio.run(run_commands_concurrently(commands))
