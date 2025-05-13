#!/bin/bash

exec fastapi run _main.py --port 8000 &
exec python3 health_checker.py