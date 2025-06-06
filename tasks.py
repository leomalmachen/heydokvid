import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from database import get_db
from services.meeting_service import MeetingService
from utils.logger import get_logger
from config import get_settings

logger = get_logger(__name__)
settings = get_settings()

class BackgroundTasks:
    """Background task manager for HeyDok"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
    
    async def start(self):
        """Start background task scheduler"""
        if self.is_running:
            logger.warning("Background tasks already running")
            return
        
        logger.info("Starting background tasks...")
        
        # Schedule cleanup tasks
        self.scheduler.add_job(
            self.cleanup_expired_meetings,
            trigger=IntervalTrigger(minutes=settings.cleanup_interval_minutes),
            id="cleanup_meetings",
            name="Cleanup Expired Meetings",
            replace_existing=True
        )
        
        # Schedule daily maintenance
        self.scheduler.add_job(
            self.daily_maintenance,
            trigger=CronTrigger(hour=2, minute=0),  # 2 AM daily
            id="daily_maintenance",
            name="Daily Maintenance",
            replace_existing=True
        )
        
        # Schedule health monitoring
        self.scheduler.add_job(
            self.health_check,
            trigger=IntervalTrigger(minutes=5),
            id="health_check",
            name="Health Check",
            replace_existing=True
        )
        
        # Start scheduler
        self.scheduler.start()
        self.is_running = True
        
        logger.info("Background tasks started successfully")
    
    async def stop(self):
        """Stop background task scheduler"""
        if not self.is_running:
            return
        
        logger.info("Stopping background tasks...")
        self.scheduler.shutdown(wait=True)
        self.is_running = False
        logger.info("Background tasks stopped")
    
    async def cleanup_expired_meetings(self):
        """Clean up expired meetings and related data"""
        try:
            logger.debug("Starting expired meetings cleanup...")
            
            db = next(get_db())
            meeting_service = MeetingService(db)
            
            cleaned_count = meeting_service.cleanup_expired_meetings()
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired meetings")
            else:
                logger.debug("No expired meetings to clean up")
                
        except Exception as e:
            logger.error(f"Error in cleanup_expired_meetings: {str(e)}", exc_info=True)
        finally:
            if 'db' in locals():
                db.close()
    
    async def daily_maintenance(self):
        """Perform daily maintenance tasks"""
        try:
            logger.info("Starting daily maintenance...")
            
            # Cleanup expired meetings (redundant but safe)
            await self.cleanup_expired_meetings()
            
            # Log statistics
            await self.log_daily_stats()
            
            # Clean up old log files (if applicable)
            await self.cleanup_old_logs()
            
            logger.info("Daily maintenance completed")
            
        except Exception as e:
            logger.error(f"Error in daily_maintenance: {str(e)}", exc_info=True)
    
    async def log_daily_stats(self):
        """Log daily statistics"""
        try:
            db = next(get_db())
            meeting_service = MeetingService(db)
            
            active_meetings = meeting_service.get_active_meetings()
            total_meetings = len(active_meetings)
            
            # Get meetings from last 24 hours
            yesterday = datetime.utcnow() - timedelta(days=1)
            recent_meetings = [
                m for m in active_meetings 
                if m.created_at >= yesterday
            ]
            
            logger.info(
                "Daily statistics",
                extra={
                    "total_active_meetings": total_meetings,
                    "meetings_last_24h": len(recent_meetings),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error logging daily stats: {str(e)}")
        finally:
            if 'db' in locals():
                db.close()
    
    async def cleanup_old_logs(self):
        """Clean up old log files (if using file logging)"""
        try:
            # This would be implemented if using file-based logging
            # For now, just log that we checked
            logger.debug("Log cleanup check completed")
            
        except Exception as e:
            logger.error(f"Error in log cleanup: {str(e)}")
    
    async def health_check(self):
        """Perform periodic health checks"""
        try:
            # Check database connectivity
            db = next(get_db())
            db.execute("SELECT 1")
            
            # Check LiveKit credentials (light check)
            from livekit_client import LiveKitClient
            livekit = LiveKitClient()
            is_valid = livekit.validate_credentials()
            
            if not is_valid:
                logger.warning("LiveKit credentials validation failed during health check")
            
            logger.debug("Health check completed successfully")
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}", exc_info=True)
        finally:
            if 'db' in locals():
                db.close()

# Global task manager instance
task_manager = BackgroundTasks()

async def start_background_tasks():
    """Start background tasks (call from main app)"""
    await task_manager.start()

async def stop_background_tasks():
    """Stop background tasks (call from main app)"""
    await task_manager.stop()

# Function to manually trigger cleanup (for testing/admin)
async def manual_cleanup():
    """Manually trigger cleanup tasks"""
    logger.info("Manual cleanup triggered")
    await task_manager.cleanup_expired_meetings()
    return {"status": "cleanup completed"}

# Function to get task status
def get_task_status():
    """Get current status of background tasks"""
    return {
        "is_running": task_manager.is_running,
        "scheduled_jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None
            }
            for job in task_manager.scheduler.get_jobs()
        ] if task_manager.is_running else []
    } 