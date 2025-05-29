"""
Rooms API endpoints
"""

from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.database import get_db
from app.core.livekit import get_livekit_client, LiveKitClient
from app.core.security import generate_secure_token, encrypt_sensitive_data
from app.core.audit import create_audit_entry
from app.models.room import Room, RoomStatus
from app.models.user import User
from app.models.participant import Participant
from app.models.meeting_link import MeetingLink
from app.models.audit import AuditAction
from app.schemas.room import (
    RoomCreate,
    RoomUpdate,
    RoomResponse,
    RoomListResponse,
    RoomTokenRequest,
    RoomTokenResponse,
    CreateMeetingLinkRequest,
    CreateMeetingLinkResponse
)
from app.api.deps import get_current_user
from app.core.config import settings

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/", response_model=RoomResponse)
@limiter.limit("10/minute")
async def create_room(
    room_data: RoomCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    livekit: LiveKitClient = Depends(get_livekit_client)
) -> Room:
    """
    Create a new room
    """
    # Check permissions
    if not current_user.can_create_rooms:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create rooms"
        )
    
    # Generate unique room ID
    room_id = livekit.generate_room_name()
    
    # Create room in LiveKit
    try:
        await livekit.create_room(
            name=room_id,
            empty_timeout=300,
            max_participants=room_data.max_participants,
            metadata={"created_by": str(current_user.id)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create room in LiveKit: {str(e)}"
        )
    
    # Create room in database
    room = Room(
        room_id=room_id,
        name=room_data.name,
        created_by=current_user.id,
        scheduled_start=room_data.scheduled_start,
        scheduled_end=room_data.scheduled_end,
        max_participants=room_data.max_participants,
        enable_recording=room_data.enable_recording,
        enable_chat=room_data.enable_chat,
        enable_screen_share=room_data.enable_screen_share,
        waiting_room_enabled=room_data.waiting_room_enabled,
        metadata=room_data.metadata
    )
    
    db.add(room)
    
    # Create audit log
    await create_audit_entry(
        db,
        user_id=current_user.id,
        action=AuditAction.CREATE,
        resource_type="room",
        resource_id=room.id,
        metadata={"room_id": room_id}
    )
    
    await db.commit()
    await db.refresh(room)
    
    return room


@router.get("/", response_model=RoomListResponse)
async def list_rooms(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[RoomStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> RoomListResponse:
    """
    List rooms with pagination
    """
    # Build query
    query = select(Room)
    
    # Filter by status if provided
    if status:
        query = query.where(Room.status == status)
    
    # Filter by user role
    if not current_user.is_admin:
        # Non-admins can only see rooms they created or are participants in
        subquery = select(Participant.room_id).where(
            Participant.user_id == current_user.id
        )
        query = query.where(
            or_(
                Room.created_by == current_user.id,
                Room.id.in_(subquery)
            )
        )
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Apply pagination
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(Room.created_at.desc())
    
    # Execute query
    result = await db.execute(query)
    rooms = result.scalars().all()
    
    return RoomListResponse(
        rooms=rooms,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Room:
    """
    Get room details
    """
    # Get room
    room = await db.get(Room, room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # Check permissions
    if not current_user.is_admin:
        # Check if user is creator or participant
        participant = await db.scalar(
            select(Participant).where(
                and_(
                    Participant.room_id == room_id,
                    Participant.user_id == current_user.id
                )
            )
        )
        if room.created_by != current_user.id and not participant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this room"
            )
    
    # Create audit log
    await create_audit_entry(
        db,
        user_id=current_user.id,
        action=AuditAction.READ,
        resource_type="room",
        resource_id=room.id
    )
    
    return room


@router.patch("/{room_id}", response_model=RoomResponse)
async def update_room(
    room_id: UUID,
    room_update: RoomUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Room:
    """
    Update room details
    """
    # Get room
    room = await db.get(Room, room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # Check permissions
    if room.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this room"
        )
    
    # Update fields
    update_data = room_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(room, field, value)
    
    # Create audit log
    await create_audit_entry(
        db,
        user_id=current_user.id,
        action=AuditAction.UPDATE,
        resource_type="room",
        resource_id=room.id,
        metadata={"updated_fields": list(update_data.keys())}
    )
    
    await db.commit()
    await db.refresh(room)
    
    return room


@router.delete("/{room_id}")
async def delete_room(
    room_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    livekit: LiveKitClient = Depends(get_livekit_client)
) -> dict:
    """
    Delete a room
    """
    # Get room
    room = await db.get(Room, room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # Check permissions
    if room.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this room"
        )
    
    # Check if room is active
    if room.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete an active room"
        )
    
    # Delete from LiveKit
    try:
        await livekit.delete_room(room.room_id)
    except Exception:
        # Room might already be deleted in LiveKit
        pass
    
    # Create audit log
    await create_audit_entry(
        db,
        user_id=current_user.id,
        action=AuditAction.DELETE,
        resource_type="room",
        resource_id=room.id
    )
    
    # Delete from database
    await db.delete(room)
    await db.commit()
    
    return {"message": "Room deleted successfully"}


@router.post("/{room_id}/token", response_model=RoomTokenResponse)
@limiter.limit("20/minute")
async def create_room_token(
    room_id: UUID,
    token_request: RoomTokenRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    livekit: LiveKitClient = Depends(get_livekit_client)
) -> RoomTokenResponse:
    """
    Create access token for room
    """
    # Get room
    room = await db.get(Room, room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # Check if user is participant
    participant = await db.scalar(
        select(Participant).where(
            and_(
                Participant.room_id == room_id,
                Participant.user_id == current_user.id
            )
        )
    )
    
    if not participant and room.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this room"
        )
    
    # Create or update participant
    if not participant:
        participant = Participant(
            room_id=room_id,
            user_id=current_user.id,
            participant_id=str(current_user.id),
            role=current_user.role,
            can_publish=True,
            can_subscribe=True
        )
        db.add(participant)
        await db.commit()
    
    # Generate LiveKit token
    user_name = token_request.user_name or current_user.email
    token = livekit.create_participant_token(
        room_name=room.room_id,
        user_id=str(current_user.id),
        user_name=user_name,
        role=current_user.role.value,
        can_publish=participant.can_publish,
        can_subscribe=participant.can_subscribe
    )
    
    # Store encrypted token
    participant.join_token = encrypt_sensitive_data(token)
    await db.commit()
    
    # Create audit log
    await create_audit_entry(
        db,
        user_id=current_user.id,
        action=AuditAction.JOIN,
        resource_type="room",
        resource_id=room.id
    )
    
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    return RoomTokenResponse(
        token=token,
        room_id=room.room_id,
        livekit_url=settings.LIVEKIT_URL,
        expires_at=expires_at
    )


@router.post("/meeting-links", response_model=CreateMeetingLinkResponse)
@limiter.limit("10/minute")
async def create_meeting_links(
    request: CreateMeetingLinkRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    livekit: LiveKitClient = Depends(get_livekit_client)
) -> CreateMeetingLinkResponse:
    """
    Create meeting links for physician and patient
    """
    # Check permissions
    if not current_user.can_create_rooms:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create meeting links"
        )
    
    # Get users
    physician = await db.get(User, request.physician_id)
    patient = await db.get(User, request.patient_id)
    
    if not physician or not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Physician or patient not found"
        )
    
    # Create room
    room_data = RoomCreate(
        name=f"Consultation: {physician.email} - {patient.email}",
        scheduled_start=request.scheduled_start,
        scheduled_end=request.scheduled_end,
        enable_recording=request.enable_recording,
        max_participants=2,
        metadata={
            "physician_id": str(physician.id),
            "patient_id": str(patient.id)
        }
    )
    
    room = await create_room(room_data, db, current_user, livekit)
    
    # Create participants
    physician_participant = Participant(
        room_id=room.id,
        user_id=physician.id,
        participant_id=str(physician.id),
        role=physician.role,
        is_presenter=True
    )
    
    patient_participant = Participant(
        room_id=room.id,
        user_id=patient.id,
        participant_id=str(patient.id),
        role=patient.role
    )
    
    db.add(physician_participant)
    db.add(patient_participant)
    
    # Create meeting links
    expires_at = datetime.utcnow() + timedelta(days=7)
    
    physician_link = MeetingLink(
        room_id=room.id,
        user_id=physician.id,
        token=generate_secure_token(32),
        expires_at=expires_at,
        max_uses=10  # Allow multiple joins
    )
    
    patient_link = MeetingLink(
        room_id=room.id,
        user_id=patient.id,
        token=generate_secure_token(32),
        expires_at=expires_at,
        max_uses=10
    )
    
    db.add(physician_link)
    db.add(patient_link)
    
    await db.commit()
    
    # Generate URLs
    base_url = "https://meet.heydok.com"
    physician_url = f"{base_url}/room/{room.room_id}?token={physician_link.token}"
    patient_url = f"{base_url}/room/{room.room_id}?token={patient_link.token}"
    
    return CreateMeetingLinkResponse(
        room_id=room.room_id,
        physician_link=physician_url,
        patient_link=patient_url,
        expires_at=expires_at
    ) 