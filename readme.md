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
