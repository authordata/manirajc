package com.dataman.support.data.model

import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

/**
 * Tests that all data models serialize/deserialize correctly
 * to match the actual backend JSON contracts.
 */
class ModelsSerializationTest {

    private lateinit var gson: Gson

    @Before
    fun setup() {
        gson = Gson()
    }

    // ---- AuthResponse ----

    @Test
    fun `AuthResponse deserializes correctly from backend JSON`() {
        val json = """{"access_token": "eyJhbGciOiJIUzI1NiJ9.test", "token_type": "bearer"}"""
        val response = gson.fromJson(json, AuthResponse::class.java)

        assertEquals("eyJhbGciOiJIUzI1NiJ9.test", response.accessToken)
        assertEquals("bearer", response.tokenType)
    }

    @Test
    fun `AuthResponse default tokenType is bearer`() {
        val json = """{"access_token": "abc123"}"""
        val response = gson.fromJson(json, AuthResponse::class.java)

        assertEquals("abc123", response.accessToken)
        assertEquals("bearer", response.tokenType)
    }

    // ---- User ----

    @Test
    fun `User deserializes with integer id from backend`() {
        val json = """{"id": 42, "email": "test@test.com", "display_name": "Test User", "role": "seeker", "is_anonymous": false}"""
        val user = gson.fromJson(json, User::class.java)

        assertEquals(42, user.id)
        assertEquals("test@test.com", user.email)
        assertEquals("Test User", user.displayName)
        assertEquals("seeker", user.role)
        assertFalse(user.isAnonymous)
    }

    // ---- SessionResponse ----

    @Test
    fun `SessionResponse uses session_id not id`() {
        val json = """{"session_id": 7, "status": "active", "giver_assigned": null, "is_ai_session": false}"""
        val response = gson.fromJson(json, SessionResponse::class.java)

        assertEquals(7, response.sessionId)
        assertEquals("active", response.status)
        assertNull(response.giverAssigned)
        assertFalse(response.isAiSession)
    }

    @Test
    fun `SessionResponse AI session flag is true`() {
        val json = """{"session_id": 10, "status": "active", "giver_assigned": null, "is_ai_session": true}"""
        val response = gson.fromJson(json, SessionResponse::class.java)

        assertEquals(10, response.sessionId)
        assertTrue(response.isAiSession)
    }

    // ---- ChatMessage ----

    @Test
    fun `ChatMessage deserializes with all fields from backend`() {
        val json = """{
            "id": 1,
            "session_id": 5,
            "sender_user_id": 42,
            "sender_label": "seeker",
            "content": "Hello, I need help",
            "created_at": "2024-01-15T10:30:00"
        }"""
        val msg = gson.fromJson(json, ChatMessage::class.java)

        assertEquals(1, msg.id)
        assertEquals(5, msg.sessionId)
        assertEquals(42, msg.senderUserId)
        assertEquals("seeker", msg.senderLabel)
        assertEquals("Hello, I need help", msg.content)
        assertEquals("2024-01-15T10:30:00", msg.createdAt)
    }

    @Test
    fun `ChatMessage AI bot has null sender_user_id`() {
        val json = """{
            "id": 2,
            "session_id": 5,
            "sender_user_id": null,
            "sender_label": "ai_bot",
            "content": "I hear you.",
            "created_at": "2024-01-15T10:30:05"
        }"""
        val msg = gson.fromJson(json, ChatMessage::class.java)

        assertNull(msg.senderUserId)
        assertEquals("ai_bot", msg.senderLabel)
    }

    @Test
    fun `ChatMessage list deserializes from backend array`() {
        val json = """[
            {"id": 1, "session_id": 5, "sender_user_id": 42, "sender_label": "seeker", "content": "Hi", "created_at": "2024-01-15T10:30:00"},
            {"id": 2, "session_id": 5, "sender_user_id": null, "sender_label": "ai_bot", "content": "Hello!", "created_at": "2024-01-15T10:30:05"}
        ]"""
        val type = object : TypeToken<List<ChatMessage>>() {}.type
        val messages: List<ChatMessage> = gson.fromJson(json, type)

        assertEquals(2, messages.size)
        assertEquals("seeker", messages[0].senderLabel)
        assertEquals("ai_bot", messages[1].senderLabel)
    }

    // ---- SendMessageResponse ----

    @Test
    fun `SendMessageResponse only has id and created_at`() {
        val json = """{"id": 15, "created_at": "2024-01-15T10:31:00"}"""
        val response = gson.fromJson(json, SendMessageResponse::class.java)

        assertEquals(15, response.id)
        assertEquals("2024-01-15T10:31:00", response.createdAt)
    }

    // ---- AiMessageResponse ----

    @Test
    fun `AiMessageResponse has reply field`() {
        val json = """{"reply": "I hear you. Thank you for sharing this."}"""
        val response = gson.fromJson(json, AiMessageResponse::class.java)

        assertEquals("I hear you. Thank you for sharing this.", response.reply)
    }

    // ---- SuccessResponse ----

    @Test
    fun `SuccessResponse from feedback endpoint`() {
        val json = """{"success": true}"""
        val response = gson.fromJson(json, SuccessResponse::class.java)

        assertTrue(response.success)
    }

    // ---- RegisterRequest ----

    @Test
    fun `RegisterRequest serializes with correct field names`() {
        val request = RegisterRequest("test@test.com", "pass123", "Test", "seeker", true)
        val json = gson.toJson(request)

        assertTrue(json.contains("\"display_name\""))
        assertTrue(json.contains("\"is_anonymous\""))
        assertFalse(json.contains("\"displayName\""))
    }

    // ---- SessionRequest ----

    @Test
    fun `SessionRequest serializes cause field`() {
        val request = SessionRequest("anxiety")
        val json = gson.toJson(request)

        assertTrue(json.contains("\"cause\":\"anxiety\""))
    }

    @Test
    fun `SessionRequest with null cause`() {
        val request = SessionRequest(null)
        val json = gson.toJson(request)

        // Gson omits null by default or serializes as null
        val deserialized = gson.fromJson(json, SessionRequest::class.java)
        assertNull(deserialized.cause)
    }

    // ---- MessageRequest ----

    @Test
    fun `MessageRequest serializes content`() {
        val request = MessageRequest("I feel overwhelmed")
        val json = gson.toJson(request)

        assertTrue(json.contains("\"content\":\"I feel overwhelmed\""))
    }

    // ---- FeedbackRequest ----

    @Test
    fun `FeedbackRequest serializes rating and optional comment`() {
        val request = FeedbackRequest(5, "Great support!")
        val json = gson.toJson(request)

        assertTrue(json.contains("\"rating\":5"))
        assertTrue(json.contains("\"comment\":\"Great support!\""))
    }

    @Test
    fun `FeedbackRequest with null comment`() {
        val request = FeedbackRequest(3, null)
        val deserialized = gson.fromJson(gson.toJson(request), FeedbackRequest::class.java)

        assertEquals(3, deserialized.rating)
        assertNull(deserialized.comment)
    }

    // ---- ReportRequest ----

    @Test
    fun `ReportRequest serializes with session_id field name`() {
        val request = ReportRequest(5, "harassment", "Details here")
        val json = gson.toJson(request)

        assertTrue(json.contains("\"session_id\""))
        assertFalse(json.contains("\"sessionId\""))
    }

    // ---- Profile models ----

    @Test
    fun `SeekerProfileUpsert serializes correct fields`() {
        val profile = SeekerProfileUpsert("male", "25-34", "anxiety,depression", "public")
        val json = gson.toJson(profile)

        assertTrue(json.contains("\"age_range\""))
        assertTrue(json.contains("\"causes_csv\""))
        assertFalse(json.contains("\"ageRange\""))
    }

    @Test
    fun `GiverProfileUpsert serializes correct fields`() {
        val profile = GiverProfileUpsert("Licensed therapist", "5 years", true)
        val json = gson.toJson(profile)

        assertTrue(json.contains("\"is_available\""))
        assertFalse(json.contains("\"isAvailable\""))
    }

    // ---- ChatSession ----

    @Test
    fun `ChatSession deserializes with integer ids`() {
        val json = """{
            "id": 1, "seeker_id": 10, "giver_id": 20,
            "status": "active", "cause": "anxiety",
            "is_ai_session": false, "created_at": "2024-01-15T10:00:00"
        }"""
        val session = gson.fromJson(json, ChatSession::class.java)

        assertEquals(1, session.id)
        assertEquals(10, session.seekerId)
        assertEquals(20, session.giverId)
        assertFalse(session.isAiSession)
    }

    @Test
    fun `ChatSession AI session has null giver_id`() {
        val json = """{"id": 2, "seeker_id": 10, "giver_id": null, "status": "active", "is_ai_session": true}"""
        val session = gson.fromJson(json, ChatSession::class.java)

        assertNull(session.giverId)
        assertTrue(session.isAiSession)
    }
}
