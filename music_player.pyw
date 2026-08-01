import os
import math
import random
import time
import shutil
import tkinter as tk
from win32com.client import Dispatch
import ctypes # 🌟 每次開始播歌時，阻止 Windows 進入系統休眠
                     
ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001) 
# ES_SYSTEM_REQUIRED (0x00000001) 代表阻止系統休眠
# ES_CONTINUOUS (0x80000000) 代表保持這個狀態直到下一次通知

MUSIC_DIR = r"C:\music"

class JayPlayer(object):
    def setup_player_system(self, root):
        self.root = root
        self.root.title("老兵播放器")
        
        # 1. 實現全螢幕
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='#000000')
        
        try:
            self.wmp = Dispatch("WMPlayer.OCX.7")
        except:
            self.wmp = Dispatch("WMPlayer.OCX")
            
        self.history = []
        self.history_index = -1
        self.is_switching_song = False
        self.current_temp_music = None
        self.current_temp_lyric = None
        
        # 按鍵綁定
        self.root.bind("<Escape>", lambda e: self.quit_player())
        self.root.bind("<Right>", lambda e: self.play_next_pressed())
        self.root.bind("<Left>", lambda e: self.play_prev_pressed())
        
        # --- 🌟 專為小筆電（1024x600）設計的純淨版面排版 🌟 ---
        
        # 2. 歌名 Label：調整為 28 級字（適合 10 吋小螢幕），上下留白收緊，防止歌詞被擠走
        self.title_label = tk.Label(root, text="載入中...", font=("Microsoft JhengHei", 28, "bold"), fg="#A0A0A0", bg="#000000")
        self.title_label.pack(pady=(30, 10), fill="x")
        
        # 3. 歌詞 Text：調整為 18 級字，完美適配 600 像素的高度
        # expand=True 和 fill="both" 會自動把剩餘的全螢幕黑色空間填滿，文字絕對置中
        self.lyrics_text = tk.Text(root, font=("Microsoft JhengHei", 18), height=10, width=50, 
                                   fg="#A0A0A0", bg="#000000", bd=0, highlightthickness=0)
        self.lyrics_text.pack(pady=10, expand=True, fill="both")
        self.lyrics_text.tag_configure("center", justify='center')
        
        # 4. 徹底移除 Canvas（波浪畫布）以釋放處理器資源，達至完美屏保效果
        
        self.init_playlist()
        self.check_music_end()      # 啟動自動下一首
        self.play_next_random()     # 播放第一首
    
    
        
    def __init__(self, root):
        self.setup_player_system(root)
        
    def init_playlist(self):
        self.raw_playlist = []
        if not os.path.exists(MUSIC_DIR):
            return
            
        # 清理 Temp 檔案
        for f in os.listdir(MUSIC_DIR):
            if f.startswith('old_soldier_temp'):
                try:
                    os.remove(os.path.join(MUSIC_DIR, f))
                except:
                    pass
                    
        # 掃描音樂檔案
        for f in os.listdir(MUSIC_DIR):
            if f.endswith('.mp3') or f.endswith('.wav') or f.endswith('.wma'):
                if f.startswith('old_soldier_temp'):
                    continue
                full_music_path = os.path.join(MUSIC_DIR, f)
                raw_name, ext = os.path.splitext(f)
                
                lyric_file = os.path.join(MUSIC_DIR, raw_name + ".txt")
                if not os.path.exists(lyric_file):
                    lyric_file = None
                    
                self.raw_playlist.append({
                    'music_src': full_music_path,
                    'lyric_src': lyric_file,
                    'ext': ext,
                    'display_name': raw_name
                })
                
    def execute_play_logic(self, song_info):
        if self.is_switching_song:
            return
        self.is_switching_song = True
        
        try:
            # 切歌前先清空 URL，防止 check_music_end 誤判
            self.wmp.controls.stop()
            self.wmp.URL = ""
            
            # 刪除舊 Temp 檔案
            if self.current_temp_music and os.path.exists(self.current_temp_music):
                try: os.remove(self.current_temp_music)
                except: pass
            if self.current_temp_lyric and os.path.exists(self.current_temp_lyric):
                try: os.remove(self.current_temp_lyric)
                except: pass
                
            rand_id = str(random.randint(1000, 9999))
            self.current_temp_music = os.path.join(MUSIC_DIR, "old_soldier_temp_" + rand_id + song_info['ext'])
            self.current_temp_lyric = os.path.join(MUSIC_DIR, "old_soldier_temp_" + rand_id + ".txt")
            
            shutil.copy(song_info['music_src'], self.current_temp_music)
            
            if song_info['lyric_src'] and os.path.exists(song_info['lyric_src']):
                shutil.copy(song_info['lyric_src'], self.current_temp_lyric)
                self.load_lyrics(self.current_temp_lyric)
            else:
                self.title_label.config(text="歌曲: " + song_info['display_name'])
                self.lyrics_text.config(state=tk.NORMAL)
                self.lyrics_text.delete("1.0", tk.END)
                self.lyrics_text.insert(tk.END, "\n\n（未搵到歌詞文字檔）")
                self.lyrics_text.tag_add("center", "1.0", tk.END)
                self.lyrics_text.config(state=tk.DISABLED)
                
            # 🌟 舊電腦最穩定的 WMP 播放寫法：直接給 URL
            # 盡量避免頻繁操作 currentPlaylist，直接指定 URL 播放最流暢連貫
            self.wmp.URL = os.path.abspath(self.current_temp_music)
            self.wmp.controls.play()
            
        except Exception as e:
            print("播放出錯: {}".format(e))
            self.is_switching_song = False
            self.root.after(500, self.play_next_random)
            return
            
        # 稍微延遲 200 毫秒解鎖切歌狀態，留給 WMP 反應時間，但不用 time.sleep 卡死全機
        self.root.after(200, self.unlock_switching_song)

    # 🌟 新增一個輔助 function 用來解鎖狀態
    def unlock_switching_song(self):
        self.is_switching_song = False

    def play_next_random(self):
        if not self.raw_playlist:
            self.title_label.config(text="音樂資料夾內無任何音樂檔案", fg="#CCCCCC", bg="#000000")
            return
            
        # 如果只有一首歌，就無得揀，直接播
        if len(self.raw_playlist) == 1:
            current_song = self.raw_playlist[0]
        else:
            # 🌟 核心改動：如果抽中嘅歌同啱啱播完嘅歌一樣，就重新抽，抽到唔一樣為止！
            current_song = random.choice(self.raw_playlist)
            if self.history:
                last_song = self.history[self.history_index]
                while current_song == last_song:
                    current_song = random.choice(self.raw_playlist)
                    
        self.history = self.history[:self.history_index + 1]
        self.history.append(current_song)
        self.history_index = len(self.history) - 1
        self.execute_play_logic(current_song)

        
    def play_next_pressed(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.execute_play_logic(self.history[self.history_index])
        else:
            self.play_next_random()
            
    def play_prev_pressed(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.execute_play_logic(self.history[self.history_index])
            
    def load_lyrics(self, path_or_name):
        self.lyrics_text.config(state=tk.NORMAL)
        self.lyrics_text.delete("1.0", tk.END)
        try:
            with open(path_or_name, "r", encoding="utf-8-sig", errors="ignore") as f:
                lines = f.readlines()
            if lines:
                real_song_title = lines[0].strip()
                self.title_label.config(text=real_song_title)
                main_lyrics = "".join(lines[1:])
                self.lyrics_text.insert(tk.END, main_lyrics)
                self.lyrics_text.tag_add("center", "1.0", tk.END)
        except Exception as e:
            self.title_label.config(text="音樂播放中...")
            self.lyrics_text.insert(tk.END, "\n\n（歌詞讀取失敗: {}）".format(e))
            self.lyrics_text.tag_add("center", "1.0", tk.END)
        self.lyrics_text.config(state=tk.DISABLED)
        
    def check_music_end(self):
        try:
            # 只有在「非切歌狀態」下，才去檢查播放器狀態
            if not self.is_switching_song and hasattr(self, 'wmp'):
                current_state = self.wmp.playState
                
                # 🌟 核心修正：狀態 8 (唱完) 或 狀態 1 (播完後停低) 都要自動跳下一首
                # 並且確保 wmp 的 URL 不是空的（代表之前確實有歌在播）
                if current_state in (1, 8) and self.wmp.URL != "":
                    # 立即觸發下一首
                    self.play_next_random()
        except Exception as e:
            print("偵測播放狀態出錯: {}".format(e))
            
        # 🌟 將檢查頻率由 1 秒（1000ms）加快到 0.5 秒（500ms），反應更靈敏連貫
        self.root.after(500, self.check_music_end)
    
        
    def quit_player(self):
        try: self.wmp.controls.stop()
        except: pass
        if self.current_temp_music and os.path.exists(self.current_temp_music):
            try: os.remove(self.current_temp_music)
            except: pass
        if self.current_temp_lyric and os.path.exists(self.current_temp_lyric):
            try: os.remove(self.current_temp_lyric)
            except: pass
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = JayPlayer(root)
    root.mainloop()
