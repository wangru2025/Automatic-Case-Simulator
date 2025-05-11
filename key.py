import wx
import threading
import time
import ctypes

class KeySimulatorFrame(wx.Frame):
    def __init__(self, parent, title):
        super(KeySimulatorFrame, self).__init__(parent, title=title, size=(500, 300))
        self.running = False
        self.tray_icon = None
        
        # 虚拟键码映射字典
        self.key_map = {
            'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45, 'f': 0x46, 'g': 0x47,
            'h': 0x48, 'i': 0x49, 'j': 0x4A, 'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E,
            'o': 0x4F, 'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54, 'u': 0x55,
            'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59, 'z': 0x5A,
            '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34, '5': 0x35, '6': 0x36,
            '7': 0x37, '8': 0x38, '9': 0x39,
            'enter': 0x0D, 'space': 0x20, 'tab': 0x09, 'esc': 0x1B,
            'up': 0x26, 'down': 0x28, 'left': 0x25, 'right': 0x27,
            'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73, 'f5': 0x74, 'f6': 0x75,
            'f7': 0x76, 'f8': 0x77, 'f9': 0x78, 'f10': 0x79, 'f11': 0x7A, 'f12': 0x7B
        }

        # UI 布局
        self.init_ui()
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_ICONIZE, self.on_minimize)

        # 使用 keyboard 库注册全局快捷键（如果需要）
        self.register_hotkeys()

    def init_ui(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # 按键序列输入
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(wx.StaticText(panel, label="按键序列："), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.key_input = wx.TextCtrl(panel, value="")
        self.key_input.SetName("按键序列输入")  # 为读屏软件提供简短名称
        hbox1.Add(self.key_input, 1, wx.EXPAND)
        vbox.Add(hbox1, 0, wx.EXPAND | wx.ALL, 5)

        # 间隔时间
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2.Add(wx.StaticText(panel, label="间隔时间（秒）："), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.delay_input = wx.TextCtrl(panel, value="")
        self.delay_input.SetName("间隔时间输入")
        hbox2.Add(self.delay_input, 0, wx.EXPAND)
        vbox.Add(hbox2, 0, wx.EXPAND | wx.ALL, 5)

        # 等待时间
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        hbox3.Add(wx.StaticText(panel, label="等待时间（秒）："), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.wait_input = wx.TextCtrl(panel, value="")
        self.wait_input.SetName("等待时间输入")
        hbox3.Add(self.wait_input, 0, wx.EXPAND)
        vbox.Add(hbox3, 0, wx.EXPAND | wx.ALL, 5)

        # 循环次数
        hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        hbox4.Add(wx.StaticText(panel, label="循环模式："), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.loop_combo = wx.ComboBox(panel, choices=["无限循环", "自定义次数", "不循环"], style=wx.CB_READONLY)
        self.loop_combo.SetSelection(0)
        self.loop_combo.SetName("循环模式选择")
        hbox4.Add(self.loop_combo, 0, wx.EXPAND | wx.RIGHT, 5)
        self.loop_input = wx.TextCtrl(panel, value="1")
        self.loop_input.Enable(False)
        self.loop_input.SetName("循环次数输入")
        hbox4.Add(self.loop_input, 0, wx.EXPAND)
        vbox.Add(hbox4, 0, wx.EXPAND | wx.ALL, 5)
        self.loop_combo.Bind(wx.EVT_COMBOBOX, self.on_loop_combo_change)

        # 按钮
        hbox5 = wx.BoxSizer(wx.HORIZONTAL)
        self.start_button = wx.Button(panel, label="开始 (&S)")
        self.start_button.SetName("开始按钮")
        self.stop_button = wx.Button(panel, label="停止 (&T)")
        self.stop_button.Enable(False)
        self.stop_button.SetName("停止按钮")
        hbox5.Add(self.start_button, 1, wx.EXPAND | wx.RIGHT, 5)
        hbox5.Add(self.stop_button, 1, wx.EXPAND)
        vbox.Add(hbox5, 0, wx.EXPAND | wx.ALL, 5)
        self.start_button.Bind(wx.EVT_BUTTON, self.on_start)
        self.stop_button.Bind(wx.EVT_BUTTON, self.on_stop)

        # 状态标签
        self.status_label = wx.StaticText(panel, label="状态：未开始")
        self.status_label.SetName("当前状态")
        vbox.Add(self.status_label, 0, wx.ALL, 5)

        panel.SetSizer(vbox)

    def register_hotkeys(self):
        """注册全局快捷键（可选，如果需要使用 keyboard 库）"""
        try:
            import keyboard
            keyboard.add_hotkey('ctrl+win+alt+f5', self.on_hotkey_start_stop)
            keyboard.add_hotkey('ctrl+win+alt+f6', self.on_hotkey_show_hide)
        except ImportError:
            pass
        except Exception as e:
            wx.MessageBox(f"全局快捷键注册失败，错误信息: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)

    def on_hotkey_start_stop(self):
        """处理启动/停止快捷键"""
        if self.running:
            self.on_stop(None)
        else:
            self.on_start(None)

    def on_hotkey_show_hide(self):
        """处理显示/隐藏快捷键"""
        if self.IsIconized() or not self.IsShown():
            self.Iconize(False)
            self.Show(True)
            self.Raise()
        else:
            self.Iconize(True)
            self.Show(False)

    def on_minimize(self, event):
        """窗口最小化时隐藏到通知区域"""
        if event.Iconized():
            self.Show(False)
        event.Skip()

    def on_close(self, event):
        """关闭窗口时清理资源"""
        self.running = False
        event.Skip()

    def on_loop_combo_change(self, event):
        self.loop_input.Enable(self.loop_combo.GetValue() == "自定义次数")

    def on_start(self, event):
        if not self.running:
            self.running = True
            self.start_button.Enable(False)
            self.stop_button.Enable(True)
            self.update_status("启动中...")
            threading.Thread(target=self.auto_key_press, daemon=True).start()

    def on_stop(self, event):
        self.running = False
        self.start_button.Enable(True)
        self.stop_button.Enable(False)
        self.update_status("已停止")

    def update_status(self, message):
        wx.CallAfter(self.status_label.SetLabel, f"状态：{message}")

    def show_error(self, title, message):
        wx.CallAfter(wx.MessageBox, message, title, wx.OK | wx.ICON_ERROR)
        self.running = False
        wx.CallAfter(self.start_button.Enable, True)
        wx.CallAfter(self.stop_button.Enable, False)
        wx.CallAfter(self.status_label.SetLabel, "状态：错误已停止")

    def parse_key_sequence(self, text):
        """解析按键序列，逗号分隔"""
        return [key.strip() for key in text.split(',') if key.strip()]

    def press_key(self, key_code):
        """使用 keybd_event 模拟按键"""
        KEYEVENTF_KEYUP = 0x0002
        ctypes.windll.user32.keybd_event(key_code, 0, 0, 0)  # 按下
        time.sleep(0.05)  # 短暂延迟
        ctypes.windll.user32.keybd_event(key_code, 0, KEYEVENTF_KEYUP, 0)  # 释放

    def simulate_key_press(self, keys, delay, loop_count):
        """模拟按键，支持有限次数或无限循环"""
        cycle = 1
        if loop_count == -1:  # 无限循环
            while self.running:
                self.update_status(f"无限循环中 - 第 {cycle} 次")
                self.simulate_one_cycle(keys, delay)
                cycle += 1
        else:  # 有限次数
            for i in range(loop_count):
                if not self.running:
                    break
                self.update_status(f"循环中 - 第 {cycle}/{loop_count} 次")
                self.simulate_one_cycle(keys, delay)
                cycle += 1
            if self.running:
                self.update_status("模拟完成")
                self.running = False
                wx.CallAfter(self.start_button.Enable, True)
                wx.CallAfter(self.stop_button.Enable, False)

    def simulate_one_cycle(self, keys, delay):
        """模拟一轮按键"""
        for key in keys:
            if not self.running:
                break
            try:
                key_code = self.key_map.get(key.lower())
                if key_code is None:
                    raise ValueError(f"不支持的按键：{key}")
                self.press_key(key_code)
                time.sleep(delay)
            except Exception as e:
                self.show_error("按键模拟错误", f"无法模拟按键 '{key}'，错误：{str(e)}")
                return

    def auto_key_press(self):
        """自动按键程序"""
        try:
            key_text = self.key_input.GetValue().strip()
            if not key_text:
                self.show_error("错误", "请输入有效的按键序列！")
                return
            keys = self.parse_key_sequence(key_text)
            if not keys:
                self.show_error("错误", "无法解析按键序列！")
                return

            try:
                delay_text = self.delay_input.GetValue().strip()
                if not delay_text:
                    self.show_error("错误", "请输入间隔时间！")
                    return
                delay = float(delay_text)
                if delay <= 0:
                    self.show_error("错误", "间隔时间必须大于0！")
                    return
            except ValueError:
                self.show_error("错误", "请输入有效的间隔时间（必须为数字）！")
                return

            try:
                wait_text = self.wait_input.GetValue().strip()
                wait_time = 0
                if wait_text:
                    wait_time = float(wait_text)
                    if wait_time < 0:
                        self.show_error("错误", "等待时间不能为负数！")
                        return
                if wait_time > 0:
                    self.update_status(f"等待 {wait_time} 秒后开始")
                    for i in range(int(wait_time), 0, -1):
                        if not self.running:
                            return
                        self.update_status(f"等待 {i} 秒后开始")
                        time.sleep(1)
            except ValueError:
                self.show_error("错误", "请输入有效的等待时间（必须为数字）！")
                return

            loop_count = -1
            if self.loop_combo.GetValue() == "自定义次数":
                try:
                    loop_count = int(self.loop_input.GetValue())
                    if loop_count <= 0:
                        self.show_error("错误", "循环次数必须大于0！")
                        return
                except ValueError:
                    self.show_error("错误", "请输入有效的循环次数（必须为整数）！")
                    return
            elif self.loop_combo.GetValue() == "不循环":
                loop_count = 1

            if self.running:
                self.simulate_key_press(keys, delay, loop_count)
        except Exception as e:
            self.show_error("错误", f"发生未知错误：{str(e)}")

class KeySimulatorApp(wx.App):
    def OnInit(self):
        frame = KeySimulatorFrame(None, "按键模拟器")
        frame.Show(True)
        return True

if __name__ == "__main__":
    app = KeySimulatorApp(False)
    app.MainLoop()