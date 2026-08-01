import os
import shutil

# 來源資料夾與目標輸出資料夾分開，確保絕對不破壞原本的珍貴檔案！
SOURCE_DIR = r"C:\music_raw"
OUTPUT_DIR = r"C:\music"

def run_safe_rename():
    if not os.path.exists(SOURCE_DIR):
        print("找不到來源資料夾！")
        return
    
    # 建立一個乾淨的輸出資料夾
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    all_files = os.listdir(SOURCE_DIR)
    music_files = [f for f in all_files if f.lower().endswith(('.mp3', '.wma', '.wav'))]
    
    print("開始安全改造，共找到 {} 首音樂...".format(len(music_files)))
    success_count = 0
    index_list = []
    
    for index, music_file in enumerate(music_files, start=1):
        raw_name, ext = os.path.splitext(music_file)
        formatted_number = str(index).zfill(3)
        
        # 定義原始與全新的路徑
        old_music_path = os.path.join(SOURCE_DIR, music_file)
        new_music_path = os.path.join(OUTPUT_DIR, "{}{}".format(formatted_number, ext.lower()))
        
        old_lyric_path = os.path.join(SOURCE_DIR, raw_name + ".txt")
        new_lyric_path = os.path.join(OUTPUT_DIR, "{}.txt".format(formatted_number))
        
        # 讀取舊歌詞（嘗試多種編碼）
        lyric_content = ""
        if os.path.exists(old_lyric_path):
            for encoding in ['utf-8-sig', 'big5', 'gbk']:
                try:
                    with open(old_lyric_path, "r", encoding=encoding, errors="ignore") as f:
                        lyric_content = f.read()
                    break # 成功讀取就跳出編碼嘗試
                except:
                    continue
        
        # 🌟 核心安全修正：將純乾淨的「中文歌名」強行塞入歌詞第一行
        # 如果原本檔名帶有數字（如 01.晴天），這裡可以用你之前爬蟲的 clean_song_name(raw_name)
        clean_title = raw_name 
        new_lyric_content = "{}\n{}".format(clean_title, lyric_content)
        
        try:
            # 1. 寫入全新的優化歌詞到新資料夾
            with open(new_lyric_path, "w", encoding="utf-8-sig") as f:
                f.write(new_lyric_content)
                
            # 2. 用複製（Copy）取代移動（Rename），萬一出錯，原本的歌依然安全無損！
            if os.path.exists(old_music_path):
                shutil.copy(old_music_path, new_music_path)
                
            index_list.append("{} : {}\n".format(formatted_number, clean_title))
            success_count += 1
            print("安全複製並封裝: [{}] ---> [{}]".format(clean_title, formatted_number))
            
        except Exception as e:
            print("處理失敗 [{}]: {}".format(clean_title, e))
            
    # 寫入索引清單
    index_file_path = os.path.join(OUTPUT_DIR, "000_index.txt")
    try:
        with open(index_file_path, "w", encoding="utf-8-sig") as f:
            f.writelines(index_list)
        print("\n[索引清單 000_index.txt 已成功生成！]")
    except Exception as e:
        print("\n寫入索引清單失敗: {}".format(e))
        
    print("\n安全改造大功告成！已成功生成 {} 組標準老兵檔案！".format(success_count))

if __name__ == "__main__":
    run_safe_rename()
