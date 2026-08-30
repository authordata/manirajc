package com.dataman.support.data.model

import com.google.gson.annotations.SerializedName

data class User(
    val id: String,
    val email: String,
    @SerializedName("display_name") val displayName: String,
    val role: String,
    @SerializedName("is_anonymous") val isAnonymous: Boolean
)

data class SeekerProfile(
    val id: String,
    @SerializedName("user_id") val userId: String,
    val bio: String? = null
)

data class GiverProfile(
    val id: String,
    @SerializedName("user_id") val userId: String,
    val bio: String? = null,
    val rating: Float? = null
)

data class ChatSession(
    val id: String,
    @SerializedName("seeker_id") val seekerId: String,
    @SerializedName("giver_id") val giverId: String?,
    val status: String,
    val cause: String? = null,
    @SerializedName("created_at") val createdAt: String
)

data class ChatMessage(
    val id: Int,
    @SerializedName("session_id") val sessionId: Int,
    @SerializedName("sender_user_id") val senderUserId: Int? = null,
    @SerializedName("sender_label") val senderLabel: String,
    val content: String,
    @SerializedName("created_at") val createdAt: String
)

data class FeedbackRequest(
    val rating: Int,
    val comment: String? = null
)

data class FeedbackResponse(
    val id: Int,
    @SerializedName("session_id") val sessionId: Int,
    val rating: Int,
    val comment: String? = null,
    @SerializedName("created_at") val createdAt: String
)

data class ReportRequest(
    @SerializedName("session_id") val sessionId: Int?,
    val reason: String,
    val details: String? = null
)

data class RegisterRequest(
    val email: String,
    val password: String,
    @SerializedName("display_name") val displayName: String,
    val role: String,
    @SerializedName("is_anonymous") val isAnonymous: Boolean = true
)

data class LoginRequest(
    val email: String,
    val password: String
)

data class AuthResponse(
    @SerializedName("access_token") val accessToken: String,
    @SerializedName("token_type") val tokenType: String = "bearer"
)

data class SessionRequest(
    val cause: String? = null
)

data class SessionResponse(
    @SerializedName("session_id") val sessionId: Int,
    val status: String,
    @SerializedName("is_ai_session") val isAiSession: Boolean = false
)

data class MessageRequest(
    val content: String
)

data class AiMessageResponse(
    @SerializedName("reply") val reply: String
)
