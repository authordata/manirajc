package com.dataman.support

object ApiConfig {
    const val BASE_URL = "http://10.0.2.2:8000"
}

data class RegisterRequest(
    val email: String,
    val password: String,
    val display_name: String,
    val role: String,
    val is_anonymous: Boolean = true
)

data class LoginRequest(
    val email: String,
    val password: String
)

data class AuthResponse(
    val access_token: String,
    val token_type: String = "bearer"
)

data class SessionRequest(
    val cause: String?
)

data class SessionResponse(
    val session_id: Int,
    val status: String
)
