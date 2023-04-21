FROM quay.io/astronomer/astro-runtime:7.4.2

USER root

# kubectl used to retrieve jwt pub keys
RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl \
    && chmod +x kubectl \
    && mv kubectl /usr/local/bin/

# step used to inspect and verify JWTs
RUN curl -LO https://dl.step.sm/gh-release/cli/docs-cli-install/v0.23.4/step-cli_0.23.4_amd64.deb \
    && dpkg -i step-cli_0.23.4_amd64.deb

USER astro


