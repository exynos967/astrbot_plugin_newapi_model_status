# astrbot_plugin_newapi_model_status

AstrBot 插件：查看并发送 `new_api_tools` 提供的模型健康度图卡。

## 功能

- `/模型情况`：手动获取当前已选模型的健康度图片（单张高分辨率长图）
- `/模型情况 <theme_id>`：临时指定本次出图主题
- `/模型情况主题`：查看可用主题列表
- `/模型情况会话`：管理员查看当前群号
- 可按插件配置向固定会话定时推送健康度图卡

## 配置说明

### 1. new_api_base_url

填写 `new_api_tools` 的根地址，例如：

- `http://127.0.0.1:3000`
- `https://newapi.example.com`

插件会自动尝试以下公开 embed 路由：

- `/api/model-status/embed/config/selected`
- `/api/model-status/embed/status/batch`
- `/api/embed/model-status/config/selected`
- `/api/embed/model-status/status/batch`

### 2. push_targets

在需要推送的QQ群里，让管理员执行：

```text
/模型情况会话
```

然后把返回的 **群号** 直接填到插件配置的 `push_targets` 中。

### 3. 远端 selected models

插件默认复用 `new_api_tools` 后台已经保存的选中模型。如果远端未配置 selected models，手动命令会直接提示去后台先完成配置。

## 渲染说明

- 当前版本固定将所有模型拼接为 **一张完整长图**
- 已提升画布宽度、字号和截图参数，优先保证文字清晰度
- 时间槽条已加宽，模型较多时会自动调整列数，尽量兼顾宽度与整图高度
- 支持 `new_api_tools` 模型健康度 embed 的全部主题 ID：
  - `daylight`
  - `obsidian`
  - `minimal`
  - `neon`
  - `forest`
  - `ocean`
  - `terminal`
  - `cupertino`
  - `material`
  - `openai`
  - `anthropic`
  - `vercel`
  - `linear`
  - `stripe`
  - `github`
  - `discord`
  - `tesla`
- 还支持 `follow_remote`：跟随远端 `new_api_tools` 后台当前主题

[new_api_tools](https://github.com/james-6-23/new_api_tools)
