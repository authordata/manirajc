package com.dataman.support.data.remote

import com.dataman.support.data.model.*
import retrofit2.Response
import retrofit2.http.*

interface ApiService {
    @POST("/auth/register")
    suspend fun register(@Body request: RegisterRequest): Response<AuthResponse>

    @POST("/auth/login")
    suspend fun login(@Body request: LoginRequest): Response<AuthResponse>

    @GET("/users/me")
    suspend fun getCurrentUser(): Response<User>

    @PUT("/users/me")
    suspend fun updateUser(@Body user: User): Response<User>

    @POST("/sessions")
    suspend fun createSession(@Body request: SessionRequest): Response<SessionResponse>

    @GET("/sessions/{id}/messages")
    suspend fun getMessages(@Path("id") sessionId: String): Response<List<ChatMessage>>

    @POST("/sessions/{id}/messages")
    suspend fun sendMessage(
        @Path("id") sessionId: String,
        @Body request: MessageRequest
    ): Response<ChatMessage>

    @POST("/sessions/{id}/feedback")
    suspend fun submitFeedback(
        @Path("id") sessionId: String,
        @Body request: FeedbackRequest
    ): Response<FeedbackResponse>

    @POST("/reports")
    suspend fun submitReport(@Body request: ReportRequest): Response<Unit>
}
