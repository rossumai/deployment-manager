FROM python:3.12-slim

RUN mkdir /app/
WORKDIR /app

# Git is required in post_gen_project
RUN apt-get update && apt install git -y && apt-get install -y gcc && apt-get install curl -y && apt-get install make
# Add testing git identity
RUN git config --global user.email "test@example.com"
RUN git config --global user.name "Test Name"

# Install and configure poetry to be able to install from exe-tools repository
ARG ROSSUM_PYPI_USERNAME=
ARG ROSSUM_PYPI_PASSWORD=

RUN pip install --upgrade pip
RUN pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry config http-basic.exe-tools "${ROSSUM_PYPI_USERNAME}" "${ROSSUM_PYPI_PASSWORD}"

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}" \
    VIRTUAL_ENV="/opt/venv"

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-interaction --no-root


ARG GIT_COMMIT=unknown
ARG CODE_PROJECT_PATH=unknown

ENV CODE_VERSION_SHA=$GIT_COMMIT \
    CODE_PROJECT_PATH=$CODE_PROJECT_PATH

LABEL code-version-sha=$CODE_VERSION_SHA \
    code-project-path=$CODE_PROJECT_PATH

COPY . ./

RUN echo "{\"code_version_hash\": \"$CODE_VERSION_SHA\"}" > /info.json
