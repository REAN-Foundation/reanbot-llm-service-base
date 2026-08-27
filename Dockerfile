FROM python:3.11-slim

# Optional: prevent interactive prompts during install
ENV DEBIAN_FRONTEND=noninteractive

# System dependencies
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    libgl1 \
    curl \
    unzip \
    libpcre2-8-0 \
    libxml2 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Create virtual environment
RUN python -m venv /venv

# Install Python dependencies
COPY requirements.txt .
RUN /venv/bin/pip install --upgrade pip setuptools wheel
RUN /venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Start the application
CMD ["/venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]

# Start with Ubuntu as the base image
# FROM ubuntu:24.04

# EXPOSE 80

# # Update the system and install necessary dependencies
# # RUN apt-get update && apt-get upgrade -y

# RUN apt-get update && apt-get upgrade -y && \
#     apt-get install -y \
#     python3\
#     python3-pip \
#     libglib2.0-0 \
#     libsm6 \
#     libxrender1 \
#     libxext6 \
#     libgl1 \
#     curl \
#     unzip \
#     python3-venv && \
#     apt-get clean && \
#     rm -rf /var/lib/apt/lists/*

# # Set Python 3.10 as the default python3
# # RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

# RUN rm /bin/sh && ln -s /bin/bash /bin/sh

# WORKDIR /app

# RUN python3 -m venv /venv

# COPY requirements.txt requirements.txt

# RUN /venv/bin/pip install --no-cache-dir -r requirements.txt

# COPY . .

# CMD ["/venv/bin/uvicorn","main:app","--host","0.0.0.0","--port","80"]

#############################

# FROM ubuntu:22.04

# # Update the system and install necessary dependencies
# RUN apt-get update && apt-get upgrade -y
# RUN apt-get install -y \
#     python3.10 \
#     python3-pip \
#     libglib2.0-0 \
#     libsm6 \
#     libxrender1 \
#     libxext6 \
#     libgl1-mesa-glx \
#     curl \
#     unzip

# # Set Python 3.10 as the default python3
# RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

# RUN rm /bin/sh && ln -s /bin/bash /bin/sh

# WORKDIR /app

# COPY requirements.txt requirements.txt

# RUN pip3 install --no-cache-dir -r requirements.txt

# COPY . .

# CMD ["uvicorn","main:app","--host","0.0.0.0","--port","80"]
