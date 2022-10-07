# See here for image contents: https://github.com/microsoft/vscode-dev-containers/tree/v0.245.2/containers/codespaces-linux/.devcontainer/base.Dockerfile

FROM mcr.microsoft.com/vscode/devcontainers/universal:2-focal

USER root

COPY packages.txt /root/packages.txt
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && xargs -r -a /root/packages.txt apt-get install -y

USER codespace