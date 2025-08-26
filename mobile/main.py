#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移动端闲鱼自动评论助手 - Kivy移动应用主程序
"""

import os
import sys
import threading
import time
from pathlib import Path

# Kivy配置 - 必须在导入kivy之前设置
os.environ['KIVY_WINDOW_ICON'] = 'assets/icon.png'

from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.logger import Logger
from kivy.utils import platform

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.screenmanager import MDScreenManager, MDScreen
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.toolbar import MDToolbar
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRectangleFlatButton
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.slider import MDSlider
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.list import MDList, OneLineListItem, TwoLineListItem, ThreeLineListItem

# 添加核心模块路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# 导入核心功能模块
try:
    from main import XianyuCommentAssistant
    from keyword_manager import KeywordStatus
except ImportError as e:
    Logger.error(f"Mobile: 导入核心模块失败: {e}")
    sys.exit(1)

class ParameterInputScreen(MDScreen):
    """参数输入界面"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'parameters'
        
        # 创建主布局
        main_layout = MDBoxLayout(
            orientation='vertical',
            padding="20dp",
            spacing="15dp"
        )
        
        # 工具栏
        toolbar = MDToolbar(
            title="参数设置",
            elevation=2
        )
        main_layout.add_widget(toolbar)
        
        # 滚动视图容器
        scroll = MDScrollView()
        content_layout = MDBoxLayout(
            orientation='vertical',
            spacing="15dp",
            size_hint_y=None,
            height="800dp"
        )
        
        # 关键词输入卡片
        keyword_card = self._create_keyword_input_card()
        content_layout.add_widget(keyword_card)
        
        # 评论类型选择卡片
        comment_type_card = self._create_comment_type_card()
        content_layout.add_widget(comment_type_card)
        
        # 任务配置卡片
        task_config_card = self._create_task_config_card()
        content_layout.add_widget(task_config_card)
        
        # API配置卡片
        api_config_card = self._create_api_config_card()
        content_layout.add_widget(api_config_card)
        
        # 反检测设置卡片
        anti_detection_card = self._create_anti_detection_card()
        content_layout.add_widget(anti_detection_card)
        
        scroll.add_widget(content_layout)
        main_layout.add_widget(scroll)
        
        # 开始任务按钮
        start_button = MDRaisedButton(
            text="开始任务",
            theme_icon_color="Custom",
            icon_color="white",
            md_bg_color="green",
            size_hint=(1, None),
            height="50dp",
            on_release=self.start_task
        )
        main_layout.add_widget(start_button)
        
        self.add_widget(main_layout)
        
        # 存储控件引用
        self.widgets = {}
    
    def _create_keyword_input_card(self):
        """创建关键词输入卡片"""
        card = MDCard(
            size_hint=(1, None),
            height="200dp",
            padding="15dp",
            elevation=2
        )
        
        layout = MDBoxLayout(orientation='vertical', spacing="10dp")
        
        title = MDLabel(
            text="关键词设置",
            theme_text_color="Primary",
            size_hint_y=None,
            height="30dp",
            font_style="H6"
        )
        layout.add_widget(title)
        
        # 关键词输入框
        self.keyword_input = MDTextField(
            hint_text="输入关键词，用逗号分隔",
            helper_text="例如: 手机,电脑,相机",
            helper_text_mode="on_focus",
            multiline=True,
            max_text_length=500
        )
        layout.add_widget(self.keyword_input)
        
        card.add_widget(layout)
        return card
    
    def _create_comment_type_card(self):
        """创建评论类型选择卡片"""
        card = MDCard(
            size_hint=(1, None),
            height="250dp",
            padding="15dp",
            elevation=2
        )
        
        layout = MDBoxLayout(orientation='vertical', spacing="10dp")
        
        title = MDLabel(
            text="评论类型",
            theme_text_color="Primary",
            size_hint_y=None,
            height="30dp",
            font_style="H6"
        )
        layout.add_widget(title)
        
        # 评论类型复选框
        self.comment_types = {}
        comment_options = [
            ("inquiry", "询价型评论"),
            ("interest", "感兴趣型评论"),
            ("compliment", "夸赞型评论"),
            ("comparison", "对比咨询型评论"),
            ("concern", "关注型评论")
        ]
        
        for key, label in comment_options:
            checkbox_layout = MDBoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height="40dp",
                spacing="10dp"
            )
            
            checkbox = MDCheckbox(
                size_hint=(None, None),
                size=("30dp", "30dp"),
                active=True if key in ["inquiry", "interest"] else False
            )
            
            checkbox_label = MDLabel(
                text=label,
                theme_text_color="Primary"
            )
            
            checkbox_layout.add_widget(checkbox)
            checkbox_layout.add_widget(checkbox_label)
            layout.add_widget(checkbox_layout)
            
            self.comment_types[key] = checkbox
        
        card.add_widget(layout)
        return card
    
    def _create_task_config_card(self):
        """创建任务配置卡片"""
        card = MDCard(
            size_hint=(1, None),
            height="200dp",
            padding="15dp",
            elevation=2
        )
        
        layout = MDBoxLayout(orientation='vertical', spacing="10dp")
        
        title = MDLabel(
            text="任务配置",
            theme_text_color="Primary",
            size_hint_y=None,
            height="30dp",
            font_style="H6"
        )
        layout.add_widget(title)
        
        # 每个关键词最大商品数
        max_products_label = MDLabel(
            text="每个关键词最大处理商品数: 50",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="30dp"
        )
        layout.add_widget(max_products_label)
        
        self.max_products_slider = MDSlider(
            min=10,
            max=200,
            value=50,
            step=10,
            size_hint_y=None,
            height="40dp"
        )
        self.max_products_slider.bind(value=lambda x, v: setattr(max_products_label, 'text', f"每个关键词最大处理商品数: {int(v)}"))
        layout.add_widget(self.max_products_slider)
        
        # 任务名称
        self.task_name_input = MDTextField(
            hint_text="任务名称（可选）",
            helper_text="为任务指定一个名称便于识别",
            helper_text_mode="on_focus"
        )
        layout.add_widget(self.task_name_input)
        
        card.add_widget(layout)
        return card
    
    def _create_api_config_card(self):
        """创建API配置卡片"""
        card = MDCard(
            size_hint=(1, None),
            height="150dp",
            padding="15dp",
            elevation=2
        )
        
        layout = MDBoxLayout(orientation='vertical', spacing="10dp")
        
        title = MDLabel(
            text="DeepSeek API配置",
            theme_text_color="Primary",
            size_hint_y=None,
            height="30dp",
            font_style="H6"
        )
        layout.add_widget(title)
        
        # API密钥输入
        self.api_key_input = MDTextField(
            hint_text="DeepSeek API密钥",
            helper_text="留空将仅使用模板生成评论",
            helper_text_mode="on_focus",
            password=True
        )
        layout.add_widget(self.api_key_input)
        
        card.add_widget(layout)
        return card
    
    def _create_anti_detection_card(self):
        """创建反检测设置卡片"""
        card = MDCard(
            size_hint=(1, None),
            height="180dp",
            padding="15dp",
            elevation=2
        )
        
        layout = MDBoxLayout(orientation='vertical', spacing="10dp")
        
        title = MDLabel(
            text="反检测设置",
            theme_text_color="Primary",
            size_hint_y=None,
            height="30dp",
            font_style="H6"
        )
        layout.add_widget(title)
        
        # 评论间隔设置
        interval_label = MDLabel(
            text="评论间隔: 15-45秒",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="30dp"
        )
        layout.add_widget(interval_label)
        
        # 每日限制
        daily_limit_label = MDLabel(
            text="每日最大评论数: 100",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="30dp"
        )
        layout.add_widget(daily_limit_label)
        
        self.daily_limit_slider = MDSlider(
            min=20,
            max=300,
            value=100,
            step=20,
            size_hint_y=None,
            height="40dp"
        )
        self.daily_limit_slider.bind(value=lambda x, v: setattr(daily_limit_label, 'text', f"每日最大评论数: {int(v)}"))
        layout.add_widget(self.daily_limit_slider)
        
        card.add_widget(layout)
        return card
    
    def start_task(self, button):
        """开始任务"""
        try:
            # 获取用户输入
            keywords_text = self.keyword_input.text.strip()
            if not keywords_text:
                self.show_error_dialog("请输入至少一个关键词")
                return
            
            keywords = [kw.strip() for kw in keywords_text.split(',') if kw.strip()]
            if not keywords:
                self.show_error_dialog("请输入有效的关键词")
                return
            
            # 获取选中的评论类型
            selected_types = []
            for key, checkbox in self.comment_types.items():
                if checkbox.active:
                    selected_types.append(key)
            
            if not selected_types:
                self.show_error_dialog("请至少选择一种评论类型")
                return
            
            # 获取其他参数
            max_products = int(self.max_products_slider.value)
            task_name = self.task_name_input.text.strip() or None
            api_key = self.api_key_input.text.strip() or None
            daily_limit = int(self.daily_limit_slider.value)
            
            # 传递参数给主应用
            app = App.get_running_app()
            app.start_keyword_task(
                keywords=keywords,
                comment_types=selected_types,
                max_products_per_keyword=max_products,
                task_name=task_name,
                api_key=api_key,
                daily_limit=daily_limit
            )
            
            # 切换到监控界面
            app.root.current = 'monitor'
            
        except Exception as e:
            Logger.error(f"Mobile: 启动任务失败: {e}")
            self.show_error_dialog(f"启动任务失败: {str(e)}")
    
    def show_error_dialog(self, message):
        """显示错误对话框"""
        dialog = MDDialog(
            title="错误",
            text=message,
            buttons=[
                MDFlatButton(
                    text="确定",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()

class MonitorScreen(MDScreen):
    """任务监控界面"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'monitor'
        
        # 创建主布局
        main_layout = MDBoxLayout(
            orientation='vertical',
            padding="20dp",
            spacing="15dp"
        )
        
        # 工具栏
        toolbar = MDToolbar(
            title="任务监控",
            elevation=2,
            right_action_items=[
                ["stop", lambda x: self.stop_task()]
            ]
        )
        main_layout.add_widget(toolbar)
        
        # 滚动视图
        scroll = MDScrollView()
        content_layout = MDBoxLayout(
            orientation='vertical',
            spacing="15dp",
            size_hint_y=None,
            height="600dp"
        )
        
        # 任务状态卡片
        self.status_card = self._create_status_card()
        content_layout.add_widget(self.status_card)
        
        # 当前关键词卡片
        self.current_keyword_card = self._create_current_keyword_card()
        content_layout.add_widget(self.current_keyword_card)
        
        # 统计信息卡片
        self.stats_card = self._create_stats_card()
        content_layout.add_widget(self.stats_card)
        
        scroll.add_widget(content_layout)
        main_layout.add_widget(scroll)
        
        self.add_widget(main_layout)
        
        # 定期更新状态
        self.update_event = Clock.schedule_interval(self.update_status, 2.0)
    
    def _create_status_card(self):
        """创建任务状态卡片"""
        card = MDCard(
            size_hint=(1, None),
            height="120dp",
            padding="15dp",
            elevation=2
        )
        
        layout = MDBoxLayout(orientation='vertical', spacing="10dp")
        
        title = MDLabel(
            text="任务状态",
            theme_text_color="Primary",
            size_hint_y=None,
            height="30dp",
            font_style="H6"
        )
        layout.add_widget(title)
        
        self.task_status_label = MDLabel(
            text="未开始",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="25dp"
        )
        layout.add_widget(self.task_status_label)
        
        self.progress_bar = MDProgressBar(
            value=0,
            size_hint_y=None,
            height="20dp"
        )
        layout.add_widget(self.progress_bar)
        
        card.add_widget(layout)
        return card
    
    def _create_current_keyword_card(self):
        """创建当前关键词卡片"""
        card = MDCard(
            size_hint=(1, None),
            height="200dp",
            padding="15dp",
            elevation=2
        )
        
        layout = MDBoxLayout(orientation='vertical', spacing="10dp")
        
        title = MDLabel(
            text="当前关键词",
            theme_text_color="Primary",
            size_hint_y=None,
            height="30dp",
            font_style="H6"
        )
        layout.add_widget(title)
        
        self.current_keyword_label = MDLabel(
            text="无",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="25dp"
        )
        layout.add_widget(self.current_keyword_label)
        
        self.keyword_progress_label = MDLabel(
            text="进度: 0/0 商品",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="25dp"
        )
        layout.add_widget(self.keyword_progress_label)
        
        self.keyword_stats_label = MDLabel(
            text="评论: 0生成/0发布",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="25dp"
        )
        layout.add_widget(self.keyword_stats_label)
        
        card.add_widget(layout)
        return card
    
    def _create_stats_card(self):
        """创建统计信息卡片"""
        card = MDCard(
            size_hint=(1, None),
            height="200dp",
            padding="15dp",
            elevation=2
        )
        
        layout = MDBoxLayout(orientation='vertical', spacing="10dp")
        
        title = MDLabel(
            text="整体统计",
            theme_text_color="Primary",
            size_hint_y=None,
            height="30dp",
            font_style="H6"
        )
        layout.add_widget(title)
        
        self.total_keywords_label = MDLabel(
            text="关键词: 0完成/0总数",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="25dp"
        )
        layout.add_widget(self.total_keywords_label)
        
        self.total_products_label = MDLabel(
            text="商品: 0处理",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="25dp"
        )
        layout.add_widget(self.total_products_label)
        
        self.total_comments_label = MDLabel(
            text="评论: 0生成/0发布",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="25dp"
        )
        layout.add_widget(self.total_comments_label)
        
        card.add_widget(layout)
        return card
    
    def update_status(self, dt):
        """更新状态显示"""
        try:
            app = App.get_running_app()
            if app.assistant:
                status = app.assistant.get_keyword_task_status()
                
                # 更新任务状态
                if status.get('is_running'):
                    self.task_status_label.text = "运行中"
                    
                    # 更新进度条
                    queue_status = status.get('queue_status', {})
                    total_keywords = queue_status.get('total_keywords', 1)
                    processed_keywords = queue_status.get('processed_keywords', 0)
                    progress = processed_keywords / max(total_keywords, 1) * 100
                    self.progress_bar.value = progress
                    
                    # 更新当前关键词信息
                    current_keyword = status.get('current_keyword')
                    if current_keyword:
                        self.current_keyword_label.text = current_keyword['keyword']
                        self.keyword_progress_label.text = f"进度: {current_keyword['products_processed']}/{current_keyword['max_products']} 商品"
                        self.keyword_stats_label.text = f"评论: {current_keyword['comments_generated']}生成/{current_keyword['comments_published']}发布"
                    
                    # 更新整体统计
                    session_stats = status.get('session_stats', {})
                    self.total_keywords_label.text = f"关键词: {processed_keywords}完成/{total_keywords}总数"
                    self.total_products_label.text = f"商品: {session_stats.get('products_processed', 0)}处理"
                    self.total_comments_label.text = f"评论: {session_stats.get('comments_generated', 0)}生成/{session_stats.get('comments_published', 0)}发布"
                    
                else:
                    self.task_status_label.text = "已停止"
                    self.progress_bar.value = 0
        
        except Exception as e:
            Logger.error(f"Mobile: 更新状态失败: {e}")
    
    def stop_task(self):
        """停止任务"""
        try:
            app = App.get_running_app()
            if app.assistant:
                app.assistant.stop_task()
                
            # 显示确认对话框
            dialog = MDDialog(
                title="任务已停止",
                text="任务已成功停止",
                buttons=[
                    MDFlatButton(
                        text="返回设置",
                        on_release=lambda x: (dialog.dismiss(), setattr(app.root, 'current', 'parameters'))
                    ),
                    MDFlatButton(
                        text="查看历史",
                        on_release=lambda x: (dialog.dismiss(), setattr(app.root, 'current', 'history'))
                    )
                ]
            )
            dialog.open()
            
        except Exception as e:
            Logger.error(f"Mobile: 停止任务失败: {e}")

class HistoryScreen(MDScreen):
    """历史记录界面"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'history'
        
        # 创建主布局
        main_layout = MDBoxLayout(
            orientation='vertical',
            padding="20dp",
            spacing="15dp"
        )
        
        # 工具栏
        toolbar = MDToolbar(
            title="历史记录",
            elevation=2,
            right_action_items=[
                ["refresh", lambda x: self.refresh_history()]
            ]
        )
        main_layout.add_widget(toolbar)
        
        # 历史记录列表
        scroll = MDScrollView()
        self.history_list = MDList()
        scroll.add_widget(self.history_list)
        main_layout.add_widget(scroll)
        
        self.add_widget(main_layout)
        
        # 加载历史记录
        Clock.schedule_once(self.load_history, 0.5)
    
    def load_history(self, dt=None):
        """加载历史记录"""
        try:
            app = App.get_running_app()
            if app.assistant:
                history = app.assistant.get_keyword_history()
                
                self.history_list.clear_widgets()
                
                for record in history:
                    item = ThreeLineListItem(
                        text=f"关键词: {record['keyword']}",
                        secondary_text=f"状态: {record['status']} | 商品: {record['products_processed']} | 评论: {record['comments_published']}",
                        tertiary_text=f"成功率: {record['success_rate']:.1f}% | 时长: {record.get('duration', 0):.0f}秒"
                    )
                    self.history_list.add_widget(item)
                
                if not history:
                    empty_item = OneLineListItem(text="暂无历史记录")
                    self.history_list.add_widget(empty_item)
        
        except Exception as e:
            Logger.error(f"Mobile: 加载历史记录失败: {e}")
    
    def refresh_history(self):
        """刷新历史记录"""
        self.load_history()

class XianyuMobileApp(MDApp):
    """闲鱼移动应用主类"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.assistant = None
        self.title = "闲鱼自动评论助手"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
    
    def build(self):
        """构建应用界面"""
        try:
            # 初始化核心助手（在后台线程中）
            threading.Thread(target=self.init_assistant, daemon=True).start()
            
            # 创建屏幕管理器
            sm = MDScreenManager()
            
            # 添加屏幕
            sm.add_widget(ParameterInputScreen())
            sm.add_widget(MonitorScreen())
            sm.add_widget(HistoryScreen())
            
            # 创建底部导航
            bottom_nav = MDBottomNavigation()
            
            # 参数设置标签页
            param_item = MDBottomNavigationItem(
                name='parameters',
                text='参数设置',
                icon='settings'
            )
            param_item.add_widget(ParameterInputScreen())
            bottom_nav.add_widget(param_item)
            
            # 任务监控标签页
            monitor_item = MDBottomNavigationItem(
                name='monitor',
                text='任务监控',
                icon='monitor'
            )
            monitor_item.add_widget(MonitorScreen())
            bottom_nav.add_widget(monitor_item)
            
            # 历史记录标签页
            history_item = MDBottomNavigationItem(
                name='history',
                text='历史记录',
                icon='history'
            )
            history_item.add_widget(HistoryScreen())
            bottom_nav.add_widget(history_item)
            
            return bottom_nav
            
        except Exception as e:
            Logger.error(f"Mobile: 构建界面失败: {e}")
            return MDLabel(text=f"应用启动失败: {str(e)}")
    
    def init_assistant(self):
        """初始化助手（后台线程）"""
        try:
            self.assistant = XianyuCommentAssistant()
            # 注意：移动端可能需要特殊的设备连接配置
            # success = self.assistant.initialize_components()
            Logger.info("Mobile: 核心助手初始化完成")
        except Exception as e:
            Logger.error(f"Mobile: 初始化核心助手失败: {e}")
    
    def start_keyword_task(self, keywords, comment_types, max_products_per_keyword, 
                          task_name=None, api_key=None, daily_limit=100):
        """启动关键词任务"""
        try:
            if not self.assistant:
                self.show_error("系统未初始化完成，请稍后再试")
                return
            
            # 在后台线程中启动任务
            def run_task():
                try:
                    success = self.assistant.start_keyword_batch_task(
                        keywords=keywords,
                        comment_types=comment_types,
                        max_products_per_keyword=max_products_per_keyword,
                        task_name=task_name
                    )
                    if not success:
                        self.show_error("启动任务失败")
                except Exception as e:
                    Logger.error(f"Mobile: 启动任务异常: {e}")
                    self.show_error(f"启动任务异常: {str(e)}")
            
            threading.Thread(target=run_task, daemon=True).start()
            
        except Exception as e:
            Logger.error(f"Mobile: 启动关键词任务失败: {e}")
            self.show_error(f"启动任务失败: {str(e)}")
    
    @mainthread
    def show_error(self, message):
        """显示错误信息（主线程）"""
        dialog = MDDialog(
            title="错误",
            text=message,
            buttons=[
                MDFlatButton(
                    text="确定",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()

if __name__ == '__main__':
    # 设置日志级别
    Logger.setLevel('INFO')
    
    # 启动应用
    XianyuMobileApp().run()