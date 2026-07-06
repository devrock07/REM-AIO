#!/bin/bash
hypercorn server:app --bind 0.0.0.0:$PORT
