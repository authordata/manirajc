package com.dataman.support.data.remote

import com.dataman.support.data.model.*
import com.google.gson.Gson
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

/**
 * Tests the Retrofit ApiService against a MockWebServer
 * to verify endpoint URLs, HTTP methods, and request/response parsing.
 */
class ApiServiceTest {

    private lateinit var mockWebServer: MockWebServer
    private lateinit var apiService: ApiService
    private val gson = Gson()

    @Before
    fun setup() {
        mockWebServer = MockWebServer()
        mockWebServer.start()

        val retrofit = Retrofit.Builder()
            .baseUrl(mockWebServer.url("/"))
            .addConverterFactory(GsonConverterFactory.create())
            .build()

        apiService = retrofit.create(ApiService::class.java)
    }

    @After
    fun tearDown() {
        mockWebServer.shutdown()
    }

    // ---- Auth Endpoints ----

    @Test
    fun `register sends POST to auth-register with JSON body`() = runBlockingTest {
        mockWebServer.enqueue(
            MockResponse()
                .setBody("""{"access_token": "tok123", "token_type": "bearer"}""")
                .setResponseCode(200)
        )

        val response = apiService.register(
            RegisterRequest("test@test.com", "pass", "Name", "seeker", true)
        )

        val request = mockWebServer.takeRequest()
        assertEquals("POST", request.method)
        assertEquals("/auth/register", request.path)
        assertTrue(request.body.readUtf8().contains("\"display_name\""))
        assertTrue(response.isSuccessful)
        assertEquals("tok123", response.body()?.accessToken)
    }

    @Test
    fun `login sends POST to auth-login with form-encoded body`() = runBlockingTest {
        mockWebServer.enqueue(
            MockResponse()
                .setBody("""{"access_token": "tok456", "token_type": "bearer"}""")
                .setResponseCode(200)
        )

        val response = apiService.login("user@test.com", "password123")

        val request = mockWebServer.takeRequest()
        assertEquals("POST", request.method)
        assertEquals("/auth/login", request.path)
        val body = request.body.readUtf8()
        // Form-encoded: username=user%40test.com&password=password123
        assertTrue("Should be form-encoded with 'username'", body.contains("username="))
        assertTrue("Should contain password field", body.contains("password="))
        assertFalse("Should NOT be JSON", body.contains("{"))
        assertTrue(response.isSuccessful)
    }

    @Test
    fun `login uses username field not email`() = runBlockingTest {
        mockWebServer.enqueue(
            MockResponse()
                .setBody("""{"access_token": "x", "token_type": "bearer"}""")
                .setResponseCode(200)
        )

        apiService.login("me@test.com", "pass")
        val body = mockWebServer.takeRequest().body.readUtf8()

        assertTrue("Backend expects 'username' field", body.contains("username="))
        assertFalse("Should NOT contain 'email' field", body.contains("email="))
    }

    // ---- Session Endpoints ----

    @Test
    fun `requestHumanSession sends POST to sessions-request`() = runBlockingTest {
        mockWebServer.enqueue(
            MockResponse()
                .setBody("""{"session_id": 1, "status": "active", "giver_assigned": null, "is_ai_session": false}""")
                .setResponseCode(200)
        )

        val response = apiService.requestHumanSession(SessionRequest("anxiety"))

        val request = mockWebServer.takeRequest()
        assertEquals("POST", request.method)
        assertEquals("/sessions/request", request.path)
        assertEquals(1, response.body()?.sessionId)
        assertFalse(response.body()!!.isAiSession)
    }

    @Test
    fun `requestAiSession sends POST to sessions-request-ai`() = runBlockingTest {
        mockWebServer.enqueue(
            MockResponse()
                .setBody("""{"session_id": 2, "status": "active", "giver_assigned": null, "is_ai_session": true}""")
                .setResponseCode(200)
        )

        val response = apiService.requestAiSession(SessionRequest("stress"))

        val request = mockWebServer.takeRequest()
        assertEquals("POST", request.method)
        assertEquals("/sessions/request-ai", request.path)
        assertTrue(response.body()!!.isAiSession)
    }

    // ---- Message Endpoints ----

    @Test
    fun `sendMessage sends POST to sessions-id-messages`() = runBlockingTest {
        mockWebServer.enqueue(
            MockResponse()
                .setBody("""{"id": 10, "created_at": "2024-01-15T10:30:00"}""")
                .setResponseCode(200)
        )

        val response = apiService.sendMessage("5", MessageRequest("Help me"))

        val request = mockWebServer.takeRequest()
        assertEquals("POST", request.method)
        assertEquals("/sessions/5/messages", request.path)
        assertEquals(10, response.body()?.id)
    }

    @Test
    fun `sendAiMessage sends POST to sessions-id-ai-message`() = runBlockingTest {
        mockWebServer.enqueue(
            MockResponse()
                .setBody("""{"reply": "I hear you. Thank you for sharing."}""")
                .setResponseCode(200)
        )

        val response = apiService.sendAiMessage("3", MessageRequest("I feel sad"))

        val request = mockWebServer.takeRequest()
        assertEquals("POST", request.method)
        assertEquals("/sessions/3/ai-message", request.path)
        assertEquals("I hear you. Thank you for sharing.", response.body()?.reply)
    }

    @Test
    fun `getMessages sends GET to sessions-id-messages`() = runBlockingTest {
        mockWebServer.enqueue(
            MockResponse()
                .setBody("""[{"id":1,"session_id":5,"sender_user_id":42,"sender_label":"seeker","content":"Hi","created_at":"2024-01-15T10:30:00"}]""")
                .setResponseCode(200)
        )

        val response = apiService.getMessages("5")

        val request = mockWebServer.takeRequest()
        assertEquals("GET", request.method)
        assertEquals("/sessions/5/messages", request.path)
        assertEquals(1, response.body()?.size)
    }

    // ---- Feedback & Reports ----

    @Test
    fun `submitFeedback sends POST to feedback-id`() = runBlockingTest {
        mockWebServer.enqueue(
            MockResponse()
                .setBody("""{"success": true}""")
                .setResponseCode(200)
        )

        val response = apiService.submitFeedback("5", FeedbackRequest(4, "Good"))

        val request = mockWebServer.takeRequest()
        assertEquals("POST", request.method)
        assertEquals("/feedback/5", request.path)
        assertTrue(response.body()!!.success)
    }

    @Test
    fun `submitReport sends POST to reports`() = runBlockingTest {
        mockWebServer.enqueue(
            MockResponse()
                .setBody("""{"success": true}""")
                .setResponseCode(200)
        )

        val response = apiService.submitReport(ReportRequest(1, "abuse", "Details"))

        val request = mockWebServer.takeRequest()
        assertEquals("POST", request.method)
        assertEquals("/reports", request.path)
    }

    // ---- Profile Endpoints ----

    @Test
    fun `updateSeekerProfile sends PUT to profiles-seeker`() = runBlockingTest {
        mockWebServer.enqueue(
            MockResponse()
                .setBody("""{"success": true}""")
                .setResponseCode(200)
        )

        val response = apiService.updateSeekerProfile(
            SeekerProfileUpsert("male", "25-34", "anxiety", "public")
        )

        val request = mockWebServer.takeRequest()
        assertEquals("PUT", request.method)
        assertEquals("/profiles/seeker", request.path)
    }

    @Test
    fun `updateGiverProfile sends PUT to profiles-giver`() = runBlockingTest {
        mockWebServer.enqueue(
            MockResponse()
                .setBody("""{"success": true}""")
                .setResponseCode(200)
        )

        val response = apiService.updateGiverProfile(
            GiverProfileUpsert("Therapist", "5 years", true)
        )

        val request = mockWebServer.takeRequest()
        assertEquals("PUT", request.method)
        assertEquals("/profiles/giver", request.path)
    }

    // ---- Error Handling ----

    @Test
    fun `401 response is handled without crash`() = runBlockingTest {
        mockWebServer.enqueue(MockResponse().setResponseCode(401).setBody("""{"detail": "Not authenticated"}"""))

        val response = apiService.getCurrentUser()

        assertFalse(response.isSuccessful)
        assertEquals(401, response.code())
    }

    @Test
    fun `422 validation error from login`() = runBlockingTest {
        mockWebServer.enqueue(MockResponse().setResponseCode(422).setBody("""{"detail": "Validation Error"}"""))

        val response = apiService.login("bad", "bad")

        assertFalse(response.isSuccessful)
        assertEquals(422, response.code())
    }

    @Test
    fun `404 session not found`() = runBlockingTest {
        mockWebServer.enqueue(MockResponse().setResponseCode(404).setBody("""{"detail": "Session not found"}"""))

        val response = apiService.getMessages("999")

        assertFalse(response.isSuccessful)
        assertEquals(404, response.code())
    }

    // Helper to run suspend functions in tests
    private fun runBlockingTest(block: suspend () -> Unit) {
        kotlinx.coroutines.runBlocking { block() }
    }
}
