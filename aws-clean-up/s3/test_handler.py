import json

import pytest

from s3 import app
import logging

def test_lambda_handler(caplog):
    caplog.set_level(logging.INFO)
    app.lambda_handler({}, {})
