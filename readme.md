# Setup Instructions

Follow these steps to set up your environment:

1. **Clone or Fork the Repository**
   - Begin by cloning or forking the repository to your local machine.

2. **Install Docker Daemon**
   - Ensure the Docker daemon is installed and running on your system. You can download Docker Desktop from the official Docker website for your platform.

3. **Create the Docker Image:**
   - Open your terminal and run the following command to build the Docker image:
     ```sh
     docker build -t dummy_image_name .
     ```

4. **Verify the Docker Image:**
   - Check that the image has been successfully created by listing all Docker images with:
     ```sh
     docker images
     ```

5. **Create and Run the Docker Container:**
   - Launch a new container from the image by running:
     ```sh
     docker run -d --name dummy_app_name -p 27017:27017 -p 5556:5556 dummy_image_name
     ```

6. **Test the Application:**
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

By following these steps, you can ensure your application is set up and tested successfully.

6. **Set up virtual environemnt**

- Make sure python version is 3.12.~ by running
 ```sh
     python --version
 ```
- navigate to your project directory, for example by running:
```sh
     cd pytest-api-test
```

```sh
     python -m venv env
```
This will create `env` folder in your project directory run: 
```sh
source env/bin/activate
```
This will activate the virtual environment located in the env folder. Post activation, your terminal prompt should change to reflect an active virtual environment, usually displaying (env) before the directory path. 

- Update pip to the latest version by executing:
```sh
 pip install --upgrade pip --trusted-host pypi.org --trusted-host files.pythonhosted.org
```
- install all required dependencies by running: 
```sh
 pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
```
