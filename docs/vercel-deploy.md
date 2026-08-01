# Vercel 部署说明

## 当前方案

这个项目已经配置为：

- 本地开发默认使用 `SQLite`
- Vercel 部署时强制要求 `DATABASE_URL`
- Vercel 构建时自动执行：
  1. `npm ci --prefix frontend`
  2. `npm run build --prefix frontend`
  3. `python manage.py collectstatic --noinput`

Python 入口定义在 [pyproject.toml](/D:/2/pyproject.toml)，使用 `bid_agent.wsgi:application`。

## 部署前准备

1. 把代码推到 GitHub 仓库
2. 在 Vercel 中导入这个仓库
3. 在数据库服务中创建 PostgreSQL

推荐：

- Vercel Postgres
- Neon
- Supabase

## Vercel 环境变量

至少配置下面这些：

- `SECRET_KEY`
- `DATABASE_URL`
- `DEBUG=False`

如果你之后绑定自定义域名，再补：

- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`

## 首次部署后

部署成功后，进入 Vercel 项目的运行环境，执行 Django 迁移：

```bash
python manage.py migrate
```

如果需要后台管理员账号，再执行：

```bash
python manage.py createsuperuser
```

## 当前限制

`TenderDocument.file` 现在写入本地 `media/` 目录。Vercel 是无状态部署环境，这些上传文件不会稳定持久保存。

如果你准备正式使用上传 PDF 功能，下一步需要把文件存储迁到外部对象存储，例如：

- Vercel Blob
- Amazon S3
- Cloudflare R2
