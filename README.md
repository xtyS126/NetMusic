# 🎵 网络音乐库系统

[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Flask 2.2+](https://img.shields.io/badge/Flask-2.2%2B-green)](https://flask.palletsprojects.com/)

## 📖 项目简介
基于Flask框架开发的网络音乐管理系统，适用于：
- 在线音乐平台原型开发
- 智能音乐设备后台管理
- 个人音乐收藏库搭建
- 音乐文件共享系统基础框架

## 🌟 功能特性
### 音乐管理功能
| 功能                 | 权限要求      | 技术实现                      |
|----------------------|-------------|-----------------------------|
| MP3文件上传          | 所有用户     | 自动重命名+格式校验            |
| 安全播放链接生成      | 所有用户     | 带时间戳的URL `/play/<filename>` |
| 音乐文件批量管理      | 管理员       | 后台删除/编辑操作              |
| 音乐元数据解析        | 系统自动     | 使用Mutagen解析时长信息        |

### 用户系统
- **注册/登录**：Flask-Login实现会话保持
- **权限分级**：
  - 匿名用户：基础文件上传
  - 普通用户：个人上传历史查看
  - 管理员：全局用户/音乐管理

## 🚀 快速开始
### 环境配置
```bash
# 克隆仓库
git clone [项目地址]

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
flask init-db

# 启动开发服务器
flask run --port 3354