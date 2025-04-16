# Use an official lightweight Python runtime as the base image
FROM python:3.13.3-slim


# Prevent Python from buffering stdout and stderr (shows logs in real time)
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container to /app
WORKDIR /app

# Copy the requirements.txt file into the container at /app
COPY requirements.txt /app/requirements.txt

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . /app

# Expose port 5000 (default for Flask)
EXPOSE 5000
# Define the command to run your application
CMD ["python", "app.py"]
