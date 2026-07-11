from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from pydantic import BaseModel
from datetime import datetime
from typing import List

DATABASE_URL = "sqlite:///./mes_system.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class BOM(Base):
    __tablename__ = "bom"
    id = Column(Integer, primary_key=True, index=True)
    product_code = Column(String, index=True)
    product_name = Column(String)
    parent_item = Column(String)
    child_item = Column(String)
    quantity = Column(Float)
    unit = Column(String)
    created_at = Column(DateTime, default=datetime.now)


class WorkOrder(Base):
    __tablename__ = "work_order"
    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String, index=True)
    product_code = Column(String)
    product_name = Column(String)
    quantity = Column(Integer)
    status = Column(String, default="pending")
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    tasks = relationship("WorkflowTask", back_populates="work_order")


class WorkflowTask(Base):
    __tablename__ = "workflow_task"
    id = Column(Integer, primary_key=True, index=True)
    work_order_id = Column(Integer, ForeignKey("work_order.id"))
    task_name = Column(String)
    task_code = Column(String)
    status = Column(String, default="pending")
    assignee = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    work_order = relationship("WorkOrder", back_populates="tasks")
    production_records = relationship("ProductionRecord", back_populates="task")


class ProductionRecord(Base):
    __tablename__ = "production_record"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("workflow_task.id"))
    work_center = Column(String)
    operator = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    quantity = Column(Integer)
    scrap_quantity = Column(Integer)
    remarks = Column(Text)
    task = relationship("WorkflowTask", back_populates="production_records")


Base.metadata.create_all(bind=engine)

app = FastAPI(title="MES系统", description="制造执行系统")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class BOMCreate(BaseModel):
    product_code: str
    product_name: str
    parent_item: str
    child_item: str
    quantity: float
    unit: str


class WorkOrderCreate(BaseModel):
    order_no: str
    product_code: str
    product_name: str
    quantity: int
    start_date: datetime
    end_date: datetime


class WorkflowTaskCreate(BaseModel):
    work_order_id: int
    task_name: str
    task_code: str
    assignee: str


class ProductionRecordCreate(BaseModel):
    task_id: int
    work_center: str
    operator: str
    start_time: datetime
    end_time: datetime
    quantity: int
    scrap_quantity: int = 0
    remarks: str = ""


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/bom", response_class=HTMLResponse)
async def bom_page(request: Request):
    return templates.TemplateResponse("bom.html", {"request": request})


@app.get("/workorder", response_class=HTMLResponse)
async def workorder_page(request: Request):
    return templates.TemplateResponse("workorder.html", {"request": request})


@app.get("/workflow", response_class=HTMLResponse)
async def workflow_page(request: Request):
    return templates.TemplateResponse("workflow.html", {"request": request})


@app.get("/production", response_class=HTMLResponse)
async def production_page(request: Request):
    return templates.TemplateResponse("production.html", {"request": request})


@app.get("/wip", response_class=HTMLResponse)
async def wip_page(request: Request):
    return templates.TemplateResponse("wip.html", {"request": request})


@app.get("/api/bom", response_model=List[dict])
async def get_bom(db: Session = Depends(get_db)):
    return [
        {
            "id": item.id,
            "product_code": item.product_code,
            "product_name": item.product_name,
            "parent_item": item.parent_item,
            "child_item": item.child_item,
            "quantity": item.quantity,
            "unit": item.unit,
            "created_at": item.created_at.isoformat()
        }
        for item in db.query(BOM).all()
    ]


@app.post("/api/bom")
async def create_bom(data: BOMCreate, db: Session = Depends(get_db)):
    bom = BOM(**data.model_dump())
    db.add(bom)
    db.commit()
    db.refresh(bom)
    return {"id": bom.id, "message": "BOM创建成功"}


@app.delete("/api/bom/{id}")
async def delete_bom(id: int, db: Session = Depends(get_db)):
    bom = db.query(BOM).filter(BOM.id == id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")
    db.delete(bom)
    db.commit()
    return {"message": "BOM删除成功"}


@app.get("/api/workorder", response_model=List[dict])
async def get_workorder(db: Session = Depends(get_db)):
    return [
        {
            "id": item.id,
            "order_no": item.order_no,
            "product_code": item.product_code,
            "product_name": item.product_name,
            "quantity": item.quantity,
            "status": item.status,
            "start_date": item.start_date.isoformat() if item.start_date else None,
            "end_date": item.end_date.isoformat() if item.end_date else None,
            "created_at": item.created_at.isoformat()
        }
        for item in db.query(WorkOrder).all()
    ]


@app.post("/api/workorder")
async def create_workorder(data: WorkOrderCreate, db: Session = Depends(get_db)):
    wo = WorkOrder(**data.model_dump())
    db.add(wo)
    db.commit()
    db.refresh(wo)
    return {"id": wo.id, "message": "工单创建成功"}


@app.put("/api/workorder/{id}/status")
async def update_workorder_status(id: int, status: str, db: Session = Depends(get_db)):
    wo = db.query(WorkOrder).filter(WorkOrder.id == id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="工单不存在")
    wo.status = status
    db.commit()
    return {"message": "工单状态更新成功"}


@app.delete("/api/workorder/{id}")
async def delete_workorder(id: int, db: Session = Depends(get_db)):
    wo = db.query(WorkOrder).filter(WorkOrder.id == id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="工单不存在")
    db.delete(wo)
    db.commit()
    return {"message": "工单删除成功"}


@app.get("/api/workflow", response_model=List[dict])
async def get_workflow(db: Session = Depends(get_db)):
    return [
        {
            "id": item.id,
            "work_order_id": item.work_order_id,
            "task_name": item.task_name,
            "task_code": item.task_code,
            "status": item.status,
            "assignee": item.assignee,
            "start_time": item.start_time.isoformat() if item.start_time else None,
            "end_time": item.end_time.isoformat() if item.end_time else None
        }
        for item in db.query(WorkflowTask).all()
    ]


@app.post("/api/workflow")
async def create_workflow(data: WorkflowTaskCreate, db: Session = Depends(get_db)):
    task = WorkflowTask(**data.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return {"id": task.id, "message": "工作流任务创建成功"}


@app.put("/api/workflow/{id}/status")
async def update_workflow_status(id: int, status: str, db: Session = Depends(get_db)):
    task = db.query(WorkflowTask).filter(WorkflowTask.id == id).first()
    if not task:
        raise HTTPException(status_code=404, detail="工作流任务不存在")
    task.status = status
    if status == "in_progress":
        task.start_time = datetime.now()
    elif status == "completed":
        task.end_time = datetime.now()
    db.commit()
    return {"message": "工作流状态更新成功"}


@app.delete("/api/workflow/{id}")
async def delete_workflow(id: int, db: Session = Depends(get_db)):
    task = db.query(WorkflowTask).filter(WorkflowTask.id == id).first()
    if not task:
        raise HTTPException(status_code=404, detail="工作流任务不存在")
    db.delete(task)
    db.commit()
    return {"message": "工作流任务删除成功"}


@app.get("/api/production", response_model=List[dict])
async def get_production(db: Session = Depends(get_db)):
    return [
        {
            "id": item.id,
            "task_id": item.task_id,
            "work_center": item.work_center,
            "operator": item.operator,
            "start_time": item.start_time.isoformat() if item.start_time else None,
            "end_time": item.end_time.isoformat() if item.end_time else None,
            "quantity": item.quantity,
            "scrap_quantity": item.scrap_quantity,
            "remarks": item.remarks
        }
        for item in db.query(ProductionRecord).all()
    ]


@app.post("/api/production")
async def create_production(data: ProductionRecordCreate, db: Session = Depends(get_db)):
    record = ProductionRecord(**data.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"id": record.id, "message": "生产记录创建成功"}


@app.delete("/api/production/{id}")
async def delete_production(id: int, db: Session = Depends(get_db)):
    record = db.query(ProductionRecord).filter(ProductionRecord.id == id).first()
    if not record:
        raise HTTPException(status_code=404, detail="生产记录不存在")
    db.delete(record)
    db.commit()
    return {"message": "生产记录删除成功"}


@app.get("/api/wip", response_model=List[dict])
async def get_wip(db: Session = Depends(get_db)):
    wip_data = []
    for wo in db.query(WorkOrder).all():
        total_produced = sum(
            r.quantity for task in wo.tasks for r in task.production_records
        )
        total_scrap = sum(
            r.scrap_quantity for task in wo.tasks for r in task.production_records
        )
        in_progress_tasks = sum(1 for t in wo.tasks if t.status == "in_progress")
        completed_tasks = sum(1 for t in wo.tasks if t.status == "completed")
        total_tasks = len(wo.tasks)
        progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        wip_data.append({
            "order_no": wo.order_no,
            "product_name": wo.product_name,
            "total_quantity": wo.quantity,
            "produced_quantity": total_produced,
            "scrap_quantity": total_scrap,
            "status": wo.status,
            "progress": round(progress, 2),
            "completed_tasks": completed_tasks,
            "total_tasks": total_tasks,
            "in_progress_tasks": in_progress_tasks
        })
    return wip_data


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
