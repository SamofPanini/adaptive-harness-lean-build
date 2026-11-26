# adaptive-harness-lean-build

公开的 Lean 4 构建与验证 runner。用 GitHub-hosted 标准 runner（4 vCPU / 16 GB / 14 GB）编译单文件 Lean 解答，做 axiom 审计、sorry/admit 扫描与 token 计数，并输出机器可读的运行收据。

- 只放公开内容：本仓库的 workflow 与脚本，以及来自公开仓库、带原许可与出处的 fixture。
- 不放任何私有数据、实验契约、判分期望或留出集；这些在另一个私有仓库里。
- 版本钉在 Lean 4.34.1 / Mathlib `d13f23b7`（与 Core1 公开复现所用的版本一致）。

状态：搭建中（R1）。
