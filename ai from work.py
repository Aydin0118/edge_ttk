import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import edge_tts
import asyncio
import threading
import os
from datetime import datetime

class TTSGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("Edge-TTS 语音生成器")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # 音色列表（根据您提供的图片信息）
        self.voices = [
            {"name": "zh-CN-XiaoxiaoNeural", "gender": "女", "desc": "最常用、最自然的女声之一，声音甜美、富有表现力。", "scene": "讲故事、旁白、有声书、客服"},
            {"name": "zh-CN-YunxiNeural", "gender": "男", "desc": "年轻、温和、友好的男声，略带磁性。", "scene": "对话解说、视频博客、轻松的内容"},
            {"name": "zh-CN-YunyangNeural", "gender": "男", "desc": "专业、沉稳的新闻播音男声，非常清晰、权威。", "scene": "新闻播报、知识科普、专业内容"},
            {"name": "zh-CN-XiaoyiNeural", "gender": "女", "desc": "声音活泼、可爱，充满活力，更像年轻女孩。", "scene": "儿童内容、活泼风格的视频、聊天"},
            {"name": "zh-CN-liaoning-XiaobeiNeural", "gender": "女", "desc": "带有东北地区口音的女声，非常接地气、有亲和力。", "scene": "搞笑段子、地方特色内容、直播"},
            {"name": "zh-HK-HiuGaaiNeural", "gender": "女", "desc": "粤语女声，清晰自然。", "scene": "粤语内容创作"},
            {"name": "zh-HK-HiuMaanNeural", "gender": "女", "desc": "另一款粤语女声，声音更成熟一些。", "scene": "粤语内容创作"},
            {"name": "zh-TW-HsiaoChenNeural", "gender": "女", "desc": "台湾普通话女声，语调温柔", "scene": "针对台湾地区的内容"}
        ]
        
        # 先初始化 selected_voice
        self.selected_voice = tk.StringVar(value=self.voices[0]["name"])
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 1. 音色选择区域
        ttk.Label(main_frame, text="选择音色:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # 创建音色选择框架
        voice_frame = ttk.LabelFrame(main_frame, text="可用音色", padding="5")
        voice_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        voice_frame.columnconfigure(0, weight=1)
        
        # 音色选择列表框
        self.voice_listbox = tk.Listbox(voice_frame, height=6, selectmode=tk.SINGLE)
        self.voice_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(voice_frame, orient=tk.VERTICAL, command=self.voice_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.voice_listbox.configure(yscrollcommand=scrollbar.set)
        
        # 填充音色列表
        for i, voice in enumerate(self.voices):
            display_text = f"{voice['name']} ({voice['gender']}) - {voice['desc'][:30]}..."
            self.voice_listbox.insert(tk.END, display_text)
        
        # 绑定选择事件
        self.voice_listbox.bind('<<ListboxSelect>>', self.on_voice_select)
        self.voice_listbox.selection_set(0)
        
        # 音色详情显示
        self.voice_detail_var = tk.StringVar(value="请选择一个音色查看详情")
        voice_detail_label = ttk.Label(voice_frame, textvariable=self.voice_detail_var, 
                                      wraplength=550, justify=tk.LEFT, background="#f0f0f0")
        voice_detail_label.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # 2. 文本输入区域
        ttk.Label(main_frame, text="输入文本:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky=tk.W, pady=(10, 5))
        
        text_frame = ttk.Frame(main_frame)
        text_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        self.text_input = tk.Text(text_frame, height=8, wrap=tk.WORD)
        self.text_input.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        text_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.text_input.yview)
        text_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.text_input.configure(yscrollcommand=text_scrollbar.set)
        
        # 3. 控制按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        button_frame.columnconfigure(1, weight=1)
        
        # 文件保存路径
        self.file_path_var = tk.StringVar(value="output.mp3")
        ttk.Entry(button_frame, textvariable=self.file_path_var, width=30).grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Button(button_frame, text="浏览...", command=self.browse_file).grid(row=0, column=1, sticky=tk.W)
        
        # 生成按钮
        ttk.Button(button_frame, text="生成音频", command=self.generate_audio).grid(row=0, column=2, sticky=tk.E, padx=(10, 0))
        
        # 4. 状态显示
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_label.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # 初始化显示第一个音色的详情
        self.on_voice_select(None)
        
    def on_voice_select(self, event):
        """当选择音色时更新详情显示"""
        selection = self.voice_listbox.curselection()
        if selection:
            index = selection[0]
            voice = self.voices[index]
            detail_text = f"音色: {voice['name']}\n性别: {voice['gender']}\n描述: {voice['desc']}\n适用场景: {voice['scene']}"
            self.voice_detail_var.set(detail_text)
            self.selected_voice.set(voice["name"])
    
    def browse_file(self):
        """选择保存文件路径"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".mp3",
            filetypes=[("MP3 files", "*.mp3"), ("All files", "*.*")]
        )
        if filename:
            self.file_path_var.set(filename)
    
    def generate_audio(self):
        """生成音频文件"""
        text = self.text_input.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("警告", "请输入要转换的文本！")
            return
        
        voice_name = self.selected_voice.get()
        file_path = self.file_path_var.get()
        
        if not file_path:
            messagebox.showwarning("警告", "请选择保存路径！")
            return
        
        # 在后台线程中运行异步任务
        self.status_var.set("正在生成音频...")
        thread = threading.Thread(target=self.run_async_tts, args=(text, voice_name, file_path))
        thread.daemon = True
        thread.start()
    
    def run_async_tts(self, text, voice, file_path):
        """在新线程中运行异步TTS任务"""
        try:
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 运行异步任务
            loop.run_until_complete(self.async_generate_audio(text, voice, file_path))
            loop.close()
            
            # 在主线程中更新状态
            self.root.after(0, lambda: self.status_var.set(f"生成完成: {file_path}"))
            self.root.after(0, lambda: messagebox.showinfo("成功", f"音频文件已生成:\n{file_path}"))
            
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"生成失败: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("错误", f"生成音频时出错:\n{str(e)}"))
    
    async def async_generate_audio(self, text, voice, file_path):
        """异步生成音频"""
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(file_path)

def main():
    # 设置Windows风格（如果可用）
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
    root = tk.Tk()
    app = TTSGenerator(root)
    root.mainloop()

if __name__ == "__main__":
    main()