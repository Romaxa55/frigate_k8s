#!/bin/bash

helm upgrade --wait --install frigate frigate --namespace frigate --create-namespace
