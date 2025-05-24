#!/bin/bash

helm upgrade --wait --install frigate2 frigate --namespace frigate2 --create-namespace -f frigate/values-second.yaml
#helm upgrade --wait --install keycloak keycloak --namespace keycloak --create-namespace
