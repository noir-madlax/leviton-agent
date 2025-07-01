"""Amazon Category Fetcher - Command Line Interface"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

# 添加当前目录到Python路径，确保能导入本地模块
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 直接导入本地模块
from models import FetchConfig
from category_config import CategoryFetcherConfig
from orchestrator import CategoryFetchOrchestrator


def setup_logging(log_level: str = "INFO"):
    """设置日志配置"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=CategoryFetcherConfig.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("category_fetcher.log")
        ]
    )


async def start_new_fetch(args):
    """启动新的获取"""
    print("🚀 Starting new Amazon category fetch...")
    
    # 创建配置
    config = FetchConfig(
        amazon_domain=args.domain,
        api_delay_seconds=args.delay,
        max_retries=args.retries,
        max_depth=args.depth,
        skip_existing=args.skip_existing,
        target_category=args.category
    )
    
    # 显示配置
    print(f"📋 Configuration:")
    print(f"   Domain: {config.amazon_domain}")
    print(f"   API Delay: {config.api_delay_seconds}s")
    print(f"   Max Retries: {config.max_retries}")
    print(f"   Max Depth: {config.max_depth}")
    print(f"   Skip Existing: {config.skip_existing}")
    if config.target_category:
        print(f"   Target Category: {config.target_category}")
    print()
    
    try:
        orchestrator = CategoryFetchOrchestrator()
        result = await orchestrator.start_new_fetch(config)
        
        if result["success"]:
            print("✅ Fetch started successfully!")
            print(f"📁 Run ID: {result['run_id']}")
            print(f"📊 Progress file: {result['progress_file']}")
            print(f"🌐 Domain: {result['domain']}")
            
            if "total_categories" in result:
                print(f"📈 Total categories found: {result['total_categories']}")
            if "api_calls" in result:
                print(f"🔗 API calls made: {result['api_calls']}")
        else:
            print(f"❌ Fetch failed: {result['error']}")
            return 1
            
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        return 1
    
    return 0


async def resume_fetch(args):
    """恢复获取"""
    print("🔄 Resuming Amazon category fetch...")
    
    try:
        orchestrator = CategoryFetchOrchestrator()
        result = await orchestrator.resume_fetch(args.run_id)
        
        if result["success"]:
            print("✅ Fetch resumed successfully!")
            print(f"📁 Run ID: {result['run_id']}")
            print(f"📊 Progress file: {result['progress_file']}")
            print(f"🌐 Domain: {result['domain']}")
            
            if "total_categories" in result:
                print(f"📈 Total categories: {result['total_categories']}")
            if "api_calls" in result:
                print(f"🔗 API calls made: {result['api_calls']}")
        else:
            print(f"❌ Resume failed: {result['error']}")
            return 1
            
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        return 1
    
    return 0


async def show_status(args):
    """显示状态"""
    try:
        orchestrator = CategoryFetchOrchestrator()
        result = await orchestrator.get_run_status(args.run_id)
        
        if result["success"]:
            print(f"📊 Status for run: {result['run_id']}")
            print(f"📁 Run directory: {result['run_directory']}")
            print(f"📋 Progress file: {result['progress_file']}")
            print()
            
            if result.get("config"):
                config = result["config"]
                print("⚙️  Configuration:")
                print(f"   Domain: {config.get('amazon_domain')}")
                print(f"   Target Category: {config.get('target_category', 'All')}")
                print(f"   Max Depth: {config.get('max_depth')}")
                print()
            
            print("📈 Progress:")
            print(result["progress_content"])
        else:
            print(f"❌ Could not get status: {result['error']}")
            return 1
            
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        return 1
    
    return 0


async def list_runs(args):
    """列出所有运行"""
    try:
        orchestrator = CategoryFetchOrchestrator()
        result = await orchestrator.list_runs()
        
        if result["success"]:
            runs = result["runs"]
            if not runs:
                print("📭 No runs found.")
                return 0
            
            print(f"📋 Found {len(runs)} runs:")
            print()
            
            # 表头
            print(f"{'RUN ID':<25} {'STATUS':<12} {'DOMAIN':<15} {'CATEGORY':<20} {'PROGRESS':<15} {'STARTED':<20}")
            print("-" * 107)
            
            for run in runs:
                run_id = run["run_id"][:24]
                status = run.get("status", "unknown")[:11]
                domain = run["domain"][:14]
                category = (run.get("target_category") or "All")[:19]
                
                if "processed_categories" in run and "total_categories" in run:
                    progress = f"{run['processed_categories']}/{run['total_categories']}"
                else:
                    progress = "unknown"
                progress = progress[:14]
                
                started = run.get("started_at", run.get("created_at", ""))[:19]
                
                print(f"{run_id:<25} {status:<12} {domain:<15} {category:<20} {progress:<15} {started:<20}")
                
        else:
            print(f"❌ Could not list runs: {result['error']}")
            return 1
            
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        return 1
    
    return 0


async def show_statistics(args):
    """显示统计信息"""
    try:
        orchestrator = CategoryFetchOrchestrator()
        result = await orchestrator.get_category_statistics()
        
        if result["success"]:
            stats = result["statistics"]
            print("📊 Category Statistics:")
            print(f"   Total Categories: {stats.get('total_categories', 0)}")
            print(f"   Root Categories: {stats.get('root_categories', 0)}")
            print(f"   Max Level: {stats.get('max_level', 0)}")
            
            level_stats = stats.get('categories_by_level', {})
            if level_stats:
                print("\n📈 Categories by Level:")
                for level in sorted(level_stats.keys()):
                    print(f"   Level {level}: {level_stats[level]} categories")
        else:
            print(f"❌ Could not get statistics: {result['error']}")
            return 1
            
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        return 1
    
    return 0


async def test_connection(args):
    """测试API连接"""
    print("🔗 Testing Rainforest API connection...")
    
    try:
        orchestrator = CategoryFetchOrchestrator()
        result = await orchestrator.test_api_connection()
        
        if result["success"]:
            print("✅ API connection successful!")
        else:
            print(f"❌ API connection failed: {result.get('error', 'Unknown error')}")
            return 1
            
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        return 1
    
    return 0


def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="Amazon Category Fetcher - 获取亚马逊所有类别数据",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 开始新的获取（所有类别）
  python main.py start

  # 获取特定类别
  python main.py start --category "Books"

  # 设置API延迟和最大深度
  python main.py start --delay 2.0 --depth 5

  # 恢复上次的获取
  python main.py resume

  # 恢复特定运行
  python main.py resume --run-id run_com_20241201_143022

  # 查看状态
  python main.py status

  # 列出所有运行
  python main.py list

  # 查看统计信息
  python main.py stats

  # 测试API连接
  python main.py test
        """
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日志级别"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # start 命令
    start_parser = subparsers.add_parser("start", help="开始新的类别获取")
    start_parser.add_argument(
        "--domain",
        default="amazon.com",
        choices=CategoryFetcherConfig.get_supported_domains(),
        help="亚马逊域名"
    )
    start_parser.add_argument(
        "--category",
        help="指定获取的顶级类别名称（可选）"
    )
    start_parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="API调用间隔时间（秒）"
    )
    start_parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="最大重试次数"
    )
    start_parser.add_argument(
        "--depth",
        type=int,
        default=10,
        help="最大深度限制"
    )
    start_parser.add_argument(
        "--no-skip-existing",
        dest="skip_existing",
        action="store_false",
        help="不跳过已存在的类别"
    )
    
    # resume 命令
    resume_parser = subparsers.add_parser("resume", help="恢复中断的获取")
    resume_parser.add_argument(
        "--run-id",
        help="要恢复的运行ID（可选，默认恢复最近的）"
    )
    
    # status 命令
    status_parser = subparsers.add_parser("status", help="查看运行状态")
    status_parser.add_argument(
        "--run-id",
        help="要查看的运行ID（可选，默认查看最近的）"
    )
    
    # list 命令
    subparsers.add_parser("list", help="列出所有运行")
    
    # stats 命令
    subparsers.add_parser("stats", help="查看类别统计信息")
    
    # test 命令
    subparsers.add_parser("test", help="测试API连接")
    
    return parser


async def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.log_level)
    
    if not args.command:
        parser.print_help()
        return 1
    
    # 确保环境变量
    if not CategoryFetcherConfig.validate_api_key():
        print("❌ Error: RAINFOREST_API_KEY environment variable is not set.")
        print("Please set your Rainforest API key:")
        print("export RAINFOREST_API_KEY=your_api_key_here")
        return 1
    
    # 执行命令
    commands = {
        "start": start_new_fetch,
        "resume": resume_fetch,
        "status": show_status,
        "list": list_runs,
        "stats": show_statistics,
        "test": test_connection
    }
    
    command_func = commands.get(args.command)
    if not command_func:
        print(f"❌ Unknown command: {args.command}")
        return 1
    
    try:
        return await command_func(args)
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user.")
        return 1
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        logging.exception("Unexpected error in main")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 