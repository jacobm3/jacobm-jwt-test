FROM quay.io/astronomer/astro-runtime:7.4.2

# kubectl
RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl
RUN chmod +x ./kubectl
USER root
RUN mv ./kubectl /usr/local/bin

# cli tool to inspect and verify jwt tokens
RUN curl -LO https://dl.step.sm/gh-release/cli/docs-cli-install/v0.23.1/step-cli_0.23.1_amd64.deb
RUN dpkg -i step-cli_0.23.1_amd64.deb

USER astro