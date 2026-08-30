package com.dataman.support.data.remote

import com.dataman.support.data.model.*
import retrofit2.Response
import retrofit2.http.*

interface ApiService {
    @POST("/auth/register")
    suspend fun register(@Body request: RegisterRequest): Response<AuthResponse>

    @FormUrlEncoded
    @POST("/auth/login")
    suspend fun login(
        @Field("username") email: String,
        @Field("password") password: String
    ): Response<AuthResponse>

    @GET("/users/me")
    suspend fun getCurrentUser(): Response<User>

    @POST("/sessions/request")
    suspend fun requestHumanSession(@Body request: SessionRequest): Response<SessionResponse>

    @POST("/sessions/request-ai")
    suspend fun requestAiSession(@Body request: SessionRequest): Response<SessionResponse>

    @GET("/sessions/{id}/messages")
    suspend fun getMessages(@Path("id") sessionId: String): Response<List<ChatMessage>>

    @POST("/sessions/{id}/messages")
    suspend fun sendMessage(
        @Path("id") sessionId: String,
        @Body request: MessageRequest
    ): Response<SendMessageResponse>

    @POST("/sessions/{id}/ai-message")
    suspend fun sendAiMessage(
        @Path("id") sessionId: String,
        @Body request: MessageRequest
    ): Response<AiMessageResponse>

    @POST("/feedback/{id}")
    suspend fun submitFeedback(
        @Path("id") sessionId: String,
        @Body request: FeedbackRequest
    ): Response<SuccessResponse>

    @POST("/reports")
    suspend fun submitReport(@Body request: ReportRequest): Response<SuccessResponse>

    @PUT("/profiles/seeker")
    suspend fun updateSeekerProfile(@Body profile: SeekerProfileUpsert): Response<SuccessResponse>

    @PUT("/profiles/giver")
    suspend fun updateGiverProfile(@Body profile: GiverProfileUpsert): Response<SuccessResponse>

    @POST("/auth/send-otp")
    suspend fun sendOtp(@Body request: SendOtpRequest): Response<OtpResponse>

    @POST("/auth/verify-otp")
    suspend fun verifyOtp(@Body request: VerifyOtpRequest): Response<SuccessResponse>

    @POST("/friends/request")
    suspend fun sendFriendRequest(@Body request: FriendRequestCreate): Response<FriendRequestResponse>

    @PUT("/friends/{requestId}/respond")
    suspend fun respondToFriendRequest(@Path("requestId") requestId: Int, @Body request: FriendRespondRequest): Response<SuccessResponse>

    @GET("/friends")
    suspend fun getFriends(): Response<List<FriendRequestResponse>>

    @DELETE("/users/me")
    suspend fun deleteAccount(): Response<SuccessResponse>
}