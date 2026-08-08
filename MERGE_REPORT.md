# Agnes AI Studio 上游合并报告（LGQLIFE V7）

> 合并时间：2026-08-08
> 合并提交：`422aed4` (Merge commit on `master`)

## 一、合并对象与关系

| 项 | 内容 |
|---|---|
| 上游（被 fork 的远端） | `LGQLIFE/agnes-ai-studio` master，V7（`3d3fd4c`） |
| 当前分支 | 本地 `master`（基于 v6 `d1ff9e3` + 本地 4 个提交） |
| 共同祖先 | `d1ff9e3` "This is v6 version" |
| 分叉情况 | 本地 4 提交（Docker/剧本/drama）、上游 1 提交（V7），双向独立演进 |
| 合并提交 | `422aed4` |

## 二、取舍原则

- **重叠功能**：取上游更新实现（V7 为更新版本）
- **互补功能**：双方独有且互不冲突的代码均保留

## 三、冲突文件处理（共 3 个文件 14 处冲突）

| 文件 | 冲突数 | 处理方式 |
|---|---|---|
| `src/routes/drama.py` | 7 | 以 V7 为基底；本地独有的"剧本编辑"系列（`edit/story`、`edit/script`、`edit/storyboard`、`edit/confirm`、`style-presets`、`optimize-prompt`、`cancel`）被 V7 的 `story/confirm`、`shot/upload_image`、`shot/delete_image`、`merge/custom` 取代 |
| `src/services/video_gen.py` | 1 | 以 V7 为基底，**补回本地独有**的 `build_agnesapi_url` / `fetch_video_url_from_agnesapi`（通过 anesapi 取视频 URL，与 V7 的 video_id 下载互补） |
| `static/index.html` | 6 | 以 V7 为基底（前端采用上游新版 UI） |

## 四、自动合并保留的本地独有改进（无冲突）

- Docker 配置：`Dockerfile`、`docker-compose.yml`、`.dockerignore`、`.github/workflows/docker-build.yml`
- Agnes API 地址 / 视频轮询 API 修正（`config.py`）
- 新增模型字段（`models.py`）
- `text_model.py` / `app.py` 等改进

## 五、运行验证

| 检查 | 结果 |
|---|---|
| Python 语法校验（全部 .py） | ✅ 通过 |
| 本地 Flask（`127.0.0.1:5000`） | ✅ 200 |
| 公网（`https://agnes.abcc.us.ci`，经 CF 隧道） | ✅ 200 |

## 六、详细代码审查结论（2026-08-08 复审）

### 通过项 ✅
- 语法校验：全部 `.py` 通过 `py_compile`
- 无重复定义：`video_gen.py` 内函数名唯一
- import 完整性：`drama.py` 从 `video_gen` import 的 `download_and_save_file` / `download_video_by_video_id` 均已定义
- 前后端路由一致：`index.html` 调用的 **19 个 `/api` 端点全部有对应后端路由，零断链**
- 本地独有改进（Docker 配置、`config.py` API 修正、`models.py` 新增字段、`text_model.py`/`app.py` 改进）在自动合入中均保留

### 待处理项 ⚠️
1. **anesapi 孤儿函数（已处理）**：补回的 `build_agnesapi_url` / `fetch_video_url_from_agnesapi` 合并后零处调用，已按审查结论**选 B 删除**（commit `e0df722`，移除 52 行死代码）。
2. **`build/`、`dist/` 二进制构建产物（已确认保留）**：用户决定保留上游 V7 带入的构建产物，仓库维持现状。

### 取舍确认
- 本地"剧本编辑 edit/*"系列及对应前端 UI 已被 V7 的 `story/confirm` + 镜头图片管理 + 自定义合并取代，符合"重叠功能取上游新版本"原则。

## 七、待确认 / 可选后续

1. **本地"编辑剧本/分镜"细粒度功能**被 V7 取代（V7 提供"编辑故事梗概 + 镜头图片管理 + 自定义合并"）。如仍需本地更细粒度的剧本/分镜编辑 UI，可尝试加回（需前后端协调）。
2. **anesapi 函数已保留但未接入 V7 下载流程**。如需让 V7 下载在失败时回退到 anesapi，可加兜底分支。
3. 合并**仅在本地**，未 push 到 `origin`（mayishidai）。建议 review 后 `git push origin master`。
4. 建议实测：文生图、文生视频、短剧生成，确认 V7 逻辑正常。
