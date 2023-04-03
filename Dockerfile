FROM quay.io/astronomer/astro-runtime:7.4.2

RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl
RUN chmod +x ./kubectl
USER root
RUN mv ./kubectl /usr/local/bin
USER astro