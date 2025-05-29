"""
Webhooks API endpoints for LiveKit events
"""

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import hmac
import hashlib

from app.core.database import get_db
from app.core.config import settings
from app.core.logging import get_logger
from app.models.room import Room, RoomStatus
from app.models.participant import Participant, ParticipantStatus
from app.models.recording import Recording, RecordingStatus
from app.core.redis import redis_client

router = APIRouter()
logger = get_logger(__name__)


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    """
    Verify LiveKit webhook signature
    """
    expected_signature = hmac.new(
        settings.LIVEKIT_API_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)


@router.post("/livekit")
async def livekit_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(None)
):
    """
    Handle LiveKit webhook events
    """
    # Get raw body
    body = await request.body()
    
    # Verify signature if provided
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        if not verify_webhook_signature(body, token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )
    
    # Parse event
    try:
        event = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON"
        )
    
    event_type = event.get("event")
    logger.info("LiveKit webhook received", event_type=event_type, event=event)
    
    # Handle different event types
    if event_type == "room_started":
        await handle_room_started(db, event)
    elif event_type == "room_finished":
        await handle_room_finished(db, event)
    elif event_type == "participant_joined":
        await handle_participant_joined(db, event)
    elif event_type == "participant_left":
        await handle_participant_left(db, event)
    elif event_type == "recording_started":
        await handle_recording_started(db, event)
    elif event_type == "recording_ended":
        await handle_recording_ended(db, event)
    elif event_type == "track_published":
        await handle_track_published(db, event)
    elif event_type == "track_unpublished":
        await handle_track_unpublished(db, event)
    
    return {"status": "ok"}


async def handle_room_started(db: AsyncSession, event: dict):
    """
    Handle room started event
    """
    room_name = event.get("room", {}).get("name")
    if not room_name:
        return
    
    # Update room status
    room = await db.scalar(
        select(Room).where(Room.room_id == room_name)
    )
    if room:
        room.start()
        await db.commit()
        logger.info("Room started", room_id=room_name)


async def handle_room_finished(db: AsyncSession, event: dict):
    """
    Handle room finished event
    """
    room_name = event.get("room", {}).get("name")
    if not room_name:
        return
    
    # Update room status
    room = await db.scalar(
        select(Room).where(Room.room_id == room_name)
    )
    if room:
        room.end()
        await db.commit()
        logger.info("Room finished", room_id=room_name)
        
        # Clear Redis cache
        await redis_client.delete(f"room:{room_name}:participants")


async def handle_participant_joined(db: AsyncSession, event: dict):
    """
    Handle participant joined event
    """
    room_name = event.get("room", {}).get("name")
    participant_info = event.get("participant", {})
    identity = participant_info.get("identity")
    
    if not room_name or not identity:
        return
    
    # Get room
    room = await db.scalar(
        select(Room).where(Room.room_id == room_name)
    )
    if not room:
        return
    
    # Update participant status
    participant = await db.scalar(
        select(Participant).where(
            and_(
                Participant.room_id == room.id,
                Participant.participant_id == identity
            )
        )
    )
    
    if participant:
        participant.join()
        await db.commit()
        
        # Update Redis cache
        await redis_client.add_room_participant(
            room_name,
            identity,
            {
                "user_id": str(participant.user_id),
                "joined_at": datetime.utcnow().isoformat(),
                "metadata": participant_info.get("metadata", {})
            }
        )
        
        logger.info(
            "Participant joined",
            room_id=room_name,
            participant_id=identity
        )


async def handle_participant_left(db: AsyncSession, event: dict):
    """
    Handle participant left event
    """
    room_name = event.get("room", {}).get("name")
    participant_info = event.get("participant", {})
    identity = participant_info.get("identity")
    
    if not room_name or not identity:
        return
    
    # Get room
    room = await db.scalar(
        select(Room).where(Room.room_id == room_name)
    )
    if not room:
        return
    
    # Update participant status
    participant = await db.scalar(
        select(Participant).where(
            and_(
                Participant.room_id == room.id,
                Participant.participant_id == identity
            )
        )
    )
    
    if participant:
        participant.leave()
        await db.commit()
        
        # Update Redis cache
        await redis_client.remove_room_participant(room_name, identity)
        
        logger.info(
            "Participant left",
            room_id=room_name,
            participant_id=identity
        )


async def handle_recording_started(db: AsyncSession, event: dict):
    """
    Handle recording started event
    """
    room_name = event.get("room", {}).get("name")
    egress_info = event.get("egressInfo", {})
    egress_id = egress_info.get("egressId")
    
    if not room_name or not egress_id:
        return
    
    # Get room
    room = await db.scalar(
        select(Room).where(Room.room_id == room_name)
    )
    if not room:
        return
    
    # Update recording status
    recording = await db.scalar(
        select(Recording).where(Recording.recording_id == egress_id)
    )
    
    if recording:
        recording.start()
        await db.commit()
        logger.info(
            "Recording started",
            room_id=room_name,
            recording_id=egress_id
        )


async def handle_recording_ended(db: AsyncSession, event: dict):
    """
    Handle recording ended event
    """
    room_name = event.get("room", {}).get("name")
    egress_info = event.get("egressInfo", {})
    egress_id = egress_info.get("egressId")
    file_info = egress_info.get("file", {})
    
    if not room_name or not egress_id:
        return
    
    # Get room
    room = await db.scalar(
        select(Room).where(Room.room_id == room_name)
    )
    if not room:
        return
    
    # Update recording status
    recording = await db.scalar(
        select(Recording).where(Recording.recording_id == egress_id)
    )
    
    if recording:
        if egress_info.get("status") == "EGRESS_COMPLETE":
            # Recording completed successfully
            file_path = file_info.get("filename", "")
            file_size = file_info.get("size", 0)
            
            # In production, encrypt the file path
            from app.core.security import encrypt_sensitive_data, generate_secure_token
            encrypted_path = encrypt_sensitive_data(file_path)
            encryption_key_id = generate_secure_token(16)
            
            recording.complete(encrypted_path, file_size, encryption_key_id)
        else:
            # Recording failed
            error = egress_info.get("error", "Unknown error")
            recording.fail(error)
        
        await db.commit()
        logger.info(
            "Recording ended",
            room_id=room_name,
            recording_id=egress_id,
            status=egress_info.get("status")
        )


async def handle_track_published(db: AsyncSession, event: dict):
    """
    Handle track published event
    """
    room_name = event.get("room", {}).get("name")
    participant_info = event.get("participant", {})
    track_info = event.get("track", {})
    
    logger.info(
        "Track published",
        room_id=room_name,
        participant_id=participant_info.get("identity"),
        track_type=track_info.get("type"),
        track_source=track_info.get("source")
    )


async def handle_track_unpublished(db: AsyncSession, event: dict):
    """
    Handle track unpublished event
    """
    room_name = event.get("room", {}).get("name")
    participant_info = event.get("participant", {})
    track_info = event.get("track", {})
    
    logger.info(
        "Track unpublished",
        room_id=room_name,
        participant_id=participant_info.get("identity"),
        track_type=track_info.get("type"),
        track_source=track_info.get("source")
    ) 