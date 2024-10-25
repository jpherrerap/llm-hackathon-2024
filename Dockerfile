FROM python:3.11-slim
FROM node:18

# Set the working directory to /app
WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Make port 8000 available to the world outside this container
EXPOSE 8000
EXPOSE 0000

RUN npm install

# Run main.py when the container launches
CMD ["python", "-m", "main"]
CMD ["npm", "run", "dev"]