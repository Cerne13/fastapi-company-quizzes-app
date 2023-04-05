# APP 
###### (WIP)

#### Fastapi REST API app for running quizzes in companies
###### !!note: The project uses Databases instead of Sessions - just practiced to use more low-level interface

## Features
- Ready-to-use Docker/docker-compose configuration
- Full companies CRUD
- Full users CRUD (including roles in companies)
- Full quizzes and quiz questions CRUD
- Quiz results statistics for users/companies
- Scheduled notifications for users on quiz availability
- JWT tokens auth
- Auth0 auth
- Alembic db migrations
- Redis caching
- JSON and .csv export for quiz results
- Github workflow for AWS CI/CD

---
## Prerequisites
This app needs Python (preferably 3.11+) to be installed on your device.


---
## Installing the app
* Use your terminal and create a local repository in any folder using command
```commandline
git init
```
* Clone the app:
```commandline
git clone https://github.com/Cerne13/Meduzzen-FastApi-internship.git
```

* Move to the created folder

<br></br>

#### If you are using Linux/Mac:
First check if you have virtualenv installed:
```commandline
virtualenv --version
```
If you don't get version, you'll need to install the module:
```commandline
pip3 install virtualenv
```

* Create the environment
```commandline
python3 -m venv venv
```

* Activate it
```commandline
source venv/bin/activate
```

* Install all the needed dependencies:
```commandline
python -p install requirements.txt
```

<br></br>

#### If you are on Windows:
* Create virtual environment by entering:
```commandline
python -m venv venv
```

* Activate the environment:
```commandline
venv\Scripts\activate
```

* Install all the needed dependencies:
```commandline
python -p install requirements.txt
```


---
## Setting up environmental variables
In the root folder you have a file named .env.sample\
Create a file called '.env' in the root directory of the project and fill it with needed info
using the guidelines from the sample file provided.


---
## Running the app

#### Using terminal

Make sure you are in the project's root folder and run in terminal to start the server:

```commandline
uvicorn app.main:app --reload
```

#### Using 'run' option from opened file
Open the file 'app/main.py' and use 'run' option.


<br></br>

Then open the following url in your browser
```commandline
http://127.0.0.1:8000
```
to get the created endpoint data directly \
or to
```commandline
http://127.0.0.1:8000/docs
```
to use Swagger autodocs.


---
## Testing the app locally

To run tests, run the following command from the terminal:
```commandline
python -m pytest
```

---

---

# Deployment for production

* Build a docker image
```commandline
docker build -t [image_name]
```

* run the image in a container
```commandline
docker run --name [container_name] -p 8001:8000 [image_name]
```

After this you will be able to access the app by entering following in your browser:
```commandline
http://localhost:8001/
```

---
## Testing your containerized app
Run the container and type the following in the terminal:
```commandline
docker exec [container_name] python -m pytest
```
(or a bit shorter version)
```commandline
docker exec [container_name] pytest
```

---

## Running migrations in docker-compose container

- Make sure your Docker app is up and running
- Build and run the app with docker-compose by running the 
following from the terminal:
```commandline
docker-compose up
```

- To make new migration(revision):
```commandline
docker-compose run app alembic revision --autogenerate -m '[your_migration_name]'
```
(or use any message convenient for you)


- Apply the created migration:
```commandline
docker-compose run app alembic upgrade head
```
