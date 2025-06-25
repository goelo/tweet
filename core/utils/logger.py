#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志记录系统
将控制台输出同时保存到日志文件
"""

import os
import sys
from datetime import datetime
from typing import TextIO


class DualOutput:
    """双重输出类 - 同时输出到控制台和文件"""
    
    def __init__(self, original_stream: TextIO, log_file: TextIO):
        self.original_stream = original_stream
        self.log_file = log_file
    
    def write(self, text: str):
        # 写入到原始流（控制台）
        self.original_stream.write(text)
        # 写入到日志文件
        self.log_file.write(text)
        # 确保实时写入
        self.original_stream.flush()
        self.log_file.flush()
    
    def flush(self):
        self.original_stream.flush()
        self.log_file.flush()
    
    def __getattr__(self, name):
        # 转发其他属性到原始流
        return getattr(self.original_stream, name)


class Logger:
    """日志管理器"""
    
    def __init__(self, log_file_path: str = "run.log"):
        self.log_file_path = log_file_path
        self.log_file = None
        self.original_stdout = None
        self.original_stderr = None
        self.dual_stdout = None
        self.dual_stderr = None
    
    def start_logging(self):
        """开始记录日志"""
        try:
            # 删除旧的日志文件
            if os.path.exists(self.log_file_path):
                os.remove(self.log_file_path)
            
            # 创建新的日志文件
            self.log_file = open(self.log_file_path, 'w', encoding='utf-8')
            
            # 写入日志头部信息
            start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.log_file.write(f"=== AutoX 运行日志 ===\n")
            self.log_file.write(f"开始时间: {start_time}\n")
            self.log_file.write(f"Python版本: {sys.version}\n")
            self.log_file.write(f"工作目录: {os.getcwd()}\n")
            self.log_file.write("=" * 60 + "\n\n")
            
            # 保存原始的输出流
            self.original_stdout = sys.stdout
            self.original_stderr = sys.stderr
            
            # 创建双重输出流
            self.dual_stdout = DualOutput(self.original_stdout, self.log_file)
            self.dual_stderr = DualOutput(self.original_stderr, self.log_file)
            
            # 重定向标准输出和错误输出
            sys.stdout = self.dual_stdout
            sys.stderr = self.dual_stderr
            
            print(f"📝 日志记录已启动: {self.log_file_path}")
            return True
            
        except Exception as e:
            print(f"❌ 启动日志记录失败: {e}")
            return False
    
    def stop_logging(self):
        """停止记录日志"""
        try:
            if self.original_stdout and self.original_stderr:
                # 恢复原始输出流
                sys.stdout = self.original_stdout
                sys.stderr = self.original_stderr
            
            if self.log_file:
                # 写入结束信息
                end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.log_file.write(f"\n\n" + "=" * 60 + "\n")
                self.log_file.write(f"结束时间: {end_time}\n")
                self.log_file.write("=== 日志记录结束 ===\n")
                
                # 关闭日志文件
                self.log_file.close()
                self.log_file = None
            
            print(f"📝 日志记录已停止: {self.log_file_path}")
            return True
            
        except Exception as e:
            print(f"❌ 停止日志记录失败: {e}")
            return False
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start_logging()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        if exc_type:
            # 如果有异常，记录到日志
            print(f"\n❌ 程序异常退出:")
            print(f"异常类型: {exc_type.__name__}")
            print(f"异常信息: {exc_val}")
            if exc_tb:
                import traceback
                print("异常堆栈:")
                traceback.print_tb(exc_tb)
        
        self.stop_logging()


# 创建全局日志管理器实例
app_logger = Logger()


def setup_logging(log_file_path: str = "run.log") -> bool:
    """
    设置日志记录
    
    Args:
        log_file_path: 日志文件路径
        
    Returns:
        是否设置成功
    """
    global app_logger
    app_logger = Logger(log_file_path)
    return app_logger.start_logging()


def cleanup_logging():
    """清理日志记录"""
    global app_logger
    if app_logger:
        app_logger.stop_logging()