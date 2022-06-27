import json
import pytest
import logging

from lambd import app

def test_lambda_handler(caplog):
    caplog.set_level(logging.INFO)
    app.lambda_handler({}, {})
