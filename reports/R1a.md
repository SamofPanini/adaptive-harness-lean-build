# R1a 执行报告

## ① 交付物清单

- `runner/`：版本参数、单 fixture 验证、注释与字符串扫描、token 计数、收据、setup 和 fixture 调度。
- `fixtures/public/core1/`：三份公开解答、MIT 许可、来源与 SHA-256。
- `.github/workflows/verify.yml`：手动触发的单 job workflow。
- `tests/`：不依赖 Lean 的扫描、token 和收据测试。
- `README.md`：手动触发、收据字段、版本修改说明。

## ② 单元测试原样输出

`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v`，退出码 0：

```text
test_every_required_field (tests.test_runner.ReceiptTests) ... ok
test_exit_verdict_mapping (tests.test_runner.ReceiptTests) ... ok
test_step_fields (tests.test_runner.ReceiptTests) ... ok
test_comments_strings_nested (tests.test_runner.ScanTests) ... ok
test_sorry_and_admit (tests.test_runner.ScanTests) ... ok
test_word_boundaries (tests.test_runner.ScanTests) ... ok
test_hand_count (tests.test_runner.TokenTests) ... ok

----------------------------------------------------------------------
Ran 7 tests in 0.002s

OK
```

## ③ shell 语法与无 Lean 环境检查

`bash -n runner/*.sh`：无输出，退出码 0。

在 PATH 不包含 Lean、Lake 的环境中，对公开 fixture 运行 `verify_one.sh`：

```text
ENV_ERROR: Lean, Lake, Mathlib cache, source, or required tools unavailable
verdict_raw=ENV_ERROR
```

退出码 10；同时生成 `verdict_raw: ENV_ERROR` 的收据。

## ④ 待 Actions 验证

- elan 安装、钉定工具链及指定 Mathlib revision 的浅获取。
- `lake exe cache get` 在该 revision 上的实际缓存命中、依赖获取、耗时和磁盘占用；确认不会从零构建 Mathlib。
- 缓存缺失或 revision 不存在时 setup 收据为 `INFRA_FAIL`，每个 fixture 收据为 `ENV_ERROR`，artifact 仍上传且 job 正常结束。
- `lake env` 搜索路径、实际 Lean 编译、超时与 GNU time 峰值内存记录。
- 实际 Lean 版本的公理输出格式、陈述 `#check` 输出与空白规范化哈希；额外公理、sorry/admit、编译失败和超时的收据。
- 多 fixture 连续执行、输入通配符、临时 base64 文件及 artifact 完整性；实际资源及时间是否满足 90 分钟限制。

## ⑤ 规格偏差

无。没有可用的 Lean 环境和联网权限，运行时行为列入 ④，未声称离线验证通过。

## ⑥ 成本观察

单元测试 7 项本机用时 0.002 秒；其他两项检查均在本机快速完成。Lean 安装、缓存与编译的时间和资源成本尚待 Actions 实测。

## ⑦ Skill 摩擦

Skill 摩擦：无
