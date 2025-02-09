from src import create_app
from src import db
from src.models import User, Health
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import time
from plyer import notification

app = create_app()

scheduler = BackgroundScheduler()

def send_hourly_message():
    notification.notify(
    title="Health Habits",
    message="Drink more water",
    app_icon='water2.ico',
    timeout=5)

scheduler.add_job(send_hourly_message, 'interval', minutes=1)

scheduler.start()

if __name__ == "__main__":
    app.run(debug=True)

