FROM ubuntu:20.04

# Install dependencies
RUN apt-get update && apt-get install -y \
  python3-pip \
  curl \
  rsync \
  && rm -rf /var/lib/apt/lists/*

# Create non-root user
ARG UID=1000
RUN echo "Building image with \"worker\" user ID: ${UID}"
RUN useradd --create-home --shell /bin/bash worker --uid ${UID}
USER worker
WORKDIR /home/worker

# Install the required Python modules:
COPY --chown=worker:worker ./requirements.txt .
ENV PATH="/home/worker/.local/bin:${PATH}"
RUN pip3 install --user -r requirements.txt

# Copy in remaining server module files
COPY --chown=worker:worker ./ ./

CMD ["/bin/bash", "-c", "cd server && python3 server.py"]
