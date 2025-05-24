#!/bin/bash

helm upgrade --install frigate frigate --namespace frigate --create-namespace
#helm upgrade --wait --install keycloak keycloak --namespace keycloak --create-namespace
