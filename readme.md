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

