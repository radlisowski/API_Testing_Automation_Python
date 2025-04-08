FROM docker.io/library/mongo:latest
# Use the latest official MongoDB image from Docker Hub as the base image.
# This provides an environment with MongoDB already installed and ready to run.

USER root
# Specify that the following operations will be run with root user privileges,
# enabling installation of software packages.

# Install Python and dependencies
RUN apt-get update && \
    apt-get install -y python3-venv && \
    mkdir -p /data/db /data/configdb
# Update package lists to ensure latest versions, then install Python's venv module to enable virtual environments.
# Create directories commonly used by MongoDB to store database and configuration data.

# Create a virtual environment
RUN python3 -m venv /app/venv
# Create a Python virtual environment in the /app/venv directory, isolating Python dependencies from the system.

# Activate the virtual environment and install Python dependencies
COPY requirements.txt /app/requirements.txt
# Copy the requirements.txt file from the local project into the Docker image at /app directory.
RUN /app/venv/bin/python -m pip install  \
    --no-cache-dir  \
    --trusted-host pypi.org  \
    --trusted-host files.pythonhosted.org  \
    -r /app/requirements.txt
# Activate the virtual environment and install Python packages listed in requirements.txt
# without caching to reduce image size. Use trusted-host options to bypass SSL verification
# (ensure security best practices are considered for actual use).

COPY . /app
# Copy the entire project into the /app directory of the Docker image, including all application code.

WORKDIR /app
# Set the working directory to /app where all subsequent commands will be executed from.

EXPOSE 27017 5556
# Declare that the container listens on network ports 27017 (MongoDB) and 5556 (application),
# making them accessible externally.

CMD mongod --bind_ip 0.0.0.0 --port 27017 --fork --logpath /var/log/mongodb.log && \
    /app/venv/bin/python /app/app.py
# Commands to start MongoDB server, binding it to all network interfaces and logging output to a specified file.
# Run the Python application using the virtual environment's Python executable, launching the application.
