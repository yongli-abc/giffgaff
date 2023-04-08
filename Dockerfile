# Set the base image
FROM python:3.9-slim-buster

# Set the working directory
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install the dependencies
RUN pip install -r requirements.txt

# Copy the application code to the working directory
COPY index.py .
COPY settings.py .
COPY ./mail ./mail
COPY ./static ./static
COPY ./templates ./templates

# Set the FLASK_APP environment variable
ENV FLASK_APP=index.py
ENV FLASK_ENV=development

# Expose the default Flask port
EXPOSE 5000

# Start the Flask application
CMD ["flask", "run", "--host=0.0.0.0"]