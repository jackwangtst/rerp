# 认证服务 ERP 系统

面向 ISO 认证服务公司的业务管理系统，涵盖市场线索、客户管理、合同收款、认证项目全流程。

## 技术栈

| 层次 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Vite + Element Plus |
| 后端 | Python 3.12 + FastAPI + SQLAlchemy 2.0（异步） |
| 数据库 | PostgreSQL 16 |
| 反向代理 | Nginx |
| 容器化 | Docker + Docker Compose |

---

## 目录结构

```
rerp/
├── backend/          # FastAPI 后端
├── frontend/         # Vue 3 前端
├── nginx/            # Nginx 配置
├── docs/             # 文档及数据库 schema
├── uploads/          # 上传文件（运行时生成）
├── backups/          # 数据库备份（运行时生成）
└── docker-compose.yml
```

---

## 部署指南

### 环境要求

- Docker >= 24.0
- Docker Compose >= 2.20
- 磁盘空间 >= 10 GB

### 一、克隆代码

```bash
git clone <仓库地址>
cd rerp
```

### 二、配置环境变量

```bash
cp backend/.env.example backend/.env
```

编辑 `backend/.env`，**至少修改以下两项**：

```env
# 数据库连接（Docker 内部网络，通常无需改动）
DATABASE_URL=postgresql+asyncpg://rerp:rerp_password@db:5432/rerp

# 务必替换为随机强密码，用于 JWT 签名
SECRET_KEY=your-very-long-random-secret-key-here

# Token 有效期（分钟），默认 8 小时
ACCESS_TOKEN_EXPIRE_MINUTES=480

# 上传文件目录（容器内路径，通常无需改动）
UPLOAD_DIR=/app/uploads
```

生成安全的 `SECRET_KEY`：

```bash
openssl rand -hex 32
```

### 三、构建前端

前端需先编译为静态文件，再由 Nginx 提供服务：

```bash
# 使用 Docker 构建（推荐，无需本地安装 Node）
docker compose --profile build run --rm frontend

# 或在本地构建（需 Node 18+）
cd frontend
npm install
npm run build
cd ..
```

构建产物输出至 `frontend/dist/`。

### 四、配置 SSL 证书

#### 方案 A：使用 Cloudflare Tunnel（推荐，无需证书文件）

Cloudflare Tunnel 在外层自动管理 HTTPS，Nginx 只需监听 HTTP：

1. 修改 `nginx/nginx.conf`，将两个 `server` 块替换为仅监听 80 端口的单块：

```nginx
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass         http://backend:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    location /uploads/ {
        proxy_pass       http://backend:8000;
        proxy_set_header Host $host;
    }
}
```

2. `docker-compose.yml` 中 nginx 的 `ports` 仅保留 `"80:80"`，移除 `"443:443"`。

#### 方案 B：自签名证书（局域网 / 测试用）

```bash
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem \
  -subj "/CN=localhost"
```

#### 方案 C：正式 SSL 证书

将证书文件放置于 `nginx/ssl/` 目录：

```
nginx/ssl/
├── cert.pem    # 证书链（含中间证书）
└── key.pem     # 私钥
```

### 五、启动服务

```bash
# 后台启动所有服务
docker compose up -d

# 查看启动日志
docker compose logs -f
```

首次启动时，PostgreSQL 会自动执行 `docs/schema.sql` 完成建表。

验证各服务状态：

```bash
docker compose ps
```

所有服务应显示 `healthy` 或 `running`。

### 六、初始化管理员账号

数据库就绪后，执行以下命令创建默认管理员（用户名 `admin`，密码 `admin123`）：

```bash
docker compose exec backend python -c "
import asyncio
from app.core.database import AsyncSessionLocal
from app.models.user import SysUser
from app.core.security import get_password_hash

async def create_admin():
    async with AsyncSessionLocal() as db:
        user = SysUser(
            username='admin',
            hashed_password=get_password_hash('admin123'),
            full_name='管理员',
            role='admin',
            is_active=True
        )
        db.add(user)
        await db.commit()
    print('管理员账号已创建')

asyncio.run(create_admin())
"
```

**创建后请立即登录并修改密码。**

### 七、访问系统

| 场景 | 地址 |
|------|------|
| 局域网（HTTP） | `http://<服务器IP>` |
| 局域网（HTTPS） | `https://<服务器IP>` |
| Cloudflare Tunnel | 由 Tunnel 配置决定 |
| API 文档 | `http://<服务器IP>/api/docs` |

---

## 本地开发

### 后端

```bash
cd backend

# 创建并激活虚拟环境
python3.12 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（指向本地 PostgreSQL）
cp .env.example .env
# 修改 DATABASE_URL 为 postgresql+asyncpg://rerp:rerp_password@localhost:5432/rerp

# 启动开发服务器
uvicorn app.main:app --reload --port 8000
```

### 前端

```bash
cd frontend

npm install

# 启动开发服务器（自动代理 /api 至 localhost:8000）
npm run dev
```

前端开发服务器默认运行在 `http://localhost:5173`。

---

## 数据库管理

### 备份

```bash
docker compose exec db pg_dump -U rerp rerp > backups/rerp_$(date +%Y%m%d_%H%M%S).sql
```

### 恢复

```bash
docker compose exec -T db psql -U rerp rerp < backups/rerp_20240101_120000.sql
```

### 进入数据库控制台

```bash
docker compose exec db psql -U rerp rerp
```

---

## 常用运维命令

```bash
# 查看服务状态
docker compose ps

# 查看后端日志
docker compose logs -f backend

# 重启单个服务
docker compose restart backend

# 停止所有服务（保留数据）
docker compose down

# 停止并删除所有数据（慎用）
docker compose down -v

# 重新构建后端镜像（修改代码后）
docker compose build backend
docker compose up -d backend

# 更新前端（修改前端代码后）
docker compose --profile build run --rm frontend
docker compose restart nginx
```

---

## 升级流程

```bash
# 1. 拉取新代码
git pull

# 2. 备份数据库
docker compose exec db pg_dump -U rerp rerp > backups/pre_upgrade_$(date +%Y%m%d).sql

# 3. 重新构建前端
docker compose --profile build run --rm frontend

# 4. 重新构建并重启后端
docker compose build backend
docker compose up -d

# 5. 验证服务正常
docker compose ps
docker compose logs --tail=50 backend
```

---

## 群晖 NAS 部署指南

群晖 NAS 通过 Container Manager（即 Docker）运行本系统，操作全程可在 DSM 图形界面完成。

### 前置条件

- DSM 7.2 或以上
- 已安装 **Container Manager** 套件
- 已安装 **Git** 套件（套件中心搜索）或通过 SSH 手动克隆
- NAS 已分配固定内网 IP（建议在路由器绑定 MAC）

---

### 一、SSH 进入 NAS 并克隆代码

在 DSM「控制面板 → 终端机和 SNMP」中启用 SSH，然后：

```bash
ssh admin@<NAS_IP>

# 进入共享文件夹（建议 docker 共享文件夹）
cd /volume1/docker

git clone <仓库地址> rerp
cd rerp
```

---

### 二、配置环境变量

```bash
cp backend/.env.example backend/.env
vi backend/.env
```

**必须修改的项：**

```env
DATABASE_URL=postgresql+asyncpg://rerp:rerp_password@db:5432/rerp
SECRET_KEY=<用下方命令生成>
ACCESS_TOKEN_EXPIRE_MINUTES=480
UPLOAD_DIR=/app/uploads
```

生成 SECRET_KEY：

```bash
openssl rand -hex 32
```

---

### 三、构建前端静态文件

群晖上推荐用 Docker 构建，无需安装 Node：

```bash
cd /volume1/docker/rerp
docker compose --profile build run --rm frontend
```

构建完成后 `frontend/dist/` 目录会生成静态文件。

---

### 四、配置 Nginx（仅监听 HTTP，由 DSM 反向代理或 Cloudflare 处理 HTTPS）

编辑 `nginx/nginx.conf`，将内容替换为仅监听 80 端口：

```nginx
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass         http://backend:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    location /uploads/ {
        proxy_pass       http://backend:8000;
        proxy_set_header Host $host;
    }
}
```

同时编辑 `docker-compose.yml`，将 nginx 的 ports 改为只暴露 80：

```yaml
ports:
  - "8080:80"   # 用 8080 避免与 DSM 默认 80 端口冲突
```

> **注意：** 群晖 DSM 默认占用 80/443 端口，建议将 nginx 映射到 8080（或其他空闲端口）。

---

### 五、启动服务

```bash
cd /volume1/docker/rerp
docker compose up -d
docker compose logs -f
```

稍等约 30 秒，待 PostgreSQL 完成初始化。验证：

```bash
docker compose ps
```

所有容器应显示 `healthy` 或 `running`。

---

### 六、初始化管理员账号

```bash
docker compose exec backend python -c "
import asyncio
from app.core.database import AsyncSessionLocal
from app.models.user import SysUser
from app.core.security import get_password_hash

async def create_admin():
    async with AsyncSessionLocal() as db:
        user = SysUser(
            username='admin',
            hashed_password=get_password_hash('admin123'),
            full_name='管理员',
            role='admin',
            is_active=True
        )
        db.add(user)
        await db.commit()
    print('管理员账号已创建')

asyncio.run(create_admin())
"
```

---

### 七、配置 DSM 反向代理（可选，用于 HTTPS 访问）

如需通过域名 + HTTPS 访问，可在 DSM 中配置反向代理将流量转发到 8080 端口：

1. 打开「控制面板 → 登录门户 → 高级 → 反向代理服务器」
2. 新增规则：
   - **来源**：协议 HTTPS，主机名填域名，端口 443
   - **目的地**：协议 HTTP，主机名 `localhost`，端口 `8080`
3. 在「安全性 → 证书」中为该域名申请 Let's Encrypt 证书并绑定

配置完成后即可通过 `https://your-domain.com` 访问系统。

---

### 八、访问地址

| 场景 | 地址 |
|------|------|
| 局域网直接访问 | `http://<NAS_IP>:8080` |
| DSM 反向代理（HTTPS） | `https://<你的域名>` |
| Cloudflare Tunnel | 由 Tunnel 配置决定 |
| API 文档 | `http://<NAS_IP>:8080/api/docs` |

---

### 群晖常用运维命令

```bash
# 查看服务状态
docker compose -f /volume1/docker/rerp/docker-compose.yml ps

# 查看后端日志
docker compose -f /volume1/docker/rerp/docker-compose.yml logs -f backend

# 重启服务
docker compose -f /volume1/docker/rerp/docker-compose.yml restart

# 备份数据库
docker compose -f /volume1/docker/rerp/docker-compose.yml exec db \
  pg_dump -U rerp rerp > /volume1/docker/rerp/backups/rerp_$(date +%Y%m%d_%H%M%S).sql

# 更新部署（拉取新代码后）
cd /volume1/docker/rerp
git pull
docker compose --profile build run --rm frontend
docker compose build backend
docker compose up -d
```



**后端无法连接数据库**

```bash
# 检查数据库健康状态
docker compose ps db
docker compose logs db
```

确认 `backend/.env` 中 `DATABASE_URL` 的主机名为 `db`（Docker 内部服务名），而非 `localhost`。

**Nginx 返回 502 Bad Gateway**

```bash
docker compose logs nginx
docker compose logs backend
# 确认后端服务已正常启动
docker compose ps backend
```

**前端页面空白或 404**

确认 `frontend/dist/` 目录存在且非空：

```bash
ls frontend/dist/
```

如果为空，重新执行第三步构建前端。

**SSL 证书错误**

检查 `nginx/ssl/` 目录下证书文件是否存在。如使用 Cloudflare Tunnel，参考方案 A 修改 Nginx 配置，移除 SSL 相关配置。
