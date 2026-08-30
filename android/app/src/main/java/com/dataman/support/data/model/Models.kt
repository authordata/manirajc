package com.dataman.support.data.model

import com.google.gson.annotations.SerializedName

// --- User ---
data class User(
    val id: Int,
    val email: String,
    @SerializedName("display_name") val displayName: String,
    val role: String,
    @SerializedName("is_anonymous") val isAnonymous: Boolean
)

// --- Profiles (matching backend schema) ---
data class SeekerProfileUpsert(
    val gender: String? = null,
    @SerializedName("age_range") val ageRange: String? = null,
    @SerializedName("causes_csv") val causesCsv: String? = null,
    val visibility: String? = null
)

data class GiverProfileUpsert(
    val about: String? = null,
    val experience: String? = null,
    @SerializedName("is_available") val isAvailable: Boolean = true
)

// --- Chat Session ---
data class ChatSession(
    val id: Int,
    @SerializedName("seeker_id") val seekerId: Int,
    @SerializedName("giver_id") val giverId: Int?,
    val status: String,
    val cause: String? = null,
    @SerializedName("is_ai_session") val isAiSession: Boolean = false,
    @SerializedName("created_at") val createdAt: String? = null,
    @SerializedName("ended_at") val endedAt: String? = null
)

// --- Chat Message ---
data class ChatMessage(
    val id: Int,
    @SerializedName("session_id") val sessionId: Int,
    @SerializedName("sender_user_id") val senderUserId: Int? = null,
    @SerializedName("sender_label") val senderLabel: String,
    val content: String,
    @SerializedName("created_at") val createdAt: String
)

// --- Auth ---
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

// --- Session ---
data class SessionRequest(
    val cause: String? = null
)

data class SessionResponse(
    @SerializedName("session_id") val sessionId: Int,
    val status: String,
    @SerializedName("giver_assigned") val giverAssigned: Int? = null,
    @SerializedName("is_ai_session") val isAiSession: Boolean = false
)

// --- Messages ---
data class MessageRequest(
    val content: String
)

data class SendMessageResponse(
    val id: Int,
    @SerializedName("created_at") val createdAt: String
)

data class AiMessageResponse(
    @SerializedName("reply") val reply: String
)

// --- Feedback ---
data class FeedbackRequest(
    val rating: Int,
    val comment: String? = null
)

// --- Reports ---
data class ReportRequest(
    @SerializedName("session_id") val sessionId: Int?,
    val reason: String,
    val details: String? = null
)

// --- Generic success response from backend ---
data class SuccessResponse(
    val success: Boolean = true
)
