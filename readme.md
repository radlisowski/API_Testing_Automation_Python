# Setup Instructions

By following these steps, you can ensure your application is set up and tested successfully.

1. **Clone or Fork the Repository**
   - Begin by cloning or forking the repository to your local machine using Git Desktop (free).
   - Open the repository in PyCharm (free) 

2. **Install Python and set up virtual environment**

- Install Python, version 3.12
- Make sure python version is 3.12.~ by running
 ```sh
     python --version
 ```
- make sure you are in your project directory or navigate to your project directory, for example by running:
```sh
     cd pytest-api-test
```
- create a virtual environment called `env` for your project 
```sh
     python3 -m venv env
```
>This will create env folder in your project directory that will allow for separating anything you do on the 
project form your machine environment (installing additional modules for the framework will only affect the 
environment you have created.)
> 
>**python3:** This specifies the Python interpreter version to use. Here, python3 is selected, ensuring you're using 
Python 3, which is recommended over Python 2 due to its extended support and features.
**-m:**
This flag tells Python to run a module as a script. In this case, it runs the venv module, which is used for 
creating lightweight virtual environments.
> 
>**venv:**
This is the module being run to create a new virtual environment. venv is included in the standard library for 
Python 3.x and is used to create isolated environments for Python projects.
> 
>**env:**
This is the name of the directory where the virtual environment will be created. You can name this directory 
anything you'd like, but env or venv are common conventions. This directory will contain the Python interpreter, 
a copy of the pip tool, and other files supporting the isolated environment.

- run the below to activate the enviremnt: 
 ```sh
source env/bin/activate
```

- Update pip to the latest version by executing:
>"Pip Installs Packages." It is the package management system used in Python to install 
and manage software packages.
```sh
 pip install --upgrade pip --trusted-host pypi.org --trusted-host files.pythonhosted.org
```
- install all required dependencies by running: 
```sh
 pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
```
pip install -r requirements.txt:

>**-r:** Tells pip to read and install from the specified requirements file.
requirements.txt: A text file that lists packages and their versions to be installed. 
Each line in this file typically contains a package name and an optional version specifier, e.g., package==1.0.0.
> 
>**--trusted-host:** These flags tell pip to trust the specified hosts. This is often used when you need to bypass SSL 
verification warnings that occur when installing packages from certain repositories.
> 
>**pypi.org and files.pythonhosted.org:** These entries specify trusted hosts that are part of the 
default Python Package Index’s hosting.

## Follow these steps to set up your docker image:
> We use the docker containers to host the endpoint and the database that wre will be testing.

1. **Install Docker Daemon**
   - Ensure the Docker daemon is installed and running on your system. You can download Docker Desktop from the official Docker website for your platform.

2. **Create the Docker Image:**
   - Open your terminal and run the following command to build the Docker image:
     ```sh
     docker build -t dummy_image_name .
     ```
>**docker build:** This command tells Docker to build an image from a Dockerfile. The build process involves reading 
> the instructions in the Dockerfile to create an image layer by layer, sequentially executing the commands specified in the file. 
> 
>-**t dummy_image_name:**
The `-t` (or `--tag`) option assigns a name and optionally a tag (in the format name:tag) to the image being built. 
In this case, `dummy_image_name` is used as the name of the image. This tag is useful for identifying and versioning 
images, making them easier to manage and reference in later commands, such as when running a container or pushing 
the image to a Docker registry.
> 
> **.**
>The period (`.`) at the end of the command specifies the build context, which is typically the current directory. 
This context includes the Dockerfile and any files the Dockerfile relies on for building the image.
Docker will package the current directory and send it to the Docker daemon, where the build process takes place.
3. **Verify the Docker Image:**
   - Check that the image has been successfully created by listing all Docker images with:
     ```sh
     docker images
     ```

4. **Create and Run the Docker Container:**
   - Launch a new container from the image by running:
     ```sh
     docker run -d --name dummy_app_name -p 27017:27017 -p 5556:5556 dummy_image_name
     ```
> **docker run**:  
> This command creates and starts a new container from a specified Docker image. The container runs as an isolated process on your host machine.
>
> **-d**:  
> The **`-d`** (or `--detach`) option runs the container in detached mode, meaning it runs in the background rather than in the current terminal session. This allows you to continue using the terminal for other commands while the container runs.
>
> **--name dummy_app_name**:  
> This assigns a name to the container being created. In this case, the container is named **`dummy_app_name`**. Naming containers makes them easier to manage, reference, and identify in commands like `docker ps`, where you view running containers.
>
> **-p 27017:27017 -p 5556:5556**:  
> These options map network ports between the Docker host (your machine) and the container. Each mapping has the format **`host_port:container_port`**.  
> - **`27017:27017`**: Maps port 27017 on the Docker host to port 27017 in the container. This is typically used for MongoDB, which listens on port 27017 by default.  
> - **`5556:5556`**: Maps port 5556 on the Docker host to port 5556 in the container. This might be used for a web service or API your application exposes on that port.  
>
> **dummy_image_name**:  
> This is the name or ID of the Docker image from which to create the container. It must be an image available locally or in a Docker registry if not present locally.

5. **Test the Application:**
   - To verify that the app is working correctly, send a POST request via terminal:
     ```sh
     curl -X POST http://localhost:5556/user/ \
          -H "Content-Type: application/json" \
          -d '{
                "username": "johndoe",
                "email": "johndoe@example.com",
                "role": "tester",
                "addresses": [
                  {
                    "street": "123 Elm St",
                    "city": "Metropolis",
                    "country": "Utopia",
                    "phone_numbers": [
                      {"type": "home", "number": "555-1234"},
                      {"type": "work", "number": "555-5678"}
                    ]
                  }
                ]
              }'
     ```
- you should get result looking like this:
     ```sh
     {"username":"johndoe","role":"tester","email":"johndoe@example.com","addresses":[{"street":"123 Elm St","city":"Metropolis","country":"Utopia","phone_numbers":[{"type":"home","number":"555-1234"},{"type":"work","number":"555-5678"}]}],"user_id":1}%      

     ```
