import json
import threading
import random
from pathlib import Path
from typing import List, Dict, Any, Union

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

DATA_FILE = Path("data/parallel_analysis_results.jsonl")
app = FastAPI(title="✨ 图像标注 ✨")

data_store: List[Dict[str, Any]] = []
file_lock = threading.Lock()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def load_data():
    """从 JSONL 文件加载数据到内存中"""
    global data_store
    if not DATA_FILE.exists():
        data_store = []
        return
    
    with DATA_FILE.open('r', encoding='utf-8') as f:
        temp_data = []
        for i, line in enumerate(f):
            item = json.loads(line)
            if 'id' not in item:
                item['id'] = i + 1
            temp_data.append(item)
        data_store = temp_data
        
    print(f"✅ 成功加载 {len(data_store)} 条数据。")

def save_data():
    """将内存中的数据保存回 JSONL 文件"""
    with file_lock:
        with DATA_FILE.open('w', encoding='utf-8') as f:
            # 确保按id排序后写入
            data_store.sort(key=lambda x: x.get('id', 0))
            for item in data_store:
                item_to_write = item.copy()
                if 'id' in item_to_write:
                    del item_to_write['id']
                f.write(json.dumps(item_to_write, ensure_ascii=False) + '\n')
        print(f"💾 数据已成功保存到 {DATA_FILE}")

@app.on_event("startup")
def startup_event():
    load_data()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "total_items": len(data_store)})

@app.get("/annotate", response_class=HTMLResponse)
async def annotate_page(request: Request):
    return templates.TemplateResponse("annotation.html", {"request": request})

@app.get("/api/data")
async def get_data_by_ids(start: int, end: int):
    """根据ID范围获取数据。ID从1开始。"""
    if not data_store:
        raise HTTPException(status_code=404, detail="数据未加载或文件为空")
    
    if start <= 0 or end > len(data_store) or start > end:
        raise HTTPException(status_code=400, detail=f"ID范围无效。有效范围：1-{len(data_store)}")
        
    return data_store[start-1:end]

@app.post("/api/save/{item_id}")
async def save_item(item_id: int, user_input: Dict[str, Any]):
    """
    接收前端标注，将原始格式转换为新格式并保存。
    """
    if not (1 <= item_id <= len(data_store)):
        raise HTTPException(status_code=404, detail=f"ID {item_id} 不存在。")

    item_index = item_id - 1
    original_item = data_store[item_index]

    question_text = user_input.get("question", "")
    answer_text = user_input.get("answer", "")
    justification = user_input.get("justification", "")
    optimal_path = user_input.get("optimal_path", "")
    
    image_path = original_item.get("image", {}).get("path", "")

    new_data = {
        "image": {"path": image_path},
        "data_source": "MultiMM",
        "ability": "metaphor",
        "prompt": [{"content": question_text, "role": "user"}],
        "reward_model": {"ground_truth": answer_text, "style": "rule"},
        "extra_info": {
            "justification": justification,
            "optimal_path": optimal_path,
            "rhetoric": "象征",
            "split": "test"
        }
    }

    options_keys = ["option1", "option2", "option3", "option4", "option5", "option6"]
    answer_key_map = {0: "A", 1: "B", 2: "C", 3: "D", 4: "E", 5: "F"}
    
    correct_answer_index = random.randint(0, len(options_keys) - 1)
    
    new_data["answer"] = answer_key_map[correct_answer_index]
    
    for i, key in enumerate(options_keys):
        if i == correct_answer_index:
            new_data[key] = answer_text
        else:
            new_data[key] = "" 

    new_data['id'] = item_id

    data_store[item_index] = new_data
    
    save_data()
    
    return JSONResponse(content={"message": f"🎉 ID: {item_id} 已保存！"}, status_code=200)