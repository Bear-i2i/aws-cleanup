import json
import pytest
from dynamo import app
import logging

def test_lambda_handler(caplog):
    caplog.set_level(logging.INFO)
    app.lambda_handler({}, {})
