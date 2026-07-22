覆盖到项目根目录 F:\shixi\api_practice：
- app\schemas.py
- app\models.py
- app\routers\passenger.py
- test_main.py

覆盖后执行：
python -m compileall app main.py test_main.py
pytest -v

预期：12 passed
