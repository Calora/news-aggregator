"""Daily pipeline: fetch all sources → AI processing → generate report."""
from datetime import datetime
from ..time_utils import beijing_today
from ..database import SessionLocal
from ..models import Article


def run_daily_pipeline():
    """Run the full daily pipeline: fetch → classify → report."""
    db = SessionLocal()
    try:
        from .email_fetcher import fetch_all_emails
        from .web_fetcher import fetch_all_web
        from .classifier import process_unclassified

        email_new = fetch_all_emails(db)
        web_new = fetch_all_web(db)

        unclassified = db.query(Article).filter(
            Article.domains == [],
            Article.relevance_score == 0,
        ).count()

        processed = process_unclassified(db)

        # Generate daily report
        if email_new + web_new + processed > 0:
            from ..routers.daily_report import do_generate_report
            do_generate_report(db, beijing_today())

        print(f"[{datetime.now()}] Pipeline done: email={email_new}, web={web_new}, "
              f"processed={processed}")

    except Exception as e:
        print(f"[{datetime.now()}] Pipeline error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
