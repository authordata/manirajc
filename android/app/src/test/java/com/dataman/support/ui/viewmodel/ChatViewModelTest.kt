package com.dataman.support.ui.viewmodel

import androidx.arch.core.executor.testing.InstantTaskExecutorRule
import com.dataman.support.data.model.*
import com.dataman.support.data.repository.ChatRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.mockito.kotlin.*

/**
 * Tests ChatViewModel business logic:
 * - Session creation (human vs AI)
 * - Message sending (correct endpoint routing)
 * - Polling behavior
 * - Error handling
 */
@OptIn(ExperimentalCoroutinesApi::class)
class ChatViewModelTest {

    @get:Rule
    val instantTaskExecutorRule = InstantTaskExecutorRule()

    private val testDispatcher = StandardTestDispatcher()
    private lateinit var chatRepository: ChatRepository
    private lateinit var viewModel: ChatViewModel

    @Before
    fun setup() {
        Dispatchers.setMain(testDispatcher)
        chatRepository = mock()
        viewModel = ChatViewModel(chatRepository)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    // ---- Session Creation ----

    @Test
    fun `startSession AI calls requestAiSession`() = runTest {
        val sessionResponse = SessionResponse(sessionId = 1, status = "active", isAiSession = true)
        whenever(chatRepository.requestAiSession(any())).thenReturn(Result.success(sessionResponse))
        whenever(chatRepository.getMessages(1)).thenReturn(Result.success(emptyList()))

        viewModel.startSession("anxiety", isAi = true)
        advanceUntilIdle()

        verify(chatRepository).requestAiSession(any())
        verify(chatRepository, never()).requestHumanSession(any())

        val state = viewModel.sessionState.value
        assertTrue("Session should be active", state is SessionState.Active)
        assertEquals(1, (state as SessionState.Active).sessionId)
    }

    @Test
    fun `startSession human calls requestHumanSession`() = runTest {
        val sessionResponse = SessionResponse(sessionId = 2, status = "active", isAiSession = false)
        whenever(chatRepository.requestHumanSession(any())).thenReturn(Result.success(sessionResponse))
        whenever(chatRepository.getMessages(2)).thenReturn(Result.success(emptyList()))

        viewModel.startSession("loneliness", isAi = false)
        advanceUntilIdle()

        verify(chatRepository).requestHumanSession(any())
        verify(chatRepository, never()).requestAiSession(any())
    }

    @Test
    fun `startSession failure sets Error state`() = runTest {
        whenever(chatRepository.requestHumanSession(any()))
            .thenReturn(Result.failure(Exception("Network error")))

        viewModel.startSession(null, isAi = false)
        advanceUntilIdle()

        val state = viewModel.sessionState.value
        assertTrue("Should be error state", state is SessionState.Error)
        assertEquals("Network error", (state as SessionState.Error).message)
    }

    @Test
    fun `initial state is Idle`() {
        assertEquals(SessionState.Idle, viewModel.sessionState.value)
    }

    // ---- Message Sending ----

    @Test
    fun `sendMessage for AI session calls sendAiMessage`() = runTest {
        // Start an AI session first
        val sessionResponse = SessionResponse(sessionId = 5, status = "active", isAiSession = true)
        whenever(chatRepository.requestAiSession(any())).thenReturn(Result.success(sessionResponse))
        whenever(chatRepository.getMessages(5)).thenReturn(Result.success(emptyList()))
        whenever(chatRepository.sendAiMessage(eq(5), any()))
            .thenReturn(Result.success(AiMessageResponse("I hear you")))

        viewModel.startSession("stress", isAi = true)
        advanceUntilIdle()

        viewModel.sendMessage("I feel overwhelmed")
        advanceUntilIdle()

        verify(chatRepository).sendAiMessage(eq(5), any())
        verify(chatRepository, never()).sendMessage(any(), any())
    }

    @Test
    fun `sendMessage for human session calls sendMessage`() = runTest {
        val sessionResponse = SessionResponse(sessionId = 3, status = "active", isAiSession = false)
        whenever(chatRepository.requestHumanSession(any())).thenReturn(Result.success(sessionResponse))
        whenever(chatRepository.getMessages(3)).thenReturn(Result.success(emptyList()))
        whenever(chatRepository.sendMessage(eq(3), any()))
            .thenReturn(Result.success(SendMessageResponse(id = 10, createdAt = "2024-01-01")))

        viewModel.startSession(null, isAi = false)
        advanceUntilIdle()

        viewModel.sendMessage("Hello giver")
        advanceUntilIdle()

        verify(chatRepository).sendMessage(eq(3), any())
        verify(chatRepository, never()).sendAiMessage(any(), any())
    }

    @Test
    fun `sendMessage does nothing when no active session`() = runTest {
        viewModel.sendMessage("test")
        advanceUntilIdle()

        verify(chatRepository, never()).sendMessage(any(), any())
        verify(chatRepository, never()).sendAiMessage(any(), any())
    }

    // ---- Message Loading ----

    @Test
    fun `loadMessages populates messages LiveData`() = runTest {
        val sessionResponse = SessionResponse(sessionId = 1, status = "active", isAiSession = false)
        whenever(chatRepository.requestHumanSession(any())).thenReturn(Result.success(sessionResponse))

        val messages = listOf(
            ChatMessage(1, 1, 42, "seeker", "Hello", "2024-01-15T10:00:00"),
            ChatMessage(2, 1, 20, "giver", "Hi there", "2024-01-15T10:01:00")
        )
        whenever(chatRepository.getMessages(1)).thenReturn(Result.success(messages))

        viewModel.startSession(null, isAi = false)
        advanceUntilIdle()

        assertEquals(2, viewModel.messages.value?.size)
        assertEquals("Hello", viewModel.messages.value?.get(0)?.content)
    }

    @Test
    fun `loadMessages does nothing when idle`() = runTest {
        viewModel.loadMessages()
        advanceUntilIdle()

        verify(chatRepository, never()).getMessages(any())
    }

    // ---- Feedback ----

    @Test
    fun `submitFeedback calls repository`() = runTest {
        val sessionResponse = SessionResponse(sessionId = 1, status = "active", isAiSession = false)
        whenever(chatRepository.requestHumanSession(any())).thenReturn(Result.success(sessionResponse))
        whenever(chatRepository.getMessages(1)).thenReturn(Result.success(emptyList()))
        whenever(chatRepository.submitFeedback(eq(1), any()))
            .thenReturn(Result.success(SuccessResponse(true)))

        viewModel.startSession(null, isAi = false)
        advanceUntilIdle()

        viewModel.submitFeedback(5, "Great!")
        advanceUntilIdle()

        verify(chatRepository).submitFeedback(eq(1), check { feedback ->
            assertEquals(5, feedback.rating)
            assertEquals("Great!", feedback.comment)
        })
    }

    // ---- Polling ----

    @Test
    fun `stopPolling cancels the polling job`() = runTest {
        val sessionResponse = SessionResponse(sessionId = 1, status = "active", isAiSession = false)
        whenever(chatRepository.requestHumanSession(any())).thenReturn(Result.success(sessionResponse))
        whenever(chatRepository.getMessages(1)).thenReturn(Result.success(emptyList()))

        viewModel.startSession(null, isAi = false)
        advanceUntilIdle()

        viewModel.stopPolling()

        // After stopping, calling advanceUntilIdle should not cause more getMessages calls
        val callCountBefore = mockingDetails(chatRepository).invocations.size
        advanceUntilIdle()
        val callCountAfter = mockingDetails(chatRepository).invocations.size

        // No additional calls should happen after stopPolling
        assertEquals(callCountBefore, callCountAfter)
    }
}
