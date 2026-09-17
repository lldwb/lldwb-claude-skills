#!/usr/bin/env bash
# filter-branch --index-filter 模板：批量替换历史中某文件的内容（改哪三处见下）
#
# 为什么用 --index-filter 而不是 --tree-filter：
#   tree-filter 会把每个提交检出到工作区，文件行尾由 core.autocrlf 决定（true → CRLF），
#   而仓库对象里通常是 LF —— 依赖行尾的替换（`^…$` 锚定、多行字面量）在 CRLF 上静默
#   失配：脚本 exit 0、内容却没换（曾因此把整个改写重做一遍）。index-filter 直接改索引里
#   的 blob（始终是仓库对象形态），不检出文件，只改个别文件时更快也更稳。
#
# 用法（被 filter-branch 逐个提交调用，工作目录为工作树根）：
#   git filter-branch --index-filter 'bash <本脚本路径>' <改写范围>
# 替换模式**不锚行尾**（不写 `$`），两种行尾下都成立。
#
# 改这三处：① TARGET 目标文件 ② DETECT 命中即处理 ③ 下面的 sed 规则。
# 上 filter-branch 前先 dry-run：用同一组 sed 规则在临时检出上跑一遍、比对替换条数
# （`grep -c`）与方案一致，再改历史 —— 规则写错只会在改完后才暴露。
set -e

TARGET="CHANGELOG.md"
# 命中才处理：不含目标内容的提交原样通过（grep 失配不算错误）。
DETECT='^### \(Added\|Changed\|Fixed\|Security\|Breaking\)'

# 该提交里没有此文件（新增文件的提交、改名前的提交）时原样跳过。
if ! git ls-files --error-unmatch "$TARGET" >/dev/null 2>&1; then
  exit 0
fi

blob=$(git rev-parse :"$TARGET")
if git cat-file blob "$blob" | grep -q "$DETECT"; then
  newblob=$(git cat-file blob "$blob" | sed \
    -e 's/^### Added/### 新增/' \
    -e 's/^### Changed/### 变更/' \
    -e 's/^### Fixed/### 修复/' \
    -e 's/^### Security/### 安全/' \
    -e 's/^### Breaking/### 破坏性变更/' \
    | git hash-object -w --stdin)
  git update-index --cacheinfo 100644 "$newblob" "$TARGET"
fi

exit 0
