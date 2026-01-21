
# WarriorFit API

A **FastAPI** backend application for accessing the WarriorFit database.

## Overview

This project provides a RESTful API to interact with the WarriorFit database. WarriorFit is a running event management system that allows you to register and track times of runners during running events.

## Features

- **Runner Registration**: Register participants for running events
- **Time Tracking**: Record and manage finish times for runners
- **Event Management**: Access and manage running event data
- **Database Integration**: Seamless connection to the WarriorFit database

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Flet (Python-based UI framework)
- **Package Manager**: uv

## Installation
gh repo sync
sudo docker stop api-warriorfit-app
sudo docker rm api-warriorfit-app
sudo docker build -t api-warriorfit-app .
sudo docker run -d --restart unless-stopped --name api-warriorfit-app -p 8555:8555 api-warriorfit-app






## API Documentation

Once the server is running, access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

# License

Copyright (c) 2025 Goethals Benoit

This source code is provided for viewing purposes only.

You may NOT:
- Use this code in any project
- Copy, modify, or distribute this code
- Use this code for commercial or non-commercial purposes

All rights reserved.