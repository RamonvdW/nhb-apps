#!/bin/bash
pip-compile requirements.in
pip-compile requirements_test.in
pip-compile requirements_dev.in
