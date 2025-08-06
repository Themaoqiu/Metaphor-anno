import json
import os
import random
import shutil

# --- 1. 配置 ---
# 请根据你的实际情况修改这些路径和参数

# 输入文件和文件夹
jsonl_input_file = r'D:\software\CodeRepo\python\metaphor_anno\data\mutimm_dataset.jsonl'  # 你的原始 .jsonl 文件名
source_image_folder = r'D:\software\CodeRepo\python\metaphor_anno\static\mutimm_images'           # 存放所有原始图片的文件夹

# 输出文件和文件夹
output_jsonl_file = r'D:\software\CodeRepo\python\metaphor_anno\data\selected_mutimm_dataset.jsonl'     # 生成的目标 .jsonl 文件名
output_image_folder = r'D:\software\CodeRepo\python\metaphor_anno\static\selected_200_images'  # 存放筛选后图片的目标文件夹

# 数据集参数
TOTAL_TARGET_COUNT = 200                     # 最终需要的数据总数

# --- 2. 数据处理与筛选 ---

print("开始处理数据集...")

# 创建两个列表，分别存放 'parallel' 和其他类型的数据
parallel_items = []
other_items = []

try:
    with open(jsonl_input_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                # 使用 .get() 方法安全地访问嵌套字典，避免因缺少键而出错
                if data.get('extra_info', {}).get('optimal_path') == 'parallel':
                    parallel_items.append(data)
                else:
                    other_items.append(data)
            except json.JSONDecodeError:
                print(f"警告：跳过一行无法解析的JSON: {line.strip()}")

except FileNotFoundError:
    print(f"错误：输入文件 '{jsonl_input_file}' 未找到。请检查文件名和路径。")
    exit()

print(f"读取完成：找到 {len(parallel_items)} 条 'parallel' 数据，{len(other_items)} 条其他数据。")


# --- 3. 构建最终数据集 ---

final_selection = []
num_parallel = len(parallel_items)

if num_parallel >= TOTAL_TARGET_COUNT:
    print(f"警告：'parallel' 数据的数量 ({num_parallel}) 大于或等于目标数量 ({TOTAL_TARGET_COUNT})。")
    print(f"将从 'parallel' 数据中随机选择 {TOTAL_TARGET_COUNT} 条。")
    final_selection = random.sample(parallel_items, TOTAL_TARGET_COUNT)
else:
    # 先把所有 'parallel' 数据都加进去
    final_selection.extend(parallel_items)
    
    # 计算还需要从 'other' 数据中挑选多少条
    num_needed_from_others = TOTAL_TARGET_COUNT - num_parallel
    
    if len(other_items) < num_needed_from_others:
        print(f"警告：其他数据的数量 ({len(other_items)}) 不足以凑齐 {TOTAL_TARGET_COUNT} 条。")
        print("将使用所有 'parallel' 和所有 'other' 数据。")
        final_selection.extend(other_items)
    else:
        print(f"需要从其他数据中随机选择 {num_needed_from_others} 条。")
        selected_others = random.sample(other_items, num_needed_from_others)
        final_selection.extend(selected_others)

print(f"最终数据集构建完成，总共 {len(final_selection)} 条数据。")


# --- 4. 写入新文件并复制图片 ---

# 创建目标文件夹 (如果不存在)
os.makedirs(output_image_folder, exist_ok=True)
print(f"目标图片文件夹 '{output_image_folder}' 已准备就绪。")

copied_count = 0
not_found_count = 0

with open(output_jsonl_file, 'w', encoding='utf-8') as f_out:
    for item in final_selection:
        # 写入新的 jsonl 文件
        f_out.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        # 复制对应的图片
        try:
            image_filename = item.get('image', {}).get('path')
            if not image_filename:
                print(f"警告：记录 {item} 中缺少图片路径，跳过复制。")
                continue

            source_path = os.path.join(source_image_folder, image_filename)
            destination_path = os.path.join(output_image_folder, image_filename)
            
            if os.path.exists(source_path):
                shutil.copy2(source_path, destination_path) # copy2 会同时复制元数据
                copied_count += 1
            else:
                print(f"警告：源图片 '{source_path}' 未找到，无法复制。")
                not_found_count += 1

        except Exception as e:
            print(f"处理记录 {item} 时发生错误：{e}")

print("\n--- 处理完毕 ---")
print(f"新的数据集 '{output_jsonl_file}' 已生成。")
print(f"成功复制 {copied_count} 张图片到 '{output_image_folder}' 文件夹。")
if not_found_count > 0:
    print(f"有 {not_found_count} 张图片因未在源文件夹中找到而未能复制。")