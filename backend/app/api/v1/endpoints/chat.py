"""
Chat API endpoints
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
from app.core.security import encrypt_sensitive_data, decrypt_sensitive_data
from app.core.redis import redis_client
from app.models.room import Room
from app.models.chat import ChatMessage
from app.models.participant import Participant
from app.models.user import User
from app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageUpdate,
    ChatMessageResponse,
    ChatMessageListResponse
)
from app.api.deps import get_current_user

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/rooms/{room_id}/messages", response_model=ChatMessageResponse)
@limiter.limit("30/minute")
async def send_message(
    room_id: UUID,
    message_data: ChatMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ChatMessage:
    """
    Send a chat message in a room
    """
    # Get room
    room = await db.get(Room, room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # Check if chat is enabled
    if not room.enable_chat:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chat is not enabled for this room"
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
    
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this room"
        )
    
    # Create encrypted message
    message = ChatMessage(
        room_id=room_id,
        sender_id=current_user.id,
        encrypted_message=encrypt_sensitive_data(message_data.message),
        metadata=message_data.metadata
    )
    
    db.add(message)
    await db.commit()
    await db.refresh(message)
    
    # Publish to Redis for real-time delivery
    await redis_client.client.publish(
        f"room:{room.room_id}:chat",
        {
            "id": str(message.id),
            "sender_id": str(current_user.id),
            "message": message_data.message,  # Send unencrypted for real-time
            "sent_at": message.sent_at.isoformat(),
            "metadata": message.metadata
        }
    )
    
    return message


@router.get("/rooms/{room_id}/messages", response_model=ChatMessageListResponse)
async def list_messages(
    room_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    since: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ChatMessageListResponse:
    """
    List chat messages in a room
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
    
    if not participant and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this room"
        )
    
    # Build query
    query = select(ChatMessage).where(
        and_(
            ChatMessage.room_id == room_id,
            ChatMessage.deleted_at.is_(None)
        )
    )
    
    # Filter by time if provided
    if since:
        query = query.where(ChatMessage.sent_at > since)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Apply pagination
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(ChatMessage.sent_at.desc())
    
    # Execute query
    result = await db.execute(query)
    messages = result.scalars().all()
    
    # Decrypt messages for response
    decrypted_messages = []
    for msg in messages:
        decrypted_messages.append(
            ChatMessageResponse(
                id=msg.id,
                room_id=msg.room_id,
                sender_id=msg.sender_id,
                message=decrypt_sensitive_data(msg.encrypted_message),
                sent_at=msg.sent_at,
                edited_at=msg.edited_at,
                metadata=msg.metadata
            )
        )
    
    return ChatMessageListResponse(
        messages=decrypted_messages,
        total=total,
        page=page,
        page_size=page_size
    )


@router.patch("/messages/{message_id}", response_model=ChatMessageResponse)
async def update_message(
    message_id: UUID,
    message_update: ChatMessageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ChatMessage:
    """
    Update a chat message
    """
    # Get message
    message = await db.get(ChatMessage, message_id)
    if not message or message.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    # Check permissions
    if message.sender_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own messages"
        )
    
    # Check if message is too old to edit (e.g., 15 minutes)
    if (datetime.utcnow() - message.sent_at).total_seconds() > 900:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message is too old to edit"
        )
    
    # Update message
    if message_update.message is not None:
        message.edit(encrypt_sensitive_data(message_update.message))
    
    await db.commit()
    await db.refresh(message)
    
    # Get room for Redis publish
    room = await db.get(Room, message.room_id)
    
    # Publish update to Redis
    await redis_client.client.publish(
        f"room:{room.room_id}:chat:update",
        {
            "id": str(message.id),
            "message": message_update.message,
            "edited_at": message.edited_at.isoformat()
        }
    )
    
    return message


@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Delete a chat message (soft delete)
    """
    # Get message
    message = await db.get(ChatMessage, message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    # Check permissions
    if message.sender_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own messages"
        )
    
    # Soft delete
    message.soft_delete()
    
    await db.commit()
    
    # Get room for Redis publish
    room = await db.get(Room, message.room_id)
    
    # Publish deletion to Redis
    await redis_client.client.publish(
        f"room:{room.room_id}:chat:delete",
        {"id": str(message.id)}
    )
    
    return {"message": "Message deleted successfully"} 