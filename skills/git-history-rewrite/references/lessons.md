# 历史改写常见坑速查（对照排查）

> 从真实历史改写（拆分发版提交、恢复时间、修正顺序）中沉淀的踩坑归纳，改写前对照排查一遍。

## 拆分提交类

- **取 %B 的顺序**：`git log -1 --format='%B' HEAD` 必须在 `git reset --soft HEAD^` **之前**执行——reset 后 HEAD 已是父提交，取到的是父的信息，提交会带上错误信息（曾把 v1.1.1 发版信息误标到 feat 提交上）。
- **reset --soft 后暂存区含全部改动**：必须先 `git restore --staged <不属于本提交的文件>` 移出，再提交第一批文件——否则第一个 commit 会把所有文件（含应进第二/第三个提交的）一起带走。
- **拆分的两个提交用同一时间**：一个提交拆成 N 个，N 个新提交的 author / committer 都沿用原提交时间。
- **commit --amend 默认保留原 author date**：要改 author 时间需加 `--reset-author`（配合 `GIT_AUTHOR_DATE`）；`GIT_COMMITTER_DATE` 单独即可改 committer。

## rebase 执行类

- **edit 标记可能静默失效**：`GIT_SEQUENCE_EDITOR` 的 sed 表达式按 todo 行 hash 前缀匹配；hash 缩写不一致或 sed 未匹配时，目标提交会被当 `pick` 重放——改写后必须逐个核对目标是否真的被处理（`git log` 对照）。
- **rebase 停在 edit 点时工作区可能残留改动**：amend 前没 `git add` 时，补丁留在工作区、amend 提交的是暂存区——提交后 `git status` 核对无残留。
- **重排一个提交 = 其后全部重放**：todo 中移动提交行后，其后的提交全部重写（committer 变重写当天），时间恢复的映射须覆盖被重放的全部提交，不只移动的那个。
- **rebase 起点**：`git rebase -i <起点>` 的 todo 只含起点**之后**的提交——起点选错会漏掉起点之前的待处理提交（曾漏掉 base 之前的 v1.1.0 改类型）。

## 时间恢复类

- **rebase / filter 后 committer 变当天**（author 保留）：恢复须同时设置 author 与 committer。
- **按信息匹配映射**：大多数提交信息未变，可在备份分支按 `%s` 精确匹配取原 `%at %ct`；改类型 / 拆分新建的提交信息不同，需手动映射表（新提交 → 原提交）。
- **filter-branch 的 `$GIT_COMMIT`**：是 filter-branch 运行时遍历的提交（即重写前的 hash），映射文件按它匹配。
- **author / committer 原值不同**（如作者 01:55 提交、08:55 amend）：恢复时分别取原 `%at` / `%ct`，不要统一。

## 发版提交类（改写涉及版本提交时）

- 发版提交（`chore(release): 发布 vX.Y.Z`）必须位于该版本**最后一个功能提交之后**——发版在前、功能在后会把功能排除在版本 tag 之外。
- 发版条目**一次写全**（覆盖该版本全部改动，含版本末尾才合入的功能）；创建后不得被后续提交修改（补记 / 修订说明都不行，补充记入下一版本条目）。
- 改类型时保留原 body：`git log -1 --format='%B' HEAD | sed '1s/.*/chore(release): 发布 vX.Y.Z/'` 只换标题。

## 验证与推送类

- **树一致性是硬标准**：改写后 `git diff backup/<分支> main` 应为空或仅方案声明的差异——任何未声明的差异都是改写错误。
- **强推前核对远程基线**：`--force-with-lease` 依赖本地 remote-tracking，改写前先 `git fetch`，避免误覆盖他人的新提交。
- **tag 重打后核对**：`git log -1 <tag>` 逐一确认指向方案声明的提交；`check-version.py --remote` 确认远程 tag / main 一致。
