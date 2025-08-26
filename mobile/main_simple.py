#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
闲鱼自动评论助手 - Android移动版
简化版本，确保构建成功
"""

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # 标题
        title = Label(
            text='闲鱼自动评论助手\nAndroid版本',
            font_size='24sp',
            size_hint_y=None,
            height='100dp',
            text_size=(None, None),
            halign='center'
        )
        
        # 版本信息
        info = Label(
            text='版本: 1.0\n构建: GitHub Actions\n\n这是移动端测试版本\n完整功能请使用桌面版本',
            font_size='16sp',
            text_size=(None, None),
            halign='center',
            valign='middle'
        )
        
        # 测试按钮
        test_btn = Button(
            text='测试按钮 - 点击验证',
            size_hint_y=None,
            height='50dp'
        )
        test_btn.bind(on_press=self.on_test_button)
        
        # 状态标签
        self.status_label = Label(
            text='状态: 就绪',
            font_size='14sp',
            size_hint_y=None,
            height='40dp'
        )
        
        layout.add_widget(title)
        layout.add_widget(info)
        layout.add_widget(test_btn)
        layout.add_widget(self.status_label)
        
        self.add_widget(layout)
    
    def on_test_button(self, instance):
        instance.text = '✓ 测试成功!'
        self.status_label.text = '状态: 交互功能正常'
        
        def reset_button(dt):
            instance.text = '测试按钮 - 点击验证'
            self.status_label.text = '状态: 就绪'
        
        Clock.schedule_once(reset_button, 2)

class XianyuMobileApp(App):
    def build(self):
        # 设置应用标题
        self.title = '闲鱼自动评论助手'
        
        # 创建屏幕管理器
        sm = ScreenManager()
        
        # 添加主屏幕
        main_screen = MainScreen(name='main')
        sm.add_widget(main_screen)
        
        return sm

def main():
    """主入口函数"""
    try:
        XianyuMobileApp().run()
    except Exception as e:
        print(f"应用启动失败: {e}")

if __name__ == '__main__':
    main()