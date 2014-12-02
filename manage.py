#!/usr/bin/env python
import os
import sys
from dns import dgachecker

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "PassiveDNS.settings")

    dgachecker.init()

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
