SQLAlchemy 2.0 改造版

替换文件：
1. app/database.py
2. 新增 app/models.py
3. app/routers/passenger.py
4. test_main.py

保留原来的 passenger.db，不要删除。

运行：
python -m compileall app main.py test_main.py
pytest -v
fastapi dev main.py
