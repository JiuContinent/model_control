启动命令
>uvicorn app.main:app --reload --app-dir src
我的项目结构：

my_project/
└── src/
    └── app/   ✅
        ├── __init__.py  (1)
        ├── main.py
        ├── config.py
        │
        ├── api/   ✅
        │   ├── __init__.py  (2)
        │   ├── deps.py
        │   ├── crud.py
        │   └── ai.py
        │
        ├── models/      # (这个目录严格来说不需要，因为它只包含数据文件，不作为一个可直接导入的包)
        │   ├── schemas.py
        │   ├── mysql_models.py
        │   └── mongo_models.py
        │
        ├── db/          # (同上，通常不需要，但为了规范性可以加上)
        │   ├── mysql.py
        │   └── mongo.py
        │
        ├── services/    ✅
        │   ├── __init__.py  (3)
        │   ├── crud_service.py
        │   └── ai_service.py
        │
        └── ai_backends/ ✅
            ├── __init__.py  (4)
            ├── openai_client.py
            └── device_control.py