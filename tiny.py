import hashlib
import os  # 导入 os 模块以与文件系统交互
import tinify  # 导入 tinify 模块以使用 TinyPNG API 进行图像压缩
import asyncio  # 导入 asyncio 模块以实现异步功能
import time  # 导入 time 模块以计算总耗时
import json  # 导入 json 模块以读取配置文件

# 从配置文件中加载 API 密钥和文件夹路径
with open('config.json', 'r', encoding='utf-8') as config_file:
    config = json.load(config_file)
    tinify.key = config.get("api_key", "YOUR_API_KEY")  # 从配置文件获取 TinyPNG API 密钥
    folder_path = config.get("folder_path", "your_folder_path_here")  # 从配置文件获取目标文件夹路径
    native_project_jsonfile = json.load(open('common-resource_project.json', 'r', encoding='utf-8'))

# 新增：從 assets.json 中讀取資產數據
with open('assets_native.json', 'r', encoding='utf-8') as assets_file:
    assets_data = json.load(assets_file)

total_original_size = 0  # 记录所有文件的原始总大小
total_compressed_size = 0  # 记录所有文件的压缩后总大小
compressed_file_count = 0  # 记录压缩的 PNG 文件总数
#暫存所有壓縮的檔案路徑
compressed_files = []

async def compress_png(file_path):
    """
    使用 TinyPNG API 异步压缩 PNG 文件并替换原始文件。
    参数：
        file_path (str): 要压缩的 PNG 文件的路径。
    """
    global total_original_size, total_compressed_size, compressed_file_count
    try:
        # 获取原始文件大小（以字节为单位）
        original_size = os.path.getsize(file_path)
        total_original_size += original_size
        
        # 使用 TinyPNG API 压缩图像
        source = await asyncio.to_thread(tinify.from_file, file_path)
        
        # 保存压缩后的图像，替换原始文件
        await asyncio.to_thread(source.to_file, file_path)  # 这一行将压缩后的图像保存到相同路径，替换原始文件
        
        # 获取压缩后的文件大小（以字节为单位）
        compressed_size = os.path.getsize(file_path)
        total_compressed_size += compressed_size
        
        # 计算节省的容量
        saved_size = original_size - compressed_size
        saved_percentage = (saved_size / original_size) * 100 if original_size > 0 else 0
        
        # 增加已压缩文件计数
        compressed_file_count += 1
        
        # 打印压缩结果，包括文件路径、原始大小、压缩后大小和节省的容量
        print(f"压缩完成: {file_path}")
        print(f"原始大小: {original_size / 1024:.2f} KB")
        print(f"压缩后大小: {compressed_size / 1024:.2f} KB")
        print(f"节省容量: {saved_size / 1024:.2f} KB ({saved_percentage:.2f}%)")
    except tinify.errors.AccountError:
        # 处理账户相关错误，例如 API 密钥无效或超出每月限制
        print("请验证您的 API 密钥和账户限制。")
    except tinify.errors.ClientError:
        # 处理客户端错误，例如不支持的文件类型或文件损坏
        print(f"输入文件无效: {file_path}")
    except tinify.errors.ServerError:
        # 处理服务器错误，例如 TinyPNG API 的临时问题
        print("TinyPNG API 出现临时问题。")
    except tinify.errors.ConnectionError:
        # 处理网络连接错误，可能在请求 API 时发生
        print("发生网络连接错误。")
    except Exception as e:
        # 处理其他任何意外错误
        print(f"发生错误: {e}")

async def compress_folder(folder_path):
    """
    异步递归压缩指定文件夹及其子文件夹中的所有 PNG 文件。
    参数：
        folder_path (str): 包含要压缩的 PNG 文件的文件夹路径。
    """
    folder_count = 0
    tasks = []  # 用于存储所有压缩任务
    for root, dirs, files in os.walk(folder_path):
        # 打印当前目录中的子文件夹数量
        if root == folder_path:
            folder_count = len(dirs)
            print(f"找到 {folder_count} 个子文件夹。")
        
        # 从 folder_path 开始遍历目录结构
        for file in files:
            # 遍历当前目录中的所有文件
            if file.lower().endswith(".png"):
                # 检查文件是否具有 .png 扩展名（不区分大小写）
                file_path = os.path.join(root, file)  # 获取完整文件路径
                # 獲取文件名
                file_name = os.path.basename(file_path)
                # 設一個 flag 來檢查是否需要壓縮
                need_compress = True
                # 在 assets.json 中查找文件名對應的資產數據
                for asset in assets_data:
                    # 印出 asset['url'] 以便檢查是否有 no-tiny 的字串
                   
                    # 檢查是否需要壓縮，如果不需要則跳過。如果 asset_data['url'] 路徑字串中有 no-tiny 則不要壓縮，並且檢查檔案名稱是否在 path 中
                    if 'no-tiny' in asset['url'] and file_name in asset['path']:
                        need_compress = False
                        break
                # 如果需要壓縮，則執行壓縮任務
                if need_compress:
                    print(f"正在处理文件: {file_path}")  # 打印正在处理的文件
                    # 存储所有压缩的文件路徑
                    compressed_files.append(file_path)
                    # tasks.append(compress_png(file_path)) # 添加压缩 PNG 文件的任务
                elif not need_compress:
                    print(f"文件 {file_path} 不需要压缩")
    
    # 如果有tasks，并行运行所有压缩任务，沒有就直接返回
    if tasks:
        await asyncio.gather(*tasks)

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

if __name__ == "__main__":
    # 记录开始时间
    start_time = time.time()
    
    # 开始压缩指定文件夹中的 PNG 文件
    asyncio.run(compress_folder(folder_path))
    
    # 记录结束时间并计算总耗时
    end_time = time.time()
    total_time = end_time - start_time

    # 如果 native_project_jsonfile 存在，則執行更新 md5 的動作，遍歷 compressed_files ，算出每一個檔案的 md5 並更新到 native_project_jsonfile 中與檔案路徑相同的 md5
    if native_project_jsonfile:
        # 印出 native_project_jsonfile 的內容
        # print(f"native_project_jsonfile: {json.dumps(native_project_jsonfile, indent=4)}")

        # 檢查 JSON 中是否有 'assets' 鍵，如果沒有則印出錯誤訊息，並跳過後續的更新 md5 的動作，有的話也印出訊息
        if "assets" not in native_project_jsonfile:
            print("JSON 中未找到 'assets' 鍵")
        else:
            print("已找到 'assets' 鍵")

            
        for file_path in compressed_files:
            # 計算 md5
            md5_hash = calculate_md5(file_path)
            # 遍歷 native_project_jsonfile 中 'assets' 鍵的所有 key
            for key in native_project_jsonfile['assets']:
                # 印出 key 以便檢查
                print(f"key: {key}")
                # 印出 file_path 以便檢查
                print(f"file_path: {file_path}")
                # 取出 file_path 中 .png 的檔名
                file_name = os.path.basename(file_path)
                print(f"file_name: {file_name}")
                # 如果 file_name 是 key 的一部分，則更新 md5
                if file_name in key:
                    print(f"更新 {file_name} 的 md5")
                    native_project_jsonfile['assets'][key]['md5'] = md5_hash
                    print(f"md5: {md5_hash}")
                    break

    # 把更新後的 native_project_jsonfile 寫入 common-resource_project.json
    with open('common-resource_project.json', 'w', encoding='utf-8') as project_file:
        json.dump(native_project_jsonfile, project_file, indent=4)
    print("已更新 common-resource_project.json")         
    
    # 计算并打印总的节省容量信息
    total_saved_size = total_original_size - total_compressed_size
    total_saved_percentage = (total_saved_size / total_original_size) * 100 if total_original_size > 0 else 0
    print("\n所有文件处理完成!")
    print(f"原始总大小: {total_original_size / 1024:.2f} KB")
    print(f"压缩后总大小: {total_compressed_size / 1024:.2f} KB")
    print(f"总节省容量: {total_saved_size / 1024:.2f} KB ({total_saved_percentage:.2f}%)")
    print(f"总耗时: {total_time:.2f} 秒")
    print(f"总共压缩了 {compressed_file_count} 个 PNG 文件")
    # 印出這個月的壓縮次數
    compressions_this_month = tinify.compression_count
    print(f"本月已使用 {compressions_this_month} 次压缩")
