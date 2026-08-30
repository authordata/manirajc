package com.dataman.support.data.model

import com.google.gson.annotations.SerializedName

data class RegisterRequest(
    val email: String,
    val passwordHash: String,
    val role: String,
    val phoneNumber: String? = null
)

data class AuthResponse(
    @SerializedName("access_token") val accessToken: String,
    @SerializedName("token_type") val tokenType: String
)

data class User(
    val id: Int,
    val email: String,
    val role: String,
    @SerializedName("is_active") val isActive: Boolean,
    @SerializedName("is_verified") val isVerified: Boolean
)

data class SessionRequest(
    val cause: String? = null
)

data class SessionResponse(
    @SerializedName("session_id") val sessionId: String,
    val status: String,
    val cause: String?
)

data class ChatMessage(
    val id: Int,
    @SerializedName("session_id") val sessionId: String,
    @SerializedName("sender_id") val senderId: Int,
    val content: String,
    @SerializedName("created_at") val createdAt: String
)

data class MessageRequest(
    val content: String
)

data class SendMessageResponse(
    val id: Int,
    val status: String
)

data class AiMessageResponse(
    val content: String
)

data class FeedbackRequest(
    val rating: Int,
    val comments: String? = null
)

data class ReportRequest(
    @SerializedName("reported_user_id") val reportedUserId: Int,
    val reason: String
)

data class SuccessResponse(
    val message: String
)

data class SeekerProfileUpsert(
    val alias: String,
    val causes: List<String>
)

data class GiverProfileUpsert(
    val name: String,
    val bio: String?,
    val qualifications: List<String>
)

data class SendOtpRequest(
    val method: String,
    val target: String
)

data class OtpResponse(
    val message: String,
    @SerializedName("reference_id") val referenceId: String
)

data class VerifyOtpRequest(
    @SerializedName("reference_id") val referenceId: String,
    val code: String
)

data class FriendRequestCreate(
    @SerializedName("target_user_id") val targetUserId: Int
)

data class FriendRequestResponse(
    val id: Int,
    @SerializedName("requester_id") val requesterId: Int,
    @SerializedName("target_id") val targetId: Int,
    val status: String,
    @SerializedName("created_at") val createdAt: String
)

data class FriendRespondRequest(
    val action: String
)

data class SubscriptionStatus(
    @SerializedName("is_premium") val isPremium: Boolean,
    @SerializedName("expires_at") val expiresAt: String?
)

data class SessionInfo(
    @SerializedName("session_id") val sessionId: Int,
    val cause: String?,
    val status: String,
    @SerializedName("is_ai_session") val isAiSession: Boolean = false,
    @SerializedName("created_at") val createdAt: String,
    @SerializedName("seeker_alias") val seekerAlias: String? = null,
    @SerializedName("last_message") val lastMessage: String? = null,
    @SerializedName("last_message_time") val lastMessageTime: String? = null
)
