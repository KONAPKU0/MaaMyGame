# Codex Cloud 与 Android APK

Cloud 负责编辑、检查 Pipeline；APK 在 GitHub Actions 编译，不需要给 Cloud 安装 Android SDK/NDK。

## 依赖和上游文档

已阅读 MaaFramework 的快速开始、Pipeline 协议、Project Interface V2，以及 MaaFwApp 的 README、INTEGRATION 和打包配方。

- [MaaFramework 文档](https://github.com/MaaXYZ/MaaFramework/tree/main/docs/zh_cn)，检查时 main 为 `321cf1a22d1cdacd0a97d152e38eb4b83e158b2c`。
- [MaaFwApp 资源接入](https://github.com/Aliothmoon/MaaFwApp/blob/de65f7a43fc6a110706f44d756a0bf82b5c296d7/INTEGRATION.md)，以 `vendor/MaaFwApp` 子模块固定该提交。
- MaaFramework Python、Node 检查器使用 5.14.2；Actions 下载同版 Android arm64 库。
- `assets/MaaCommonAssets` 保留原有固定子模块提交；OCR 由 `tools/configure.py` 从子模块复制，不提交模型。
- npm 锁文件的镜像 URL 改为官方 registry，版本与 integrity 不变。

## Cloud 检查

从当前 checkout 操作，每个 Cloud 任务已隔离，不创建额外 worktree。

```bash
cd /workspace/MaaMyGame
git submodule update --init --recursive
python -m venv /workspace/maa-venv
/workspace/maa-venv/bin/python -m pip install -r tools/requirements-dev.txt
npm ci --cache /workspace/npm-cache --no-audit --no-fund
/workspace/maa-venv/bin/python tools/configure.py
npx --no-install @nekosu/maa-tools check
/workspace/maa-venv/bin/python tools/validate_schema.py --schema-dir deps/tools --resource-dirs assets/resource --exclude-dirs assets/resource/announcement --interface-files assets/interface.json
/workspace/maa-venv/bin/python tools/prepare_android.py
/workspace/maa-venv/bin/python tools/check_runtime.py
```

Python 虚拟环境在仓库外，Node 原生检查库缓存位于忽略的 `build/maa-tools`。运行时检查实际加载资源与 OCR，确认任务入口存在；这不是手机截屏、点击或游戏行为测试。

## APK 构建

提交并推送这些配置后，main 分支相关文件变动或 PR 会触发 **Android APK**；也可在 Actions 手动运行。工作流初始化子模块、校验资源、铺入 Android 库，使用上游 Gradle wrapper、JDK 17、SDK 37、CMake 3.22.1 编译 `assembleDebug`，限制为 arm64。NDK 由 AGP 按默认版本安装，不改上游代码。

下载成功运行的 `MaaMyGame-arm64-debug-<commit>` artifact 中的 APK。这是可安装的调试签名包，不是正式发行签名包；无需配置签名密钥。正式发行应另行配置安全签名流程。工作流只上传 artifact，不创建 Release。

`android/pi-profile.yaml` 指向 `build/android-pi`。生成目录保留源资源，但将 Android 界面限制为模板现有 `MyTask1`、`MyTask2`、`MyTask3` 三个纯 Pipeline 任务和 Adb 类型控制器。模板自定义识别任务需要 Python Agent，现阶段不在 Android 任务列表中；源 interface 和 Agent 保持原样。三个空示例任务仅验证装配，没有具体游戏操作。

构建后 `verify_apk.py` 打开真实 APK 的 `assets/pi.zip`，逐文件比对暂存资源的 SHA-256，检查三个任务入口、OCR 模型及 arm64 原生库。随后 `apksigner verify` 验证签名，任一检查失败都不上传成功产物。不能把单独打资源 ZIP 的本地检查当成 APK 构建成功。

## 手机验收与限制

Android 9+、arm64 手机需要 Shizuku 或 root；无需连接电脑持续运行。安装后授权、连接特权服务，确认任务列表显示三个模板任务，再运行普通任务。实际手机权限、native controller、截图与点击尚需真机验证。每次变更资源重新编译 APK；如果同版本安装后仍显示旧资源，清应用数据或使用应用的重新解压资源功能。

GitHub Actions 必须读取已提交的配置才能运行。本地环境中 Git 读取可用，但检查时 GitHub API 返回 Forbidden，未取得远程构建结果。首次成功运行与 APK 内资源验证通过之前，不能声称自动构建成功。

MaaFwApp 使用 AGPL-3.0；分发 APK 时应遵循上游许可证并提供相应源码。
