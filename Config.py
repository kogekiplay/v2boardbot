import yaml


class Config:
    class DATABASE:
        database = None
        host = None
        password = None
        user = None
        to_dict = None

    class TELEGRAM:
        admin_telegram_id = None
        http_proxy = None
        https_proxy = None
        token = None
        title = None
        to_dict = None

    class WEBSITE:
        email = None
        password = None
        suffix = None
        url = None
        to_dict = None

    class TIGER:
        rate = None
        switch = None
        to_dict = None

    class DICE:
        rate = None
        switch = None
        to_dict = None

    class AUTODELETE:
        status = True

    class __ConfigSection:
        def __init__(self, section_dict):
            for key, value in section_dict.items():
                setattr(self, key, value)

        def to_dict(self):
            return {
                attr: getattr(self, attr)
                for attr in dir(self)
                if not callable(getattr(self, attr)) and not attr.startswith("__")
            }

        def __getattr__(self, item):
            setattr(self, item, f"{item}未配置")
            return getattr(self, item)

    def __init__(self, config_path="config.yaml"):
        self.config = self._load_config(config_path)
        self._load_attributes()

    def __getattr__(self, item):
        print(item, "不存在")
        setattr(self, item, self.__ConfigSection({}))
        return getattr(self, item)

    def _load_config(self, config_path):
        with open(config_path, "r", encoding="utf8") as fp:
            return yaml.safe_load(fp)

    def _load_attributes(self):
        for section, values in self.config.items():
            if values:
                section_obj = self.__ConfigSection(values)
                setattr(self, section, section_obj)
            else:
                setattr(self, section, values)

    def save(self, config_path="config.yaml"):
        saved_config = {}
        for section_name, section_obj in self.__dict__.items():
            if isinstance(section_obj, self.__ConfigSection):
                saved_config[section_name] = section_obj.to_dict()
        with open(config_path, "w") as fp:
            yaml.dump(saved_config, fp)

        self.config = saved_config


config = Config()
