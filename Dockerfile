FROM python:3.11-slim
RUN apt-get -y update
RUN apt-get -y install git
# Set the working directory to /app
WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Make port 8000 available to the world outside this container
EXPOSE 8000


# Run main.py when the container launches
CMD ["python", "-m", "main"]