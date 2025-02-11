#!/bin/bash

helm upgrade --wait --install frigate frigate --namespace frigate --create-namespace
#helm upgrade --wait --install keycloak keycloak --namespace keycloak --create-namespace
