# Findings

## Initial Inventory

- 根目录已有核心文档：`README.md`、`product_spec.md`、`project_spec.md`、`PROJECT_STATUS.md`、`CHANGELOG.md`
- `docs/` 下当前只有 `ERROR_LOG.md`、`TDD_WORKFLOW.md`、`PRODUCT_STRATEGY.md`
- `documents/` 下有生成出来的示例文档，属于产品样例而非项目治理文档
- 仓库存在未提交修改：`README.md`、若干 `src/` 与 `tests/` 文件

## Early Hypotheses

- 根目录规格文档较多，职责边界不够清晰，容易产生重复和口径漂移
- 产品策略已经更新到 `docs/PRODUCT_STRATEGY.md`，但尚未同步到主说明和规格文档
- `PROJECT_STATUS.md` 可能包含历史口径，需与代码现状重新对齐

## Documentation Problems Confirmed

- `README.md` 仍将产品表述为宽泛的“knowledge document generator”，未体现聚焦到技术教程 / 学习指南的方向
- `product_spec.md` 仍按旧版“泛文档生成器”定义需求，没有纳入需求澄清、控纲、局部重写、反馈回灌、学习路线、面试精选等新方向
- `project_spec.md` 混合了当前实现、历史设想和未实现模块，且部分目录结构与实际代码不完全一致
- `PROJECT_STATUS.md` 中测试数量、覆盖率、最新执行情况存在旧口径；当前本地验证结果为 `109 passed, 1 skipped`
- `.claude/CLAUDE.md` 的项目概述和文档索引尚未同步最新产品战略
- `documents/` 下内容属于示例产物，不应与项目治理文档混为一类

## Proposed Documentation Roles

- `README.md`：面向首次进入仓库的读者，负责定位、快速开始、核心能力和文档导航
- `product_spec.md`：面向产品和需求讨论，负责产品定义、核心场景、需求边界与版本路线
- `project_spec.md`：面向实现和架构，负责系统模块、数据流、扩展点和技术约束
- `PROJECT_STATUS.md`：面向当前状态同步，负责已完成能力、已验证结果、已知缺口和近期计划
- `CHANGELOG.md`：保留变更记录职责，不承载现状判断
- `docs/PRODUCT_STRATEGY.md`：保留中长期战略方向
- `docs/TDD_WORKFLOW.md`、`docs/ERROR_LOG.md`：保留工程实践文档
- 新增文档索引文件，用于定义完整文档结构和每份文档职责

## OpenSpec-Style Decision

- 采用增量方式引入变更级 spec，而不是替换现有项目级文档
- 项目级文档负责长期共识，`specs/` 目录负责单次功能变更的执行契约
- 第一份 spec 选择“Design Brief / 需求澄清流程”，因为它是后续控纲和重写能力的基础
