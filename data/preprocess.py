import json
import os
from pathlib import Path

def preprocess_jsonl(input_path=r"D:\software\CodeRepo\python\metaphor_anno\data\parallel_analysis_results_EN.jsonl", output_path=r"D:\software\CodeRepo\python\metaphor_anno\data\parallel_analysis_results1.jsonl"):
    """
    预处理JSONL文件：
    1. 为每行数据添加一个从1开始的 'id'。
    2. 将 'image.path' 的绝对路径修改为相对路径。
    """
    # 确保输出目录存在
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        with open(input_path, 'r', encoding='utf-8') as infile, \
             open(output_path, 'w', encoding='utf-8') as outfile:
            
            for i, line in enumerate(infile):
                try:
                    # 读取原始数据
                    data = json.loads(line.strip())
                    
                    # 1. 添加ID
                    data['id'] = i + 1
                    
                    # 2. 修改图片路径
                    original_path = data.get("image", {}).get("path", "")
                    if "imgs_EN/" in original_path:
                        # 从 "imgs_CN/" 开始截取，得到相对路径
                        relative_path = "imgs_EN" + original_path.split("imgs_EN", 1)[1]
                        data["image"]["path"] = relative_path
                    
                    # 将处理后的数据写回新文件，确保中文正常显示
                    outfile.write(json.dumps(data, ensure_ascii=False) + '\n')

                except json.JSONDecodeError:
                    print(f"警告: 第 {i+1} 行不是有效的JSON格式，已跳过。")
                except Exception as e:
                    print(f"处理第 {i+1} 行时发生错误: {e}")

        print(f"🎉 预处理完成！共处理 {i+1} 行数据。")
        print(f"处理后的文件已保存至: {output_path}")

    except FileNotFoundError:
        print(f"错误: 输入文件未找到 -> {input_path}")
        print("请确保你的原始jsonl文件名为 'source.jsonl' 并且与脚本在同一目录下。")

if __name__ == "__main__":
    # 将你的原始文件名和期望的输出文件名传入函数
    preprocess_jsonl()