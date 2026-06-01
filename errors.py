"""插件内部异常定义。"""


class PluginConfigurationError(ValueError):
    """插件配置缺失或不合法。"""


class NewApiRequestError(RuntimeError):
    """调用 new_api_tools 接口失败。"""


class RemoteSelectionEmptyError(RuntimeError):
    """远端未配置 selected models。"""

