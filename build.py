
# -*- coding: UTF-8 -*-
# ((dir, config, global_log_path,True)

import worker
import os
import json
import sys


def read_config_file(path):
    if not os.path.exists(path):
        print("config file is not found, please check file")
        return None
    with open(path) as file:
        return json.load(file)
    print('open file faild, please check file type is json')
    return None


length = len(sys.argv)
if length != 3:
    print('parameter error')
    sys.exit(1)

workspace = sys.argv[1]
config_path = sys.argv[2]

# 单独构建
worker.worker((workspace,read_config_file(config_path), workspace,True))




