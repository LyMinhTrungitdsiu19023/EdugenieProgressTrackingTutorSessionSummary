# Use an official AWS Python runtime for Lambda as a base image
FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.11

# Copy requirements.txt
COPY . ${LAMBDA_TASK_ROOT}

# Install any required Python dependencies specified in requirements.txt
RUN pip install -r requirements.txt

# Run your Python program
CMD ["handler.main"]