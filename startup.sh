#!/bin/bash
pip install -r /home/site/wwwroot/requirements.txt
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind=0.0.0.0:8000