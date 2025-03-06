# Use an official Python image as the base
FROM python:3.11

# Set the working directory
WORKDIR /app

# Copy the project files to the container
COPY . /app/

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install -r requirements.txt

# Expose the port Django runs on
EXPOSE 8000

# Command to start the Django server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
