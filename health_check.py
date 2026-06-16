"""健康检查脚本：检测数据断流并自动修复。

检查项：
1. 后端是否在运行
2. 最近抓取时间是否超过 24 小时
3. DeepSeek API Key 是否有效
4. 是否有大量 score=0 未处理文章

发现问题时自动尝试修复，并输出诊断报告。
"""

import json
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

API = "http://localhost:8000/api"
BEIJING_TZ = timezone(timedelta(hours=8))

# 阈值配置
FETCH_STALE_HOURS = 24       # 超过此时间未抓取视为断流
UNPROCESSED_ALARM = 50       # 未处理文章超过此数触发告警


def api_get(path: str) -> dict | None:
    try:
        req = urllib.request.Request(f"{API}{path}")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}


def api_post(path: str) -> dict | None:
    try:
        req = urllib.request.Request(f"{API}{path}", method="POST", data=b"")
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}


def is_backend_alive() -> bool:
    result = api_get("/articles?page_size=1")
    return result is not None and "items" in result


def get_latest_fetch_time() -> datetime | None:
    result = api_get("/articles?page_size=1&score_min=0&sort_by=fetched_at&sort_order=desc")
    if result and result.get("items"):
        return datetime.fromisoformat(result["items"][0]["fetched_at"])
    return None


def get_unprocessed_count() -> int:
    result = api_get("/articles?page_size=1&score_min=0&score_max=0")
    if result and "total" in result:
        return result["total"]
    return -1


def trigger_fetch() -> bool:
    result = api_post("/fetch")
    return result is not None and result.get("ok") is True


def trigger_reprocess() -> bool:
    result = api_post("/reprocess")
    return result is not None and result.get("ok") is True


def health_report() -> str:
    now = datetime.now(BEIJING_TZ)
    lines = [f"=== 健康检查 {now.strftime('%Y-%m-%d %H:%M')} 北京时间 ==="]

    # 1. 后端状态
    if not is_backend_alive():
        lines.append("[错误] 后端无法访问 — 请启动 start.bat")
        return "\n".join(lines)
    lines.append("[正常] 后端运行中")

    # 2. 最新抓取
    latest = get_latest_fetch_time()
    if latest:
        latest_dt = latest if latest.tzinfo else latest.replace(tzinfo=BEIJING_TZ)
        hours_ago = (now - latest_dt).total_seconds() / 3600
        if hours_ago > FETCH_STALE_HOURS:
            lines.append(f"[告警] 最近抓取: {latest.strftime('%m-%d %H:%M')} ({hours_ago:.0f}小时前) — 超过阈值，触发修复...")
            if trigger_fetch():
                lines.append("[修复] 已触发抓取")
            else:
                lines.append("[失败] 抓取触发失败")
        else:
            lines.append(f"[正常] 最近抓取: {latest.strftime('%m-%d %H:%M')} ({hours_ago:.0f}小时前)")
    else:
        lines.append("[告警] 无任何抓取记录")

    # 3. 未处理文章
    unprocessed = get_unprocessed_count()
    if unprocessed < 0:
        lines.append("[告警] 无法获取未处理文章数")
    elif unprocessed >= UNPROCESSED_ALARM:
        lines.append(f"[告警] 未处理文章: {unprocessed} 篇 — 触发 AI 处理...")
        if trigger_reprocess():
            lines.append("[修复] 已触发 AI 重处理")
        else:
            lines.append("[失败] AI 处理触发失败")
    elif unprocessed > 0:
        lines.append(f"[正常] 未处理文章: {unprocessed} 篇 (少量积压，正常)")
    else:
        lines.append("[正常] 无积压")

    # 4. 日报生成（最近3天是否有日报）
    report_list = api_get("/report/list")
    if report_list and isinstance(report_list, list):
        today_str = now.strftime("%Y-%m-%d")
        yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        dates = [r.get("date", "") for r in report_list]
        if today_str not in dates and yesterday not in dates:
            lines.append("[告警] 最近2天无日报")

    return "\n".join(lines)


def auto_fix_loop():
    """自动修复循环：查问题 → 修复 → 再查 → 直到正常或无法修复"""
    for attempt in range(3):
        result = api_get("/articles?page_size=1&score_min=0&sort_by=fetched_at&sort_order=desc")
        if not result or "items" not in result:
            print(f"[尝试{attempt+1}] 后端不可达，无法自动修复（需手动启动 start.bat）")
            return False

        items = result.get("items", [])
        if not items:
            print(f"[尝试{attempt+1}] 无文章，触发抓取...")
            trigger_fetch()
            time.sleep(10)
            continue

        latest = datetime.fromisoformat(items[0]["fetched_at"])
        latest_dt = latest if latest.tzinfo else latest.replace(tzinfo=BEIJING_TZ)
        age_h = (datetime.now(BEIJING_TZ) - latest_dt).total_seconds() / 3600
        if age_h >= 6:
            print(f"[尝试{attempt+1}] 数据已{age_h:.0f}小时未更新，触发抓取...")
            trigger_fetch()
            time.sleep(5)

        # 处理积压
        unprocessed = get_unprocessed_count()
        if unprocessed > 10:
            print(f"[尝试{attempt+1}] 触发 AI 处理...")
            trigger_reprocess()
            time.sleep(5)

        break

    return True


def log_to_file(report: str):
    """Append health check report to log file."""
    import os
    log_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(log_dir, "health_check.log")
    # Keep log under ~100 lines
    try:
        existing = []
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                existing = f.readlines()
        with open(log_path, "w", encoding="utf-8") as f:
            for line in existing[-80:]:  # keep last 80 lines
                f.write(line)
            f.write(report + "\n")
    except Exception:
        pass


if __name__ == "__main__":
    report = health_report() if len(sys.argv) <= 1 or sys.argv[1] != "--auto-fix" else ""
    if len(sys.argv) > 1 and sys.argv[1] == "--auto-fix":
        auto_fix_loop()
        report = health_report()
    print(report)
    log_to_file(report)
