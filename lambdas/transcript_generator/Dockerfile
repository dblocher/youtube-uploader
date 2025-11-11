FROM public.ecr.aws/lambda/python:3.11

# Install ffmpeg and ffprobe
RUN yum install -y wget tar xz && \
    wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz && \
    tar xf ffmpeg-release-amd64-static.tar.xz && \
    mv ffmpeg-*-amd64-static/ffmpeg /usr/local/bin/ && \
    mv ffmpeg-*-amd64-static/ffprobe /usr/local/bin/ && \
    rm -rf ffmpeg-* && \
    yum clean all

# Copy requirements and install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy function code
COPY handler.py ${LAMBDA_TASK_ROOT}/

# Set the CMD to your handler
CMD ["handler.lambda_handler"]
