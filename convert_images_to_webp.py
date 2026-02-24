#!/usr/bin/env python3
"""
圖片轉換為WebP格式腳本
將PNG和JPG圖片轉換為WebP格式以優化加載性能
"""

import os
import sys
from pathlib import Path
from PIL import Image
import concurrent.futures
from datetime import datetime

def convert_image_to_webp(input_path, output_path, quality=85):
    """
    將圖片轉換為WebP格式
    
    Args:
        input_path: 輸入圖片路徑
        output_path: 輸出WebP路徑
        quality: WebP質量 (1-100)
    """
    try:
        # 檢查輸出文件是否已存在
        if os.path.exists(output_path):
            print(f"  WebP文件已存在: {output_path}")
            return True
        
        # 打開圖片
        with Image.open(input_path) as img:
            # 如果是PNG且有透明度，保持RGBA模式
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                img = img.convert('RGBA')
            else:
                img = img.convert('RGB')
            
            # 保存為WebP
            img.save(output_path, 'WEBP', quality=quality, method=6)
            
            # 獲取文件大小信息
            input_size = os.path.getsize(input_path)
            output_size = os.path.getsize(output_path)
            reduction = ((input_size - output_size) / input_size) * 100
            
            print(f"  轉換完成: {os.path.basename(input_path)} → {os.path.basename(output_path)}")
            print(f"    大小: {input_size/1024:.1f}KB → {output_size/1024:.1f}KB (減少 {reduction:.1f}%)")
            
            return True
            
    except Exception as e:
        print(f"  轉換失敗 {input_path}: {e}")
        return False

def find_image_files(directory, extensions=('.png', '.jpg', '.jpeg')):
    """
    查找指定目錄中的圖片文件
    
    Args:
        directory: 目錄路徑
        extensions: 圖片擴展名列表
        
    Returns:
        圖片文件路徑列表
    """
    image_files = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(extensions):
                image_files.append(os.path.join(root, file))
    
    return image_files

def process_directory(directory, quality=85, max_workers=4):
    """
    處理目錄中的所有圖片文件
    
    Args:
        directory: 目錄路徑
        quality: WebP質量
        max_workers: 最大並行工作數
    """
    print(f"掃描目錄: {directory}")
    
    # 查找圖片文件
    image_files = find_image_files(directory)
    
    if not image_files:
        print("未找到圖片文件")
        return
    
    print(f"找到 {len(image_files)} 個圖片文件")
    
    # 創建轉換任務列表
    conversion_tasks = []
    
    for input_path in image_files:
        # 構建輸出路徑
        input_path_obj = Path(input_path)
        output_path = input_path_obj.with_suffix('.webp')
        
        # 跳過已經存在的WebP文件
        if output_path.exists():
            continue
            
        conversion_tasks.append((input_path, str(output_path), quality))
    
    if not conversion_tasks:
        print("所有圖片已轉換為WebP格式")
        return
    
    print(f"需要轉換 {len(conversion_tasks)} 個圖片")
    
    # 使用線程池並行轉換
    successful = 0
    failed = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任務
        future_to_task = {
            executor.submit(convert_image_to_webp, *task): task 
            for task in conversion_tasks
        }
        
        # 處理結果
        for future in concurrent.futures.as_completed(future_to_task):
            task = future_to_task[future]
            try:
                if future.result():
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"任務執行失敗 {task[0]}: {e}")
                failed += 1
    
    # 輸出統計信息
    print(f"\n轉換完成:")
    print(f"  成功: {successful}")
    print(f"  失敗: {failed}")
    print(f"  總計: {len(conversion_tasks)}")

def create_webp_fallback_html():
    """
    創建WebP回退方案的HTML示例
    """
    html_template = """<!DOCTYPE html>
<html lang="zh-HK">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WebP圖片回退方案</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .example {
            margin: 20px 0;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        img {
            max-width: 100%;
            height: auto;
        }
    </style>
</head>
<body>
    <h1>WebP圖片回退方案示例</h1>
    
    <div class="example">
        <h2>方法1: picture元素 (推薦)</h2>
        <picture>
            <source srcset="/media/coffee_images/coffee_01.webp" type="image/webp">
            <source srcset="/media/coffee_images/coffee_01.png" type="image/png">
            <img src="/media/coffee_images/coffee_01.png" alt="咖啡圖片" loading="lazy">
        </picture>
        <p>瀏覽器會優先加載WebP格式，如果不支持則回退到PNG格式。</p>
    </div>
    
    <div class="example">
        <h2>方法2: JavaScript檢測</h2>
        <img src="/media/coffee_images/coffee_01.png" 
             data-webp="/media/coffee_images/coffee_01.webp"
             alt="咖啡圖片" 
             class="webp-fallback"
             loading="lazy">
        <p>使用JavaScript檢測瀏覽器是否支持WebP，並動態替換圖片源。</p>
    </div>
    
    <script>
        // WebP支持檢測
        function supportsWebP() {
            const canvas = document.createElement('canvas');
            if (canvas.getContext && canvas.getContext('2d')) {
                return canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
            }
            return false;
        }
        
        // 替換WebP圖片
        if (supportsWebP()) {
            document.querySelectorAll('.webp-fallback').forEach(img => {
                const webpSrc = img.getAttribute('data-webp');
                if (webpSrc) {
                    img.src = webpSrc;
                }
            });
        }
    </script>
</body>
</html>"""
    
    output_path = Path("templates/betweencoffee_delivery/webp_fallback_example.html")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f"創建WebP回退示例: {output_path}")

def main():
    """主函數"""
    print("=" * 60)
    print("Between Coffee 圖片優化工具")
    print("將PNG/JPG圖片轉換為WebP格式")
    print("=" * 60)
    
    # 定義要處理的目錄
    media_dirs = [
        'media/coffee_images',
        'media/bean_images',
        'media/menu_images',
        'media/avatars'
    ]
    
    # 檢查目錄是否存在
    existing_dirs = []
    for dir_path in media_dirs:
        if os.path.exists(dir_path):
            existing_dirs.append(dir_path)
        else:
            print(f"警告: 目錄不存在 {dir_path}")
    
    if not existing_dirs:
        print("錯誤: 未找到任何媒體目錄")
        return 1
    
    print(f"將處理以下目錄: {', '.join(existing_dirs)}")
    
    # 處理每個目錄
    total_converted = 0
    
    for dir_path in existing_dirs:
        print(f"\n處理目錄: {dir_path}")
        process_directory(dir_path, quality=85, max_workers=4)
    
    # 創建WebP回退示例
    print("\n" + "=" * 60)
    print("創建WebP回退方案示例...")
    create_webp_fallback_html()
    
    print("\n" + "=" * 60)
    print("圖片轉換完成!")
    print("=" * 60)
    
    # 使用建議
    print("\n使用建議:")
    print("1. 在模板中使用<picture>元素實現WebP回退")
    print("2. 對於動態生成的圖片，使用JavaScript檢測WebP支持")
    print("3. 定期運行此腳本以轉換新上傳的圖片")
    print("4. 考慮在Django視圖中添加WebP支持檢測")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n用戶中斷操作")
        sys.exit(1)
    except Exception as e:
        print(f"錯誤: {e}")
        sys.exit(1)