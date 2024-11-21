import json
import os
import hashlib

# 从配置文件中加载 API 密钥和文件夹路径
with open('config.json', 'r', encoding='utf-8') as config_file:
    config = json.load(config_file)
    folder_path = config.get("folder_path", "your_folder_path_here")  # 从配置文件获取目标文件夹路径

def calculate_md5(file_path):
    """
    計算指定文件的 MD5 值。
    參數：
        file_path (str): 文件路徑。
    返回：
        str: MD5 哈希值。
    """
    with open(file_path, "rb") as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)
    return file_hash.hexdigest()

def print_png_md5(folder_path):
    """
    遞歸遍歷指定資料夾，計算所有 PNG 文件的 MD5 並印出。
    參數：
        folder_path (str): 要處理的資料夾路徑。
    """
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(".png"):  # 檢查是否是 PNG 文件
                file_path = os.path.join(root, file)
                md5_hash = calculate_md5(file_path)
                print(f"文件: {file_path}")
                print(f"MD5: {md5_hash}")
                print("-" * 40)

if __name__ == "__main__":
    if os.path.isdir(folder_path):
        print_png_md5(folder_path)
    else:
        print("無效的資料夾路徑，請重新輸入。")
