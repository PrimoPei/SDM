#!/usr/bin/env python3
"""
清理所有生成图片的本地存储及相关记录的脚本
安全地清理：本地存储文件、数据库记录、JSON配置文件
"""

import os
import shutil
import sqlite3
import glob
from pathlib import Path
import json
from datetime import datetime

def backup_databases():
    """备份数据库文件"""
    print("📦 正在备份数据库文件...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(f"backup_{timestamp}")
    backup_dir.mkdir(exist_ok=True)
    
    # 备份数据库文件
    db_files = ["rooms.db", "sd-multiplayer-data/rooms_data.db"]
    for db_file in db_files:
        if Path(db_file).exists():
            backup_path = backup_dir / Path(db_file).name
            shutil.copy2(db_file, backup_path)
            print(f"   ✅ 已备份: {db_file} -> {backup_path}")
    
    return backup_dir

def clean_local_storage():
    """清理本地存储文件"""
    print("\n🗂️ 正在清理本地存储文件...")
    local_storage_path = Path("local_storage")
    
    if not local_storage_path.exists():
        print("   ℹ️  local_storage 目录不存在，跳过")
        return
    
    # 统计文件数量
    total_files = 0
    for root, dirs, files in os.walk(local_storage_path):
        total_files += len(files)
    
    print(f"   📊 发现 {total_files} 个文件需要清理")
    
    # 逐个清理子目录
    for item in local_storage_path.iterdir():
        if item.is_dir():
            print(f"   🗑️  正在清理目录: {item.name}")
            shutil.rmtree(item)
            print(f"      ✅ 已删除: {item}")
        elif item.is_file():
            print(f"   🗑️  正在清理文件: {item.name}")
            item.unlink()
            print(f"      ✅ 已删除: {item}")
    
    print("   ✅ 本地存储清理完成")

def reset_rooms_database():
    """重置房间数据库"""
    print("\n🏠 正在重置房间数据库...")
    
    db_path = "rooms.db"
    if Path(db_path).exists():
        # 删除现有数据库
        Path(db_path).unlink()
        print(f"   ✅ 已删除旧数据库: {db_path}")
    
    # 重新创建数据库
    if Path("schema.sql").exists():
        print("   🔧 正在重新创建数据库结构...")
        db = sqlite3.connect(db_path)
        with open("schema.sql", "r") as f:
            db.executescript(f.read())
        db.commit()
        db.close()
        print("   ✅ 数据库结构重新创建完成")
    else:
        print("   ⚠️  警告: schema.sql 文件不存在，无法重新创建数据库")

def clean_rooms_data_database():
    """清理房间数据数据库"""
    print("\n📊 正在清理房间数据数据库...")
    
    db_path = "sd-multiplayer-data/rooms_data.db"
    if Path(db_path).exists():
        print(f"   📊 数据库大小: {Path(db_path).stat().st_size / (1024*1024):.1f} MB")
        
        try:
            # 连接数据库并清理数据
            db = sqlite3.connect(db_path)
            cursor = db.cursor()
            
            # 获取表名
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            # 清理每个表的数据
            for table in tables:
                table_name = table[0]
                if table_name != 'sqlite_sequence':  # 跳过系统表
                    cursor.execute(f"DELETE FROM {table_name}")
                    print(f"      ✅ 已清理表: {table_name}")
            
            # 重置自增ID
            cursor.execute("DELETE FROM sqlite_sequence")
            
            db.commit()
            db.close()
            print("   ✅ 房间数据数据库清理完成")
            
        except Exception as e:
            print(f"   ❌ 清理数据库时出错: {e}")
            # 如果清理失败，直接删除数据库文件
            Path(db_path).unlink()
            print("   ✅ 已删除损坏的数据库文件")
    else:
        print("   ℹ️  房间数据数据库不存在，跳过")

def clean_json_files():
    """清理JSON配置文件"""
    print("\n📄 正在清理JSON配置文件...")
    
    json_dir = Path("sd-multiplayer-data")
    if not json_dir.exists():
        print("   ℹ️  sd-multiplayer-data 目录不存在，跳过")
        return
    
    # 查找所有房间JSON文件
    json_files = list(json_dir.glob("room-*.json"))
    
    if not json_files:
        print("   ℹ️  没有找到房间JSON文件")
        return
    
    print(f"   📊 发现 {len(json_files)} 个JSON文件")
    
    # 计算总大小
    total_size = sum(f.stat().st_size for f in json_files)
    print(f"   📊 总大小: {total_size / (1024*1024):.1f} MB")
    
    # 删除JSON文件
    for json_file in json_files:
        json_file.unlink()
        print(f"   ✅ 已删除: {json_file.name}")
    
    print("   ✅ JSON文件清理完成")

def recreate_storage_structure():
    """重新创建基本的存储目录结构"""
    print("\n📁 正在重新创建存储目录结构...")
    
    directories = [
        "local_storage",
        "local_storage/timelapse",
        "local_storage/uploads"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ 已创建目录: {directory}")

def main():
    """主清理函数"""
    print("🧹 开始清理所有生成图片的本地存储及相关记录")
    print("=" * 60)
    
    # 询问用户确认
    response = input("\n⚠️  此操作将删除所有生成的图片和相关数据，是否继续？ (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("❌ 操作已取消")
        return
    
    # 询问是否备份数据库
    backup_response = input("\n💾 是否备份数据库文件？ (Y/n): ")
    backup_dir = None
    if backup_response.lower() not in ['n', 'no']:
        backup_dir = backup_databases()
    
    try:
        # 执行清理操作
        clean_local_storage()
        reset_rooms_database() 
        clean_rooms_data_database()
        clean_json_files()
        recreate_storage_structure()
        
        print("\n" + "=" * 60)
        print("🎉 清理完成！")
        print("\n📊 清理总结:")
        print("   ✅ 本地存储文件 - 已清理")
        print("   ✅ 房间数据库 - 已重置")
        print("   ✅ 房间数据数据库 - 已清理")
        print("   ✅ JSON配置文件 - 已清理")
        print("   ✅ 目录结构 - 已重建")
        
        if backup_dir:
            print(f"   💾 数据库备份位置: {backup_dir}")
        
        print("\n🚀 现在可以重新启动服务器，开始全新的创作！")
        
    except Exception as e:
        print(f"\n❌ 清理过程中出现错误: {e}")
        if backup_dir:
            print(f"💾 可以从备份恢复: {backup_dir}")

if __name__ == "__main__":
    main() 