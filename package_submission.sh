#!/bin/bash

cd "$(dirname "${BASH_SOURCE[0]}")"
rm -f submission.zip
zip -r submission.zip targets/ waa/ setup.py requirements.txt -x "*__pycache__*" -x "*.DS_Store" -x "*.pyc"
