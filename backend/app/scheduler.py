"""APScheduler-based periodic task runner."""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from .time_utils import beijing_now_naive, beijing_today, to_beijing_naive


scheduler = BackgroundScheduler()


def start_scheduler():
    from .config import settings
    from .services.pipeline import run_daily_pipeline

    interval_hours = settings.update_interval_hours

    # Fetch + AI processing every N hours
    scheduler.add_job(
        run_daily_pipeline,
        IntervalTrigger(hours=interval_hours),
        id="news_fetch",
        replace_existing=True,
    )

    # Daily report generation at 8:00 AM Beijing time
    scheduler.add_job(
        _generate_report_job,
        CronTrigger(hour=8, minute=0, timezone="Asia/Shanghai"),
        id="daily_report_8am",
        replace_existing=True,
    )

    # Health check every 6 hours
    scheduler.add_job(
        _health_check_job,
        IntervalTrigger(hours=6),
        id="health_check",
        replace_existing=True,
    )

    # Run once on startup
    scheduler.add_job(
        run_daily_pipeline,
        id="news_fetch_startup",
        replace_existing=True,
    )

    scheduler.start()


def _generate_report_job():
    from .database import SessionLocal
    db = SessionLocal()
    try:
        from .routers.daily_report import do_generate_report
        do_generate_report(db, beijing_today())
    finally:
        db.close()


def _health_check_job():
    """Self-monitoring: detect stale data, unprocessed articles, and auto-fix."""
    from .database import SessionLocal
    from .models import Article
    from datetime import timedelta
    import logging

    logger = logging.getLogger("health_check")
    now = beijing_now_naive()

    db = SessionLocal()
    try:
        issues = []

        # 1. Check if latest article is > 24h old
        latest = db.query(Article).order_by(Article.fetched_at.desc()).first()
        if latest:
            latest_fetched_at = to_beijing_naive(latest.fetched_at)
            age_h = (now - latest_fetched_at).total_seconds() / 3600
            if age_h > 24:
                issues.append(f"数据断流{age_h:.0f}小时，最新抓取: {latest_fetched_at.strftime('%m-%d %H:%M')}")
        else:
            issues.append("数据库无文章")

        # 2. Check unprocessed articles
        unprocessed = db.query(Article).filter(Article.relevance_score == 0).count()
        if unprocessed > 20:
            issues.append(f"未处理文章积压: {unprocessed}篇")
            from .services.classifier import process_unclassified
            for _ in range(10):
                n = process_unclassified(db)
                if n == 0:
                    break
            remaining = db.query(Article).filter(Article.relevance_score == 0).count()
            if remaining < unprocessed:
                logger.info(f"健康检查自动处理: {unprocessed - remaining}篇, 剩余{remaining}")

        # 3. Check if reports exist for last 2 days
        from .models import DailyReport
        yesterday = (now - timedelta(days=1)).date()
        today_report = db.query(DailyReport).filter(DailyReport.date == now.date()).first()
        yesterday_report = db.query(DailyReport).filter(DailyReport.date == yesterday).first()
        if not today_report and not yesterday_report:
            issues.append("最近2天无日报")

        # 4. Check email sources (Gmail OAuth token expiry)
        from .models import EmailAccount
        email_accounts = db.query(EmailAccount).filter(EmailAccount.enabled == True).all()
        for acc in email_accounts:
            if acc.last_fetch_at:
                last_fetch_at = to_beijing_naive(acc.last_fetch_at)
                email_age_h = (now - last_fetch_at).total_seconds() / 3600
                if email_age_h > 48:
                    issues.append(f"邮箱源 {acc.email} 超过{email_age_h:.0f}小时未拉取")
            if "gmail" in acc.email.lower():
                try:
                    from .services.gmail_fetcher import test_gmail_connection
                    ok, msg = test_gmail_connection(acc.email)
                    if not ok:
                        issues.append(f"Gmail API 失效: {msg[:80]}")
                except Exception as e:
                    issues.append(f"Gmail API 检测异常: {e}")

        if issues:
            logger.warning(f"健康检查发现问题({len(issues)}项): {'; '.join(issues)}")
        else:
            latest_label = to_beijing_naive(latest.fetched_at).strftime('%m-%d %H:%M') if latest else 'N/A'
            logger.info(f"健康检查通过 | 最新文章: {latest_label} | 积压: {unprocessed} | 邮件: 正常")

    except Exception as e:
        logger.error(f"健康检查异常: {e}")
    finally:
        db.close()


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
