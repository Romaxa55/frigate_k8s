#!/bin/bash

helm upgrade --install frigate ./frigate --namespace frigate --create-namespace --set-file configContent=config.yaml
#helm upgrade --wait --install keycloak keycloak --namespace keycloak --create-namespace
