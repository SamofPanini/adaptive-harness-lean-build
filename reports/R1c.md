# R1c 执行报告

## ① 产物清单

- `fixtures/public/challenge/`：Challenge、Comparator 配置及来源。
- `runner/`：固定版本、工具构建和模板、独立 judge、Comparator 分类与收据扩展。
- `.github/workflows/verify.yml`：配置 Go；`tests/`：离线测试；`README.md`：使用与收据说明。

## ② 单元测试原样输出

```text
test_classification (tests.test_comparator.ComparatorTests) ... ok
test_codes_and_priority (tests.test_comparator.ComparatorTests) ... ok
test_judge (tests.test_comparator.ComparatorTests) ... ok
test_receipt_comparator_required (tests.test_comparator.ComparatorTests) ... ok
test_statement_matches_public_source (tests.test_comparator.ComparatorTests) ... ok
test_every_required_field (tests.test_runner.ReceiptTests) ... ok
test_exit_verdict_mapping (tests.test_runner.ReceiptTests) ... ok
test_step_fields (tests.test_runner.ReceiptTests) ... ok
test_comments_strings_nested (tests.test_runner.ScanTests) ... ok
test_sorry_and_admit (tests.test_runner.ScanTests) ... ok
test_word_boundaries (tests.test_runner.ScanTests) ... ok
test_hand_count (tests.test_runner.TokenTests) ... ok

----------------------------------------------------------------------
Ran 12 tests in 0.011s

OK
```

## ③ shell 与无 Lean 检查原样输出

```text
bash -n exit=0
ENV_ERROR: Lean, Lake, Mathlib cache, source, or required tools unavailable
verdict_raw=ENV_ERROR
verify_one.sh exit=10
```

## ④ 待 Actions 验证

- comparator 和 lean4export 改写 toolchain 后是否能成功构建及运行；comparator 的 manifest pin 是否正确解析。
- landrun 在 GitHub runner 上是否可用；预装 cargo 和 Go stable 能否构建固定版本。
- judge 的 path 依赖与 packagesDir 是否解析、能否复用已解压 Mathlib 缓存，且不会重编 Mathlib；Comparator 沙箱对这些路径的访问是否足够。
- 模板 Challenge 编译及 #check 文本和哈希是否按预期取得；各类 fixture 的 Comparator 日志、状态和收据是否完整。
- Comparator 与 nanoda 的真实耗时、峰值内存及 1800 秒超时行为；整个任务是否适合 90 分钟。

## ⑤ 偏离

- Comparator 的 `Main.lean:297–300` 先运行外部 kernel，然后通过 `<|>` 决定是否运行 Lean 内建 kernel；规格的已知事实将顺序写反。本实现调用官方程序，按源码执行。
- 规格所述公开来源的第 1–12 行含两行注释，实际只提取 import 与 open；第 128–129 行的目标陈述去掉 `_root_.` 后逐字一致。四个固定 commit 与提供的实物一致。
- 模板 Challenge 采用已有 Mathlib 环境中的 `lean -o` 构建，避免模板构建触发 Mathlib 重编；judge 中 Lake 的行为需在 Actions 核验。

## ⑥ 成本观察

离线验证 12 项单元测试约 0.011 秒；本次未运行 Lean 构建，实际工具构建与 Comparator 的时间、内存和缓存成本未知。

## ⑦ Skill 摩擦

Skill 摩擦：无
