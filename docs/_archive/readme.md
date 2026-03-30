## docx-convert（pipx 安装版）

一个极简 CLI，调用 LibreOffice 将 `.doc` 转成 `.docx`。默认输出同目录、文件名加 `_DOC_Converted` 后缀，便于与源文件区分。

### 安装（pipx）
1. 确认已安装 LibreOffice，命令行里能执行 `soffice --version`。macOS 默认路径：`/Applications/LibreOffice.app/Contents/MacOS/soffice`。
2. 安装 pipx（任选其一）：
   - macOS（Homebrew）：`brew install pipx && pipx ensurepath`
   - 纯 Python：`python3 -m pip install --user pipx && python3 -m pipx ensurepath`
3. 用 pipx 从 GitHub 安装本工具（把 `<your-repo-url>` 换成你创建的仓库地址，例如 `https://github.com/you/docx-convert.git`）：
   ```sh
   pipx install git+<your-repo-url>
   ```

### 使用
- 基础转换（生成 `*_DOC_Converted.docx`）：
  ```sh
  docx "/path/to/file.doc"
  ```
- 保留 LibreOffice 默认生成的同名 `.docx`（不加后缀）：
  ```sh
  docx "/path/to/file.doc" --keep-original-name
  ```
- LibreOffice 不在 PATH 时指定可执行文件：
  ```sh
  docx "/path/to/file.doc" --soffice "/Applications/LibreOffice.app/Contents/MacOS/soffice"
  ```

### 错误排查
- 提示找不到 soffice：确认已安装 LibreOffice，或用 `--soffice` 指定实际路径。
- 转换后未生成文件：检查源文件路径是否正确；可手动运行命令 `soffice --headless --convert-to docx --outdir ...` 验证 LibreOffice 是否正常。
