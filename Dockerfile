# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container to /app
WORKDIR /app

# Add the current directory contents into the container at /app
ADD . /app

# Install any needed packages specified in requirements.txt
RUN pip install pip-tools
RUN pip-sync

# Make port 8501 available to the world outside this container
EXPOSE 8501

# Run the command to start the app
CMD ["streamlit", "run", "app.py"]