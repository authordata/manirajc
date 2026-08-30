package com.dataman.support.ui.viewmodel

import androidx.arch.core.executor.testing.InstantTaskExecutorRule
import com.dataman.support.data.local.TokenManager
import com.dataman.support.data.model.AuthResponse
import com.dataman.support.data.model.LoginRequest
import com.dataman.support.data.model.RegisterRequest
import com.dataman.support.data.model.User
import com.dataman.support.data.repository.AuthRepository
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
 * Tests AuthViewModel:
 * - Login flow (success/failure)
 * - Registration flow (success/failure)
 * - Logout clears token
 * - Loading state transitions
 */
@OptIn(ExperimentalCoroutinesApi::class)
class AuthViewModelTest {

    @get:Rule
    val instantTaskExecutorRule = InstantTaskExecutorRule()

    private val testDispatcher = StandardTestDispatcher()
    private lateinit var authRepository: AuthRepository
    private lateinit var tokenManager: TokenManager
    private lateinit var viewModel: AuthViewModel

    @Before
    fun setup() {
        Dispatchers.setMain(testDispatcher)
        authRepository = mock()
        tokenManager = mock()
        viewModel = AuthViewModel(authRepository, tokenManager)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    // ---- Login ----

    @Test
    fun `login success sets loginResult with success`() = runTest {
        val authResponse = AuthResponse(accessToken = "token123", tokenType = "bearer")
        whenever(authRepository.login(any())).thenReturn(Result.success(authResponse))

        viewModel.login("test@test.com", "password")
        advanceUntilIdle()

        val result = viewModel.loginResult.value
        assertNotNull(result)
        assertTrue(result!!.isSuccess)
        assertEquals("token123", result.getOrNull()?.accessToken)
    }

    @Test
    fun `login failure sets loginResult with failure`() = runTest {
        whenever(authRepository.login(any()))
            .thenReturn(Result.failure(Exception("Invalid credentials")))

        viewModel.login("bad@test.com", "wrong")
        advanceUntilIdle()

        val result = viewModel.loginResult.value
        assertNotNull(result)
        assertTrue(result!!.isFailure)
        assertEquals("Invalid credentials", result.exceptionOrNull()?.message)
    }

    @Test
    fun `login passes LoginRequest to repository`() = runTest {
        whenever(authRepository.login(any()))
            .thenReturn(Result.success(AuthResponse("x", "bearer")))

        viewModel.login("user@test.com", "pass123")
        advanceUntilIdle()

        verify(authRepository).login(check { request ->
            assertEquals("user@test.com", request.email)
            assertEquals("pass123", request.password)
        })
    }

    // ---- Register ----

    @Test
    fun `register success sets registerResult`() = runTest {
        val authResponse = AuthResponse(accessToken = "newtoken", tokenType = "bearer")
        whenever(authRepository.register(any())).thenReturn(Result.success(authResponse))

        viewModel.register("new@test.com", "pass", "New User", "seeker", true)
        advanceUntilIdle()

        val result = viewModel.registerResult.value
        assertNotNull(result)
        assertTrue(result!!.isSuccess)
    }

    @Test
    fun `register passes correct RegisterRequest`() = runTest {
        whenever(authRepository.register(any()))
            .thenReturn(Result.success(AuthResponse("x", "bearer")))

        viewModel.register("new@test.com", "pass", "New User", "seeker", true)
        advanceUntilIdle()

        verify(authRepository).register(check { request ->
            assertEquals("new@test.com", request.email)
            assertEquals("pass", request.password)
            assertEquals("New User", request.displayName)
            assertEquals("seeker", request.role)
            assertTrue(request.isAnonymous)
        })
    }

    @Test
    fun `register failure sets error result`() = runTest {
        whenever(authRepository.register(any()))
            .thenReturn(Result.failure(Exception("Email already taken")))

        viewModel.register("taken@test.com", "pass", "User", "seeker", false)
        advanceUntilIdle()

        val result = viewModel.registerResult.value
        assertTrue(result!!.isFailure)
        assertEquals("Email already taken", result.exceptionOrNull()?.message)
    }

    // ---- Loading State ----

    @Test
    fun `isLoading is false initially`() {
        assertEquals(false, viewModel.isLoading.value)
    }

    @Test
    fun `isLoading becomes false after login completes`() = runTest {
        whenever(authRepository.login(any()))
            .thenReturn(Result.success(AuthResponse("x", "bearer")))

        viewModel.login("a@b.com", "p")
        advanceUntilIdle()

        assertEquals(false, viewModel.isLoading.value)
    }

    // ---- Logout ----

    @Test
    fun `logout clears token`() {
        viewModel.logout()

        verify(tokenManager).clearToken()
    }

    @Test
    fun `logout clears current user`() = runTest {
        // Set up a current user first
        val user = User(1, "test@test.com", "Test", "seeker", false)
        whenever(authRepository.getCurrentUser()).thenReturn(Result.success(user))

        viewModel.loadCurrentUser()
        advanceUntilIdle()
        assertNotNull(viewModel.currentUser.value)

        viewModel.logout()

        assertNull(viewModel.currentUser.value)
    }

    // ---- Load Current User ----

    @Test
    fun `loadCurrentUser populates user on success`() = runTest {
        val user = User(42, "test@test.com", "Test User", "seeker", false)
        whenever(authRepository.getCurrentUser()).thenReturn(Result.success(user))

        viewModel.loadCurrentUser()
        advanceUntilIdle()

        assertEquals(42, viewModel.currentUser.value?.id)
        assertEquals("Test User", viewModel.currentUser.value?.displayName)
    }

    @Test
    fun `loadCurrentUser does not crash on failure`() = runTest {
        whenever(authRepository.getCurrentUser())
            .thenReturn(Result.failure(Exception("Not authenticated")))

        viewModel.loadCurrentUser()
        advanceUntilIdle()

        assertNull(viewModel.currentUser.value)
    }
}
