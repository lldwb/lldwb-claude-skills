# git-history-rewrite

Git 历史改写：对既有提交做结构性修正（拆分 / 改类型 / 重排 / 删除 / 恢复时间），含备份分支、方案先行、四重验证与强推。

## 使用

当用户要求"把某次提交拆成两个""把版本号从功能提交里拆出去""统一历史提交类型""移动发版提交位置""删除历史补记""恢复重写后的提交时间"时触发。

```bash
# 改写前先备份（名字带主题后缀，避免与同日其他备份重名）
git branch backup/<分支>-<日期>[-<主题>]
```

**边界**：把分支回滚到历史版本（`reset` / `revert`）用 `git-rollback`；清理分支用 `git-clean-branches`；只评审提交质量、不改写用 `commit-review`。

## 能力

- 五类结构性修正：拆分提交（一次提交按文件拆成多个）、改类型/标题、重排顺序、删除提交、恢复提交时间
- 发版提交特有规则：`chore(release): 发布 vX.Y.Z` 只动版本文件、位于该版本最后一个功能提交之后、条目一次写全且创建后不可修改
- 批量替换历史内容：`filter-branch --index-filter` 跨多个提交替换同一处文本（模板见 `references/index-filter.sh`，绕开 `core.autocrlf` 的行尾陷阱）
- 四重验证：树一致性（`git diff backup/<分支> <分支>`）、提交规则、时间语义、tag 指向——全通过才强推
- 安全边界：改写须显式确认；强推用 `--force-with-lease`（外加 `--force` 推 tags），影响说明与用户确认缺一不可；`reflog expire` / `gc --prune=now` / `filter-repo` 不做

## 文件

| 文件 | 说明 |
|------|------|
| `SKILL.md` | 技能指令（备份 → 方案 → 改写 → 时间恢复 → 重打 tag → 四重验证 → 强推） |
| `references/lessons.md` | 常见坑速查（备份与基线、拆分顺序、rebase 执行、批量替换、时间恢复、发版提交、验证与推送） |
| `references/index-filter.sh` | `--index-filter` 批量替换脚本模板（改目标文件 / 命中模式 / sed 规则三处即可用） |

## 依赖

- git（`rebase` / `filter-branch` / `tag` / `push` 等标准命令）
- 无额外依赖；`check-version.py`（仓库根）用于改写后的版本一致性核对
