# main.py

import json
import threading
from pathlib import Path
from typing import List, Dict, Any

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from data_adapter import get_adapter_for_record

DATA_DIR = Path("data")  # 數據集文件夾
app = FastAPI(title="✨ 隐喻数据标注 ✨")

DATASETS: Dict[str, List[Dict[str, Any]]] = {}
file_lock = threading.Lock()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def load_all_datasets():
    """掃描data文件夾，加載所有.jsonl文件到內存。"""
    global DATASETS
    if not DATA_DIR.is_dir():
        DATA_DIR.mkdir()
        print(f"創建數據文件夾: {DATA_DIR}")
        return

    for file_path in DATA_DIR.glob("*.jsonl"):
        dataset_name = file_path.stem  # 使用文件名（不含擴展名）作為數據集ID
        with file_path.open('r', encoding='utf-8') as f:
            temp_data = []
            for i, line in enumerate(f):
                try:
                    item = json.loads(line)
                    item['id'] = i + 1  # 賦予運行時ID
                    temp_data.append(item)
                except json.JSONDecodeError:
                    print(f"警告: 文件 {file_path.name} 第 {i+1} 行 JSON 格式錯誤，已跳過。")
            DATASETS[dataset_name] = temp_data
            print(f"✅ 成功加載數據集 '{dataset_name}' ({len(temp_data)} 條記錄)。")

def save_dataset(dataset_name: str):
    """將指定數據集的內存數據保存回對應的JSONL文件。"""
    if dataset_name not in DATASETS:
        print(f"错误：尝试保存不存在的数据集： '{dataset_name}'")
        return

    with file_lock:
        records = DATASETS[dataset_name]
        file_path = DATA_DIR / f"{dataset_name}.jsonl"
        
        with file_path.open('w', encoding='utf-8') as f:
            records.sort(key=lambda x: x.get('id', 0))
            for item in records:
                item_to_write = item.copy()
                del item_to_write['id']
                f.write(json.dumps(item_to_write, ensure_ascii=False) + '\n')
        print(f"💾 数据集 '{dataset_name}' 已成功保存到 {file_path}")

@app.on_event("startup")
def startup_event():
    load_all_datasets()

# --- 路由和端點 ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """渲染主頁，並傳遞所有可用數據集的名稱和記錄數。"""
    dataset_info = {name: len(records) for name, records in DATASETS.items()}
    return templates.TemplateResponse("index.html", {
        "request": request,
        "dataset_info": dataset_info
    })

@app.get("/annotate", response_class=HTMLResponse)
async def annotate_page(request: Request):
    return templates.TemplateResponse("annotation.html", {"request": request})

@app.get("/api/data", response_class=JSONResponse)
async def get_data_by_ids(dataset: str, start: int, end: int):
    if dataset not in DATASETS:
        raise HTTPException(status_code=404, detail=f"數據集 '{dataset}' 不存在。")
    
    records_list = DATASETS[dataset]
    if not (1 <= start <= end <= len(records_list)):
        raise HTTPException(status_code=400, detail=f"ID范围无效。'{dataset}'有效范围：1-{len(records_list)}")
        
    raw_records = records_list[start-1:end]
    
    display_data = []
    for record in raw_records:
        adapter = get_adapter_for_record(record)
        display_data.append(adapter.get_display_data())
        
    return JSONResponse(content=display_data)

@app.post("/api/save/{item_id}", response_class=JSONResponse)
async def save_item(item_id: int, form_data: Dict[str, Any], dataset: str = Query(...)):
    if dataset not in DATASETS:
        raise HTTPException(status_code=404, detail=f"数据集 '{dataset}' 不存在。")
    
    records_list = DATASETS[dataset]
    if not (1 <= item_id <= len(records_list)):
        raise HTTPException(status_code=404, detail=f"ID {item_id} 在 '{dataset}' 中不存在。")

    item_index = item_id - 1
    original_record = records_list[item_index]
    
    adapter = get_adapter_for_record(original_record)
    adapter.update_record(form_data)
    
    records_list[item_index] = adapter.record
    
    save_dataset(dataset)
    
    return JSONResponse(content={"message": f"🎉 ID: {item_id} (来自 {dataset}) 已成功保存！"}, status_code=200)