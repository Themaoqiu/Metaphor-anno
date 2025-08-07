# data_adapter.py
import random
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class DatasetAdapter(ABC):
    def __init__(self, record: Dict[str, Any]):
        self.record = record

    @abstractmethod
    def get_display_data(self) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def update_record(self, form_data: Dict[str, Any]):
        raise NotImplementedError

class QuestionAnswerAdapter(DatasetAdapter):
    """
    标注问题和答案的通用任务
    """
    def update_record(self, form_data: Dict[str, Any]):
        
        if "prompt" not in self.record:
            self.record["prompt"] = [{"content": "", "role": "user"}]
        self.record["prompt"][0]["content"] = form_data.get("question", "")
        
        if "extra_info" not in self.record:
            self.record["extra_info"] = {}
        self.record["extra_info"]["optimal_path"] = form_data.get("optimal_path", "")
        self.record["extra_info"]["justification"] = form_data.get("justification", "")
        
        correct_answer_text = form_data.get("correct_answer", "")

        if "reward_model" not in self.record:
            self.record["reward_model"] = {"ground_truth": "", "style": "rule"}
        self.record["reward_model"]["ground_truth"] = correct_answer_text
        
        option_keys = ["option1", "option2", "option3", "option4"]
        slot_to_letter = {'option1': 'A', 'option2': 'B', 'option3': 'C', 'option4': 'D'}
        
        correct_slot = random.choice(option_keys)
        
        for key in option_keys:
            self.record[key] = ""
        self.record[correct_slot] = correct_answer_text
        
        self.record["answer"] = slot_to_letter[correct_slot]


class MutimmAdapter(QuestionAnswerAdapter):
    def get_display_data(self) -> Dict[str, Any]:
        base_path = self.record.get("image", {}).get("path", "")
        return {
            "id": self.record.get("id"),
            "image_path": f"mutimm_images/{base_path}" if base_path else "",
            "display_fields": [],
            "annotation_fields": [
                {
                    "name": "question", "label": "问题 (Prompt)", "type": "textarea",
                    "value": self.record.get("prompt", [{}])[0].get("content", "")
                },
                {
                    "name": "correct_answer", "label": "正确答案 (Correct Answer Text)", "type": "textarea",
                    "value": self.record.get("reward_model", {}).get("ground_truth", "")
                },
                {
                    "name": "optimal_path", "label": "理解路径 (Optimal Path)", "type": "select",
                    "value": self.record.get("extra_info", {}).get("optimal_path", ""),
                    "options": ["", "parallel", "sequential", "direct"]
                },
                {
                    "name": "justification", "label": "路径解释 (Justification)", "type": "textarea",
                    "value": self.record.get("extra_info", {}).get("justification", "")
                }
            ]
        }

class HummusAdapter(QuestionAnswerAdapter):
    def get_display_data(self) -> Dict[str, Any]:
        extra_info = self.record.get("extra_info", {})
        base_path = self.record.get("image", {}).get("path", "")
        return {
            "id": self.record.get("id"),
            "image_path": f"hummus_images/{base_path}" if base_path else "",
            "display_fields": [
                {"label": "图像解释 (Explanation)", "value": extra_info.get("explanation", "N/A")},
                {"label": "核心隐喻 (Metaphorical Meaning)", "value": extra_info.get("metaphorical_meaning", "N/A")}
            ],
            "annotation_fields": [
                {
                    "name": "question", "label": "问题 (Prompt)", "type": "textarea",
                    "value": self.record.get("prompt", [{}])[0].get("content", "")
                },
                {
                    "name": "correct_answer", "label": "正确答案 (Correct Answer Text)", "type": "textarea",
                    "value": self.record.get("reward_model", {}).get("ground_truth", "")
                },
                {
                    "name": "optimal_path", "label": "理解路径 (Optimal Path)", "type": "select",
                    "value": extra_info.get("optimal_path", ""),
                    "options": ["", "parallel", "sequential", "direct"]
                },
                {
                    "name": "justification", "label": "路徑解释 (Justification)", "type": "textarea",
                    "value": extra_info.get("justification", "")
                }
            ]
        }

class YesbutAdapter(DatasetAdapter): 
    def get_display_data(self) -> Dict[str, Any]:
        extra_info = self.record.get("extra_info", {})
        base_path = self.record.get("image", {}).get("path", "")
        return {
            "id": self.record.get("id"),
            "image_path": f"yesbut_images/{base_path}" if base_path else "",
            "display_fields": [
                {"label": "问题 (Question)", "value": self.record.get("prompt", [{}])[0].get("content", "N/A")},
                {"label": "选项 (Options)", "value": "\n".join([f"{k[0].upper()}. {v}" for k, v in self.record.items() if k.startswith('option') and v])},
                {"label": "正確答案 (Correct Answer)", "value": self.record.get("answer", "N/A")},
                {"label": "图像解释 (Explanation)", "value": extra_info.get("explanation", "N/A")},
                {"label": "隐喻含义 (Metaphorical Meaning)", "value": extra_info.get("metaphorical_meaning", "N/A")}
            ],
            "annotation_fields": [
                {
                    "name": "optimal_path", "label": "理解路径 (Optimal Path)", "type": "select",
                    "value": extra_info.get("optimal_path", ""), "options": ["", "parallel", "sequential", "direct"]
                },
                {
                    "name": "justification", "label": "路径解释 (Justification)", "type": "textarea",
                    "value": extra_info.get("justification", "")
                }
            ]
        }

    def update_record(self, form_data: Dict[str, Any]):
        self.record["extra_info"]["optimal_path"] = form_data.get("optimal_path", "")
        self.record["extra_info"]["justification"] = form_data.get("justification", "")

class VfluteAdapter(QuestionAnswerAdapter):
    """针对 'V-FLUTE' 数据集的具体适配器。"""
    def get_display_data(self) -> Dict[str, Any]:
        extra_info = self.record.get("extra_info", {})
        base_path = self.record.get("image", {}).get("path", "")
        
        return {
            "id": self.record.get("id"),
            "image_path": f"vflute_images/{base_path}" if base_path else "",
            "display_fields": [
                {"label": "图像解释 (Explanation)", "value": extra_info.get("explanation", "N/A")},
                {"label": "相关批语 (Claim)", "value": extra_info.get("claim", "N/A")}
            ],
            "annotation_fields": [
                {
                    "name": "question", "label": "问题 (Prompt)", "type": "textarea",
                    "value": self.record.get("prompt", [{}])[0].get("content", "")
                },
                {
                    "name": "correct_answer", "label": "正确答案 (Correct Answer Text)", "type": "textarea",
                    "value": self.record.get("reward_model", {}).get("ground_truth", "")
                },
                {
                    "name": "optimal_path", "label": "理解路径 (Optimal Path)", "type": "select",
                    "value": extra_info.get("optimal_path", ""),
                    "options": ["", "parallel", "sequential", "direct"]
                },
                {
                    "name": "justification", "label": "路径解释 (Justification)", "type": "textarea",
                    "value": extra_info.get("justification", "")
                }
            ]
        }

def get_adapter_for_record(record: Dict[str, Any]) -> DatasetAdapter:
    """檢查記錄中的'data_source'欄位，並返回相應的適配器實例。"""
    data_source = record.get("data_source", "")
    
    if data_source == "V-FLUTE": 
        return VfluteAdapter(record)
    elif data_source == "YesBut_Benchmark":
        return YesbutAdapter(record)
    elif data_source == "hummus":
        return HummusAdapter(record)
    else:
        return MutimmAdapter(record)