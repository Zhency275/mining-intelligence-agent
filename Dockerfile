# Mining Intelligence Agent — Docker Image
# Build: docker build -t mining-intelligence-agent .
# Run:   docker run -e ANTHROPIC_API_KEY=sk-ant-... mining-intelligence-agent

FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create reports directory
RUN mkdir -p /app/reports

# The agent client is the entry point
ENTRYPOINT ["python", "-m", "agent_client.main"]
CMD ["--help"]
