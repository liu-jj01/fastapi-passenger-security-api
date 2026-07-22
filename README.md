# FastAPI 旅客安检接口练习项目

这是一个基于 **FastAPI + SQLAlchemy + SQLite + Alembic** 的接口练习项目，包含旅客安检信息的新增、查询、更新、删除、分页筛选、备注管理、API Key 鉴权、请求日志和自动化测试。

## 功能概览

- 机场信息查询与新增
- 旅客安检信息新增、单条查询、更新、删除
- 旅客列表分页查询
- 按证件号、航班号、航班日期、旅客姓名筛选
- 按 ID 或创建时间排序
- `certNo + fltNo + fltDate` 唯一约束，防止重复提交
- 航班号、日期、座位号等字段格式校验
- 旅客备注新增、修改和清空
- 统一成功与错误返回格式
- `X-API-Key` 接口鉴权
- 请求状态码与耗时日志
- Alembic 数据库迁移
- pytest 自动化测试

## 技术栈

- Python 3.12
- FastAPI
- Pydantic / pydantic-settings
- SQLAlchemy 2.x
- SQLite
- Alembic
- pytest
- HTTPX / TestClient

## 项目结构

```text
api_practice/
├─ app/
│  ├─ routers/
│  │  ├─ __init__.py
│  │  ├─ airport.py
│  │  └─ passenger.py
│  ├─ __init__.py
│  ├─ config.py
│  ├─ database.py
│  ├─ exception_handlers.py
│  ├─ main.py
│  ├─ models.py
│  ├─ request_logging.py
│  ├─ schemas.py
│  └─ security.py
├─ migrations/
│  ├─ versions/
│  ├─ env.py
│  └─ script.py.mako
├─ .env
├─ .env.example
├─ .gitignore
├─ alembic.ini
├─ main.py
├─ passenger.db
├─ requirements.txt
└─ test_main.py
```

## 环境准备

进入项目目录：

```powershell
cd F:\shixi\api_practice
```

创建虚拟环境：

```powershell
python -m venv .venv
```

激活虚拟环境：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

安装依赖：

```powershell
pip install -r requirements.txt
```

## 环境变量

项目根目录需要创建 `.env`：

```env
APP_NAME=接口练习项目
DATABASE_URL=sqlite:///./passenger.db
API_KEY=替换为你自己的真实密钥
```

生成随机 API Key：

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

`.env.example` 可以保留示例配置：

```env
APP_NAME=接口练习项目
DATABASE_URL=sqlite:///./passenger.db
API_KEY=replace-with-your-api-key
```

真实的 `.env` 不要提交到 Git。

## 数据库迁移

查看当前数据库版本：

```powershell
alembic current
```

升级到最新版本：

```powershell
alembic upgrade head
```

修改 `app/models.py` 后生成迁移脚本：

```powershell
alembic revision --autogenerate -m "迁移说明"
```

生成后应先检查迁移文件，再执行：

```powershell
alembic upgrade head
```

查看迁移历史：

```powershell
alembic history
```

## 启动项目

每天启动时执行：

```powershell
cd F:\shixi\api_practice
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
alembic upgrade head
fastapi dev main.py
```

启动后访问：

```text
http://127.0.0.1:8000/docs
```

停止服务：

```text
Ctrl + C
```

## API Key 鉴权

旅客安检接口需要在请求头中携带：

```text
X-API-Key: 你在 .env 中配置的 API_KEY
```

不传密钥时返回 `401`，密钥错误时返回 `403`。

在 Swagger 文档页面中，可以点击右上角 **Authorize**，输入 API Key 后测试接口。

## 接口说明

### 机场接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/airport?code=CSX` | 查询机场信息 |
| POST | `/airport` | 新增机场信息 |

### 旅客安检接口

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/security/passenger` | 新增旅客安检信息 |
| GET | `/security/passenger` | 精确查询单条旅客信息 |
| PUT | `/security/passenger` | 更新旅客信息 |
| DELETE | `/security/passenger` | 删除旅客信息 |
| GET | `/security/passengers` | 分页查询旅客列表 |

单条查询、更新和删除使用三个定位参数：

```text
certNo + fltNo + fltDate
```

示例：

```text
GET /security/passenger?certNo=110101198410063535&fltNo=CA8899T&fltDate=2026-07-20
```

## 新增旅客示例

请求：

```text
POST http://127.0.0.1:8000/security/passenger
```

Headers：

```text
Content-Type: application/json
X-API-Key: 你的 API_KEY
```

Body：

```json
{
  "mainType": "SCRC",
  "subType": "PSIF",
  "sender": "SECURITYCHECK",
  "message": "{\"fltNo\":\"CA8899T\",\"fltDate\":\"2026-07-20\",\"brdno\":\"1\",\"dept\":\"CTU\",\"seat\":\"12A\",\"certType\":\"NI\",\"certNo\":\"110101198410063535\",\"psrName\":\"姚明\",\"remark\":\"需要人工复核\"}"
}
```

注意：`message` 本身是一个 JSON 字符串，因此内部双引号需要使用 `\"` 转义。

## 更新备注示例

```text
PUT http://127.0.0.1:8000/security/passenger?certNo=110101198410063535&fltNo=CA8899T&fltDate=2026-07-20
```

Body：

```json
{
  "remark": "复核已经完成"
}
```

清空备注：

```json
{
  "remark": null
}
```

## 分页、筛选与排序

查询第一页，每页 10 条：

```text
GET /security/passengers?page=1&pageSize=10
```

按航班号筛选：

```text
GET /security/passengers?fltNo=CA8899T&page=1&pageSize=10
```

按姓名模糊查询：

```text
GET /security/passengers?psrName=姚&page=1&pageSize=10
```

按 ID 升序：

```text
GET /security/passengers?sortBy=id&sortOrder=asc
```

按创建时间降序：

```text
GET /security/passengers?sortBy=createdAt&sortOrder=desc
```

## 返回格式

成功示例：

```json
{
  "code": "0000",
  "message": "查询成功",
  "data": {}
}
```

失败示例：

```json
{
  "code": "4004",
  "message": "没有找到对应的旅客航班数据",
  "data": null
}
```

常用业务错误码：

| HTTP 状态码 | 业务码 | 含义 |
|---|---|---|
| 400 | `4000` | 请求内容错误 |
| 401 | `4001` | 缺少 API Key |
| 403 | `4003` | API Key 错误 |
| 404 | `4004` | 数据不存在 |
| 409 | `4009` | 数据重复 |
| 422 | `4220` | 请求参数校验失败 |

## 请求日志

接口调用后，终端会输出请求方法、路径、状态码和耗时：

```text
GET /security/passengers status=200 duration=21.68ms
GET /security/passenger status=404 duration=3.86ms
```

响应头中还会包含：

```text
X-Process-Time-Ms
```

## 自动化测试

运行全部测试：

```powershell
pytest -v
```

当前测试覆盖：

- 新增旅客
- 重复新增返回 409
- 单条查询
- 查询不存在数据返回 404
- 更新旅客
- 删除旅客
- 日期格式校验
- 缺少参数返回 422
- 列表分页
- 姓名筛选
- 排序
- 备注新增、修改与清空
- 缺少 API Key 返回 401
- 错误 API Key 返回 403

正常结果：

```text
14 passed
```

测试使用临时 SQLite 数据库，不会污染正式的 `passenger.db`。

## 依赖更新

安装新依赖后更新：

```powershell
pip freeze > requirements.txt
```

## 常用命令

```powershell
# 激活虚拟环境
.\.venv\Scripts\Activate.ps1

# 数据库升级
alembic upgrade head

# 查看数据库版本
alembic current

# 运行测试
pytest -v

# 启动开发服务
fastapi dev main.py

# 检查 Python 文件语法
python -m compileall app migrations main.py test_main.py
```

## 后续可扩展方向

- 切换 MySQL 或 PostgreSQL
- 增加 JWT 用户登录
- 增加更细粒度的权限控制
- 增加结构化日志和日志文件
- 增加 Docker 部署
- 增加 CI 自动测试
- 增加前端管理页面
