import os
import json
import requests
from urllib.parse import urlparse

# ================= 配置 =================
# 目标源 JSON（Vercel 源）
SOURCE_URL = "https://emby-icon.vercel.app/TFEL-Emby.json"
# 保存的 JSON 文件名
OUTPUT_JSON_NAME = "TFEL-Emby-Mirror.json"
# 图片保存目录
ICONS_DIR = "icons"
# =======================================

def run():
    # 1. 获取当前仓库信息 (由 GitHub Action 环境变量自动注入)
    # 格式通常是 "用户名/仓库名"
    repo_full_name = os.environ.get("GITHUB_REPOSITORY")
    if not repo_full_name:
        print("错误：无法获取 GITHUB_REPOSITORY 环境变量，请在 GitHub Actions 中运行。")
        return

    # 构造 GitHub Raw 的基础路径 (用于拼接新的图片链接)
    # 最终格式: https://ghproxy.net/https://raw.githubusercontent.com/用户名/仓库名/main/icons/
    # 注意：如果你稍后发现分支名不是 main 而是 master，请修改这里的 'main'
    base_url = f"https://ghproxy.net/https://raw.githubusercontent.com/{repo_full_name}/main/{ICONS_DIR}/"
    
    print(f"当前仓库: {repo_full_name}")
    print(f"图片基准路径: {base_url}")

    # 2. 创建目录
    if not os.path.exists(ICONS_DIR):
        os.makedirs(ICONS_DIR)

    # 3. 下载原始 JSON
    print("正在下载原始 JSON...")
    try:
        resp = requests.get(SOURCE_URL, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"下载 JSON 失败: {e}")
        return

    # 4. 遍历并处理
    items = data if isinstance(data, list) else data.get("icons", [])
    print(f"找到 {len(items)} 个图标，开始同步...")

    count = 0
    for item in items:
        # 获取 URL，兼容大小写
        original_url = item.get('url') or item.get('Url')
        if not original_url: 
            continue

        # 解析文件名
        parsed = urlparse(original_url)
        filename = os.path.basename(parsed.path)
        if not filename: continue

        # A. 下载图片到仓库目录
        save_path = os.path.join(ICONS_DIR, filename)
        if not os.path.exists(save_path):
            try:
                # 下载图片
                img_resp = requests.get(original_url, timeout=15)
                if img_resp.status_code == 200:
                    with open(save_path, "wb") as f:
                        f.write(img_resp.content)
                    print(f"[OK] 下载: {filename}")
                else:
                    print(f"[ERR] 图片 404: {filename}")
            except Exception as e:
                print(f"[ERR] 下载异常 {filename}: {e}")
        
        # B. 暴力替换 JSON 里的链接
        # 无论图片下载是否成功，我们将链接指向你的 GitHub 镜像
        # 这样即使脚本偶尔漏了图，下一次运行也能补上，且链接结构始终正确
        new_link = base_url + filename
        
        if 'url' in item: item['url'] = new_link
        if 'Url' in item: item['Url'] = new_link
        
        count += 1

    # 5. 保存修改后的 JSON
    with open(OUTPUT_JSON_NAME, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"处理完成！新 JSON 已保存为: {OUTPUT_JSON_NAME}")

if __name__ == "__main__":
    run()
