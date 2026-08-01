import os
import re
import urllib.parse
import requests

# ----------------- 設定區 -----------------
MUSIC_DIR = r"C:\music_raw"  # 音樂資料夾路徑
# ------------------------------------------

def clean_song_name(filename):
    """ 清理波名，移走副檔名和前面的數字序號（例如將 '01.晴天.mp3' 變為 '晴天'） """
    name, _ = os.path.splitext(filename)
    # 去除開頭的數字、點、空格 (例如 01. 晴天 -> 晴天)
    name = re.sub(r'^\d+[\.\s\-]*', '', name).strip()
    return name

def fetch_plain_lyrics(song_title, artist="周杰倫"):
    """ 調用免費的 LRCLIB API 搜尋並下載純文字歌詞 """
    print(f"正在網上搜尋: 【{song_title}】...")
    
    # 使用一般關鍵字搜尋參數 q
    query_str = f"q={urllib.parse.quote(artist + ' ' + song_title)}"
    url = f"https://lrclib.net/api/search?{query_str}"
    
    headers = {
        "User-Agent": "JayChouLyricsFetcher/1.0 (https://github.com)"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            results = response.json()
            
            # 確保有搜尋到結果，且結果是個清單並包含至少一筆資料
            if results and isinstance(results, list) and len(results) > 0:
                # 拿取第一筆最精準的匹配資料
                best_match = results[0]
                
                # 優先拿取 plainLyrics (純文字歌詞)
                if best_match.get("plainLyrics"):
                    return best_match["plainLyrics"]
                elif best_match.get("syncedLyrics"):
                    # 如果只有動態歌詞，就用正規表示式把時間軸 [00:00.00] 削走
                    synced = best_match["syncedLyrics"]
                    plain = re.sub(r'\[\d{2}:\d{2}\.\d{2,3}\]', '', synced)
                    return plain.strip()
            return None
        else:
            print(f"❌ 伺服器回應錯誤，狀態碼: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 網絡連線發生錯誤: {e}")
        return None

def main():
    if not os.path.exists(MUSIC_DIR):
        print(f"❌ 錯誤：找不到 '{MUSIC_DIR}' 資料夾，請先建立它。")
        return
        
    files = os.listdir(MUSIC_DIR)
    music_files = [f for f in files if f.endswith(('.mp3', '.wma', '.wav'))]
    
    if not music_files:
        print(f"ℹ️ '{MUSIC_DIR}' 資料夾內沒有發現 MP3/WMA 音樂檔案。")
        return
        
    print(f"動工！共偵測到 {len(music_files)} 首歌曲。")
    success_count = 0
    
    for filename in music_files:
        raw_name, _ = os.path.splitext(filename)
        txt_path = os.path.join(MUSIC_DIR, f"{raw_name}.txt")
        
        if os.path.exists(txt_path):
            print(f"⏩ 【{raw_name}】已有歌詞，跳過。")
            continue
            
        search_title = clean_song_name(filename)
        lyrics = fetch_plain_lyrics(search_title)
        
        if lyrics:
            # 🌟 核心修正：配合播放器排版，將乾淨的歌名強行寫在第一行！
            # 格式：[歌名] + 換行 + 歌詞
            formatted_content = f"{search_title}\n{lyrics}"
            
            with open(txt_path, "w", encoding="utf-8-sig") as f:
                f.write(formatted_content)
                
            print(f"✅ 成功下載並為播放器優化格式: {raw_name}.txt")
            success_count += 1
        else:
            print(f"❌ 搵唔到【{search_title}】嘅歌詞，請稍後手動建立。")
            
    print(f"\n🎉 大功告成！本次新下載了 {success_count} 首歌曲的歌詞。")


if __name__ == "__main__":
    main()