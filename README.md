# Discounty

A Django application that scrapes local supermarket data and displays it with options to filter and sort by discounts and markets, and to create, export and mail shopping lists.

## Features

* Backend: Python 3.13 + Django 6.0.3
* Frontend: HTML + CSS + Bootstrap + Ajax + JavaScript
* Database: PostgreSQL
* (Optional) Scheduling: Celery 5.5 + Redis
* (Optional) Containerization: Docker + Docker Compose

## Setup

### 1. Prerequisites
Ensure you have **Git** installed.

### 2. Clone the repository and create a virtual environment
First clone the repository:
```
git clone https://github.com/sTodorovski/Discounty
cd Discounty
```

Afterwards create a virtual environment:

```
py -3.13 -m venv .venv
.venv\Scripts\Activate
```

### 3. Environment variables and dependencies
Copy the `.env.example` file and rename it to `.env` and change the placeholder values with the necessary data:
* DB_NAME - The name for the database that will store the supermarket and product data
* DB_USER - The username for the database admin
* DB_PASSWORD - The database admin's password
* DB_HOST - The host for the database
* DB_PORT - The port that the database will listen on
* EMAIL_HOST_USER - An email for the app's mailing service
* EMAIL_HOST_PASSWORD - The password for the email
* SECRET_KEY - A security key for the security-related Django operations

To install the dependencies listed in the `requirements.txt` file just run the following command:
```
pip install -r requirements.txt
```

### 4. Create a PostgreSQL database for the project
First create the PostgreSQL database in pgAdmin or using psql and ensure that the database environment variables from the `.env` file are also applied to the database variables.
```
CREATE DATABASE market_db;
```

Afterwards apply the migrations:
```
python manage.py migrate
```

### 5. Launching
To launch the scraper just run the following command:
```
python manage.py scrape_all
```
Afterwards to see the scraped data run the following command and launch the app in a browser:
```
.venv\Scripts\Activate
python manage.py runserver
```

### (Optional) 6. Dockerizing
In order to check the scraper scheduling that runs automatically at 9:00 the app needs to be dockerized first using these commands:

#### 6.1. Build and start the containers
```
docker compose up --build -d
```

#### 6.2. Apply the database migrations
```
docker compose exec web python manage.py migrate
```

#### 6.3. Run the scrapers
```
docker compose exec web python manage.py scrape_all
```

#### 6.4. (Optional) Monitor the scheduling process
```
docker compose logs -f beat
```

#### 6.5. (Optional) Monitor the scraping process
```
docker compose logs -f worker
```

#### 6.6. Launch the application
After/during the scraping process the app can be launched in the browser and the data will be updated periodically.
```
http://localhost:8000
```

#### 6.7. Close the Docker process
```
docker compose down
```
