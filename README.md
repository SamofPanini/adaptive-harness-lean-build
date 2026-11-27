# adaptive-harness-lean-build

公开的 Lean 4 构建与验证 runner。用 GitHub-hosted 标准 runner（4 vCPU / 16 GB / 14 GB）编译单文件 Lean 解答，做 axiom 审计、sorry/admit 扫描与 token 计数，并输出机器可读的运行收据。

- 只放公开内容：本仓库的 workflow 与脚本，以及来自公开仓库、带原许可与出处的 fixture。
- 不放任何私有数据、实验契约、判分期望或留出集；这些在另一个私有仓库里。
- 版本钉在 Lean 4.34.1 / Mathlib `d13f23b7`（与 Core1 公开复现所用的版本一致）。

状态：搭建中（R1）。

## 怎么手动触发

在 GitHub Actions 的 **Verify Lean fixtures** 页面选择 **Run workflow**。`fixtures` 是空格分隔的路径或通配符；留空选用公开 fixture。`mathlib_rev` 可覆盖默认版本；`extra_b64` 可注入一份 base64 编码的 Lean 文件。收据和日志位于运行生成的 `lean-receipts` artifact。

编译成功后还会运行 Comparator 链：landrun、lean4export、Comparator 与 nanoda。工具版本固定在 `runner/versions.env`。

## 收据字段

每个 `receipt.json` 包含 fixture ID、文件 SHA-256、版本、各步骤退出码和耗时、原始状态 `verdict_raw`、公理、sorry 命中、新增 axiom 声明、目标陈述原文和规范化空白后的 SHA-256、token 计数、峰值内存、Mathlib 磁盘占用、运行机器信息及起止时间。未能取得的数据为 null 或空列表。`setup_receipt.json` 记录工具链、Mathlib 和缓存步骤、磁盘余量及 setup 状态。收据只记录观察值，不判断目标陈述。`setup_receipt.json` 的 `comparator_status` 为 OK、INFRA_FAIL 或 SKIPPED；单文件收据的 `comparator` 记录状态、退出码、耗时、峰值内存和日志末尾，完整日志另存。退出码 40 表示 Comparator 拒收，11 表示 Comparator 工具错误、超时或跳过；原有 31、30 优先。

## 版本在哪改

修改 `runner/versions.env` 中 Lean、Mathlib 与四个 Comparator 链工具的固定版本；workflow 默认读取该文件，手动输入 `mathlib_rev` 时使用输入的 revision。
