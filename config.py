import yaml

class Config(dict):
    __getattr__ = dict.__getitem__

    def __init__(self):
        configFile = open('config.yaml')
        data = yaml.load(configFile)
        for key in data:
            dict.__setitem__(self, key, data[key])
