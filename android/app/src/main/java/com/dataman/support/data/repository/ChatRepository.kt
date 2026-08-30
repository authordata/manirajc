package com.dataman.support.data.repository

import com.dataman.support.data.model.*
import com.dataman.support.data.remote.ApiService

class ChatRepository(private val apiService: ApiService) {
    
    suspend fun requestHumanSession(request: SessionRequest): Result<SessionResponse> {
        return try {
            val response = apiService.requestHumanSession(request)
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("Failed to request human session: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun requestAiSession(request: SessionRequest): Result<SessionResponse> {
        return try {
            val response = apiService.requestAiSession(request)
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("Failed to request AI session: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun getMessages(sessionId: Int): Result<List<ChatMessage>> {
        return try {
            val response = apiService.getMessages(sessionId.toString())
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("Failed to fetch messages: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun sendMessage(sessionId: Int, request: MessageRequest): Result<ChatMessage> {
        return try {
            val response = apiService.sendMessage(sessionId.toString(), request)
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("Failed to send message: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun sendAiMessage(sessionId: Int, request: MessageRequest): Result<AiMessageResponse> {
        return try {
            val response = apiService.sendAiMessage(sessionId.toString(), request)
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("Failed to send AI message: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun submitFeedback(sessionId: Int, request: FeedbackRequest): Result<FeedbackResponse> {
        return try {
            val response = apiService.submitFeedback(sessionId.toString(), request)
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("Failed to submit feedback: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun submitReport(request: ReportRequest): Result<Unit> {
        return try {
            val response = apiService.submitReport(request)
            if (response.isSuccessful) {
                Result.success(Unit)
            } else {
                Result.failure(Exception("Failed to submit report: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
