"""
Recordings API endpoints
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.database import get_db
from app.core.livekit import get_livekit_client, LiveKitClient
from app.core.security import generate_secure_token
from app.core.audit import create_audit_entry
from app.models.room import Room
from app.models.recording import Recording, RecordingStatus
from app.models.user import User
from app.models.audit import AuditAction
from app.schemas.recording import (
    RecordingResponse,
    RecordingListResponse,
    StartRecordingRequest,
    RecordingConsentRequest
)
from app.api.deps import get_current_user
from app.core.config import settings

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/start", response_model=RecordingResponse)
@limiter.limit("5/minute")
async def start_recording(
    request: StartRecordingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    livekit: LiveKitClient = Depends(get_livekit_client)
) -> Recording:
    """
    Start recording a room
    """
    # Check permissions
    if not current_user.can_record:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to start recordings"
        )
    
    # Get room
    room = await db.get(Room, request.room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # Check if room allows recording
    if not room.enable_recording:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recording is not enabled for this room"
        )
    
    # Check if room is active
    if not room.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room is not active"
        )
    
    # Check if already recording
    existing_recording = await db.scalar(
        select(Recording).where(
            and_(
                Recording.room_id == room.id,
                Recording.status.in_([RecordingStatus.PENDING, RecordingStatus.RECORDING])
            )
        )
    )
    
    if existing_recording:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room is already being recorded"
        )
    
    # Generate recording path
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    recording_path = f"{settings.RECORDING_STORAGE_PATH}/{room.room_id}_{timestamp}.mp4"
    
    # Start recording in LiveKit
    try:
        egress_id = await livekit.start_room_recording(
            room_name=room.room_id,
            output_path=recording_path,
            audio_only=request.audio_only
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start recording: {str(e)}"
        )
    
    # Create recording record
    recording = Recording(
        room_id=room.id,
        recording_id=egress_id,
        started_by=current_user.id,
        status=RecordingStatus.PENDING,
        metadata={
            "audio_only": request.audio_only,
            "requested_by": str(current_user.id)
        }
    )
    
    # Add initial consent if user is starting their own recording
    if request.consent_given:
        recording.add_consent(current_user.id)
    
    db.add(recording)
    
    # Create audit log
    await create_audit_entry(
        db,
        user_id=current_user.id,
        action=AuditAction.START_RECORDING,
        resource_type="recording",
        resource_id=recording.id,
        metadata={"room_id": str(room.id)}
    )
    
    await db.commit()
    await db.refresh(recording)
    
    return recording


@router.post("/{recording_id}/stop")
async def stop_recording(
    recording_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    livekit: LiveKitClient = Depends(get_livekit_client)
) -> dict:
    """
    Stop an active recording
    """
    # Get recording
    recording = await db.get(Recording, recording_id)
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )
    
    # Check permissions
    if recording.started_by != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to stop this recording"
        )
    
    # Check if recording is active
    if not recording.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recording is not active"
        )
    
    # Stop recording in LiveKit
    try:
        await livekit.stop_recording(recording.recording_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop recording: {str(e)}"
        )
    
    # Update status
    recording.stop()
    
    # Create audit log
    await create_audit_entry(
        db,
        user_id=current_user.id,
        action=AuditAction.STOP_RECORDING,
        resource_type="recording",
        resource_id=recording.id
    )
    
    await db.commit()
    
    return {"message": "Recording stopped successfully"}


@router.post("/{recording_id}/consent", response_model=RecordingResponse)
async def add_consent(
    recording_id: UUID,
    consent: RecordingConsentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Recording:
    """
    Add consent for recording
    """
    # Get recording
    recording = await db.get(Recording, recording_id)
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )
    
    # Check if user is participant in the room
    room = await db.get(Room, recording.room_id)
    # TODO: Check participant status
    
    if consent.consent_given:
        recording.add_consent(current_user.id)
    
    await db.commit()
    await db.refresh(recording)
    
    return recording


@router.get("/", response_model=RecordingListResponse)
async def list_recordings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    room_id: Optional[UUID] = None,
    status: Optional[RecordingStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> RecordingListResponse:
    """
    List recordings with pagination
    """
    # Build query
    query = select(Recording).where(Recording.deleted_at.is_(None))
    
    # Filter by room if provided
    if room_id:
        query = query.where(Recording.room_id == room_id)
    
    # Filter by status if provided
    if status:
        query = query.where(Recording.status == status)
    
    # Non-admins can only see recordings they started or have access to
    if not current_user.is_admin:
        # TODO: Add more complex permission logic
        query = query.where(Recording.started_by == current_user.id)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Apply pagination
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(Recording.created_at.desc())
    
    # Execute query
    result = await db.execute(query)
    recordings = result.scalars().all()
    
    return RecordingListResponse(
        recordings=recordings,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{recording_id}", response_model=RecordingResponse)
async def get_recording(
    recording_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Recording:
    """
    Get recording details
    """
    # Get recording
    recording = await db.get(Recording, recording_id)
    if not recording or recording.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )
    
    # Check permissions
    if recording.started_by != current_user.id and not current_user.is_admin:
        # TODO: Check if user has access to the room
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this recording"
        )
    
    # Create audit log
    await create_audit_entry(
        db,
        user_id=current_user.id,
        action=AuditAction.READ,
        resource_type="recording",
        resource_id=recording.id
    )
    
    return recording


@router.delete("/{recording_id}")
async def delete_recording(
    recording_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Delete a recording (soft delete for GDPR)
    """
    # Get recording
    recording = await db.get(Recording, recording_id)
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )
    
    # Check permissions
    if recording.started_by != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this recording"
        )
    
    # Soft delete
    recording.soft_delete()
    
    # Create audit log
    await create_audit_entry(
        db,
        user_id=current_user.id,
        action=AuditAction.DELETE,
        resource_type="recording",
        resource_id=recording.id
    )
    
    await db.commit()
    
    return {"message": "Recording deleted successfully"} 