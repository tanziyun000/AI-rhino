# Residential Unit Generator MVP

## 目标

为矩形公寓边界生成满足基本规则的户型方案，并输出可复用的 Rhino / JSON / CSV 结果。

## 当前结构

- `configs/`：项目配置
- `docs/`：设计说明与路线图
- `gh/`：Grasshopper 文件与 Python 脚本
- `results/`：批量生成结果
- `tests/`：单元测试
- `prompts/`：AI 协作 prompt

## 快速开始

```bash
# 1) 运行核心原型
python residential-unit-generator/run_prototype.py residential-unit-generator/configs/default_3br.json 20 residential-unit-generator/results

# 2) 跑矩阵
python residential-unit-generator/tools/run_unit_matrix.py residential-unit-generator/configs/unit_matrix.json --count 5

# 3) 生成报告包
python residential-unit-generator/tools/generate_report_pack.py residential-unit-generator/configs/unit_matrix.json --unit-count 5 --policy-count 1

# 4) 单独生成 dashboard
python residential-unit-generator/tools/make_dashboard.py --matrix-report residential-unit-generator/results/unit_matrix/matrix_report.json --policy-matrix-report residential-unit-generator/results/policy_matrix/policy_matrix_report.json --pack-summary residential-unit-generator/results/report_pack_summary.json --out residential-unit-generator/results/dashboard.html
```

## 报告包

推荐一键命令：

```bash
python residential-unit-generator/tools/generate_report_pack.py residential-unit-generator/configs/unit_matrix.json --unit-count 5 --policy-count 1
```

常用变体：

```bash
# 只打印命令，不执行
python residential-unit-generator/tools/generate_report_pack.py residential-unit-generator/configs/unit_matrix.json --dry-run

# 跳过 dashboard
python residential-unit-generator/tools/generate_report_pack.py residential-unit-generator/configs/unit_matrix.json --skip-dashboard

# 只校验已有产物
python residential-unit-generator/tools/generate_report_pack.py residential-unit-generator/configs/unit_matrix.json --verify

# 指定 summary 输出
python residential-unit-generator/tools/generate_report_pack.py residential-unit-generator/configs/unit_matrix.json --json-summary residential-unit-generator/results/custom_summary.json
```

## 验证

```bash
python residential-unit-generator/tests/run_tests.py
```

## 开发顺序

1. 纯 Python 原型
2. Grasshopper Python 封装
3. Rhino 输出
4. 批量生成
5. AI 协作与迭代
