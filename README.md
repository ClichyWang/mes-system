# MES制造执行系统

基于Python + FastAPI的Web版MES系统，包含BOM管理、工单管理、工作流、生产过程采集和WIP报表等功能。

## 功能模块

- **BOM管理**: 产品物料清单的增删查
- **工单管理**: 工单创建、状态更新、删除
- **工作流**: 任务分配、状态跟踪、负责人管理
- **生产采集**: 生产记录录入、产量统计、报废记录
- **WIP报表**: 在制品进度展示、完成率统计、可视化进度条

## 技术栈

- 后端: Python + FastAPI + SQLAlchemy
- 前端: HTML + CSS + JavaScript (Jinja2模板)
- 数据库: SQLite

## 安装运行

```bash
pip install -r requirements.txt
python main.py
```

访问 http://localhost:8000

## 项目结构

```
mes_system/
├── main.py              # 后端API服务
├── requirements.txt     # 依赖配置
├── static/
│   └── style.css        # 样式文件
└── templates/
    ├── index.html       # 首页
    ├── bom.html         # BOM管理
    ├── workorder.html   # 工单管理
    ├── workflow.html    # 工作流
    ├── production.html  # 生产采集
    └── wip.html         # WIP报表
```
