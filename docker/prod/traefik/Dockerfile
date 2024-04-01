FROM docker.io/traefik:2.11.0
RUN mkdir -p /etc/traefik/acme \
  && touch /etc/traefik/acme/acme.json \
  && chmod 600 /etc/traefik/acme/acme.json
COPY ./docker/prod/traefik/traefik.yml /etc/traefik
