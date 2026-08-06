# 百度文字转语音 (Baidu TTS)

基于[百度AI开放平台语音合成](https://ai.baidu.com/tech/speech/tts)的 Home Assistant 自定义集成，将文本转换为高质量中文语音，可推送到媒体播放器播报。

## 特性

- **12 种发音人**：度小宇、度小美、度逍遥、度丫丫等，可在 UI 中切换
- **语速/音调/音量**：0-15 级可调
- **多种音频格式**：MP3、WAV、PCM 16kHz/8kHz
- **长文本支持**：自动按句子边界分段合成并无缝拼接，突破单次请求字数限制
- **流式输出**：支持 HA 新版 TTS 流式接口，边合成边播放，首字延迟更低
- **高性能**：aiohttp 连接复用 + 访问令牌缓存（30 天有效期），合成响应快
- **UI 配置**：完整的配置流程与选项流程，支持中文界面

## 环境要求

- Home Assistant **2026.8.0** 及以上
- 百度AI开放平台账号（语音合成服务有免费额度）

## 安装

### 方式一：HACS（推荐）

1. 打开 HACS → 集成 → 右上角菜单 → **自定义存储库**
2. 添加仓库地址 `https://github.com/ly2199/baidu_tts`，类别选择 **Integration**
3. 搜索 **百度文字转语音** 并安装，重启 Home Assistant

### 方式二：手动安装

将 `custom_components/baidu_tts` 目录复制到 Home Assistant 的 `config/custom_components/` 下：

```
config/
└── custom_components/
    └── baidu_tts/
        ├── __init__.py
        ├── client.py
        ├── config_flow.py
        ├── const.py
        ├── manifest.json
        ├── strings.json
        ├── translations/
        └── tts.py
```

重启 Home Assistant。

## 获取 API 凭证

1. 登录 [百度AI开放平台](https://console.bce.baidu.com/ai/)，创建**语音合成**应用
2. 在应用列表中获取 **API Key** 和 **Secret Key**

## 配置

1. 进入 **设置 → 设备与服务 → 添加集成**，搜索 **百度文字转语音**
2. 填入 API Key、Secret Key，选择发音人、语速等参数
3. 集成会自动验证凭证，验证通过后生成 TTS 引擎实体

之后可在集成的 **选项** 中随时调整发音人、语速、音调、音量和音频格式。

## 使用

### 服务调用

在 **开发者工具 → 动作** 中调用 `tts.speak`：

```yaml
action: tts.speak
data:
  cache: false
  media_player_entity_id: media_player.living_room
  message: "欢迎回家，今天的天气很好。"
target:
  entity_id: tts.baidu_tts
```

可选参数（覆盖默认配置）：

```yaml
data:
  message: "你好，世界"
  options:
    voice: "0"          # 发音人：0=度小美, 1=度小宇, 5003=度逍遥(精品) 等
    speed: 7            # 语速 0-15
    pitch: 5            # 音调 0-15
    volume: 10          # 音量 0-15
    audio_output: wav   # 输出格式：mp3 / wav / pcm-16k / pcm-8k
```

### 自动化示例

```yaml
automation:
  - alias: "门口有人按门铃"
    triggers:
      - trigger: state
        entity_id: binary_sensor.doorbell
        to: "on"
    actions:
      - action: tts.speak
        data:
          media_player_entity_id: media_player.living_room
          message: "有人按门铃，请注意查看。"
        target:
          entity_id: tts.baidu_tts
```

### 发音人列表

| ID | 发音人 | ID | 发音人 |
|---|---|---|---|
| 1 | 度小宇 | 106 | 度博文 |
| 0 | 度小美 | 110 | 度小童 |
| 3 | 度逍遥(基础) | 111 | 度小萌 |
| 4 | 度丫丫 | 103 | 度米朵 |
| 5003 | 度逍遥(精品) | 5 | 度小娇 |
| 5118 | 度小鹿 | 4146 | 度嘻嘻 |

## 常见问题

**配置时提示"无法连接百度认证服务"**
检查 Home Assistant 所在主机能否访问 `aip.baidubce.com`（网络/代理/DNS 问题）。

**提示"API Key 或 Secret Key 无效"**
确认凭证来自同一个语音合成应用，且应用已开通服务。

**合成报错"Token验证失败"**
集成会自动刷新令牌并重试；若持续出现请重新核对凭证。

**长文本播报不连续？**
2.0.0 版本已支持自动分段合成拼接，请确认已更新到最新版本。

## 版本历史

- **2.0.0**：适配 HA 2026.8（新版 TTS 实体 API、流式输出）；改用 aiohttp 连接复用；长文本自动分段拼接；令牌缓存跨重载保留；选项键 `speaker` 迁移为标准 `voice`
- **1.0.0**：首个版本

## 许可证

本项目基于 [Apache License 2.0](LICENSE) 开源。
