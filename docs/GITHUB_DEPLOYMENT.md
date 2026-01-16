# GitHub 部署指南

## 📋 部署前准备

### 1. 检查文件

确保以下文件已创建：
- ✅ `.gitignore` - Git忽略文件
- ✅ `README.md` - 项目说明
- ✅ `.env.example` - 环境变量模板（可选）

### 2. 检查敏感信息

确保以下文件/内容不会被提交：
- ❌ `.env` - 包含API密钥
- ❌ `config.json` - 如果包含敏感配置
- ❌ `*.db` - 数据库文件
- ❌ `*.pkl` - 训练好的模型（可选）
- ❌ `*.csv` - 数据文件（可能很大）

## 🚀 部署步骤

### 方法1：使用Git命令行（推荐）

#### 1. 初始化Git仓库

```bash
cd binance-futures-trading
git init
```

#### 2. 添加文件

```bash
# 添加所有文件（.gitignore会自动排除敏感文件）
git add .

# 检查将要提交的文件（确保没有敏感文件）
git status
```

#### 3. 创建首次提交

```bash
git commit -m "Initial commit: 币安期货强化学习交易系统 v3.0"
```

#### 4. 在GitHub创建仓库

1. 登录GitHub
2. 点击右上角 "+" → "New repository"
3. 填写仓库信息：
   - Repository name: `binance-futures-trading`
   - Description: `基于强化学习的币安期货自动化交易系统`
   - Visibility: Private（推荐）或 Public
   - **不要**勾选 "Initialize with README"
4. 点击 "Create repository"

#### 5. 连接远程仓库并推送

```bash
# 添加远程仓库（替换yourusername为你的GitHub用户名）
git remote add origin https://github.com/yourusername/binance-futures-trading.git

# 或者使用SSH（如果配置了SSH密钥）
# git remote add origin git@github.com:yourusername/binance-futures-trading.git

# 推送代码
git branch -M main
git push -u origin main
```

### 方法2：使用GitHub Desktop

1. 下载并安装 [GitHub Desktop](https://desktop.github.com/)
2. 登录GitHub账号
3. File → Add Local Repository
4. 选择项目目录
5. 填写提交信息
6. 点击 "Publish repository"
7. 选择仓库名称和可见性
8. 点击 "Publish Repository"

### 方法3：使用GitHub CLI

```bash
# 安装GitHub CLI（如果未安装）
# Windows: winget install GitHub.cli
# Mac: brew install gh
# Linux: 参考 https://github.com/cli/cli

# 登录GitHub
gh auth login

# 创建并推送仓库
gh repo create binance-futures-trading --private --source=. --remote=origin --push
```

## ✅ 验证部署

部署成功后，访问你的GitHub仓库页面，检查：

1. ✅ README.md 正确显示
2. ✅ 代码文件都在
3. ✅ `.env` 文件**不在**仓库中
4. ✅ `*.db` 文件**不在**仓库中
5. ✅ `__pycache__/` 目录**不在**仓库中

## 🔒 安全检查清单

部署前请确认：

- [ ] `.env` 文件已添加到 `.gitignore`
- [ ] `config.json` 如果包含敏感信息，已添加到 `.gitignore`
- [ ] 所有数据库文件（`*.db`）已排除
- [ ] API密钥没有硬编码在代码中
- [ ] 训练数据文件（如果很大）已排除
- [ ] 个人敏感信息已移除

## 📝 后续更新

### 日常更新代码

```bash
# 1. 查看更改
git status

# 2. 添加更改
git add .

# 3. 提交更改
git commit -m "描述你的更改"

# 4. 推送到GitHub
git push
```

### 创建新分支

```bash
# 创建并切换到新分支
git checkout -b feature/new-feature

# 提交更改
git add .
git commit -m "添加新功能"

# 推送到远程
git push -u origin feature/new-feature

# 在GitHub上创建Pull Request
```

## 🐛 常见问题

### 1. 推送被拒绝（Push rejected）

**原因**: 远程仓库有本地没有的提交

**解决**:
```bash
git pull --rebase origin main
git push
```

### 2. 不小心提交了敏感文件

**解决**:
```bash
# 从Git历史中移除文件（但保留本地文件）
git rm --cached .env
git commit -m "Remove sensitive file"
git push

# 如果已经推送，需要重写历史（谨慎使用）
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all
git push --force
```

### 3. 文件太大无法推送

**原因**: GitHub限制单个文件100MB

**解决**:
- 使用 Git LFS（Large File Storage）
- 或者将大文件添加到 `.gitignore`

## 📚 相关资源

- [Git官方文档](https://git-scm.com/doc)
- [GitHub文档](https://docs.github.com/)
- [GitHub Desktop文档](https://docs.github.com/en/desktop)

---

**提示**: 如果这是私有仓库，只有你和你授权的用户可以访问。如果是公开仓库，任何人都可以看到代码。

































