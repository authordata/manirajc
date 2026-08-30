package com.dataman.support.data.repository

import com.dataman.support.data.local.TokenManager
import com.dataman.support.data.model.AuthResponse
import com.dataman.support.data.model.LoginRequest
import com.dataman.support.data.model.RegisterRequest
import com.dataman.support.data.model.User
import com.dataman.support.data.remote.ApiService
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.runTest
import okhttp3.ResponseBody.Companion.toResponseBody
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import org.mockito.kotlin.*
import retrofit2.Response

/**
 * Tests AuthRepository:
 * - Token saving on successful login/register
 * - Error propagation
 * - Logout clearing
 */
@OptIn(ExperimentalCoroutinesApi::class)
class AuthRepositoryTest {

    private lateinit var apiService: ApiService
    private lateinit var tokenManager: TokenManager
    private lateinit var repository: AuthRepository

    @Before
    fun setup() {
        apiService = mock()
        tokenManager = mock()
        repository = AuthRepository(apiService, tokenManager)
    }

    // ---- Login ----

    @Test
    fun `login saves token on success`() = runTest {
        val authResponse = AuthResponse("mytoken123", "bearer")
        whenever(apiService.login(any(), any())).thenReturn(Response.success(authResponse))

        val result = repository.login(LoginRequest("user@test.com", "pass"))

        assertTrue(result.isSuccess)
        verify(tokenManager).saveToken("mytoken123")
    }

    @Test
    fun `login returns failure on HTTP error`() = runTest {
        val errorBody = "Unauthorized".toResponseBody(null)
        whenever(apiService.login(any(), any()))
            .thenReturn(Response.error(401, errorBody))

        val result = repository.login(LoginRequest("bad@test.com", "wrong"))

        assertTrue(result.isFailure)
        assertTrue(result.exceptionOrNull()?.message?.contains("401") == true)
        verify(tokenManager, never()).saveToken(any())
    }

    @Test
    fun `login returns failure on network exception`() = runTest {
        whenever(apiService.login(any(), any())).thenThrow(RuntimeException("No network"))

        val result = repository.login(LoginRequest("x@x.com", "p"))

        assertTrue(result.isFailure)
        assertEquals("No network", result.exceptionOrNull()?.message)
    }

    // ---- Register ----

    @Test
    fun `register saves token on success`() = runTest {
        val authResponse = AuthResponse("regtoken", "bearer")
        whenever(apiService.register(any())).thenReturn(Response.success(authResponse))

        val result = repository.register(
            RegisterRequest("new@test.com", "pass", "Name", "seeker", true)
        )

        assertTrue(result.isSuccess)
        verify(tokenManager).saveToken("regtoken")
    }

    @Test
    fun `register returns failure on 400 error`() = runTest {
        val errorBody = "Bad Request".toResponseBody(null)
        whenever(apiService.register(any())).thenReturn(Response.error(400, errorBody))

        val result = repository.register(
            RegisterRequest("dup@test.com", "p", "N", "seeker", false)
        )

        assertTrue(result.isFailure)
        verify(tokenManager, never()).saveToken(any())
    }

    // ---- Get Current User ----

    @Test
    fun `getCurrentUser returns user on success`() = runTest {
        val user = User(1, "test@test.com", "Test", "seeker", false)
        whenever(apiService.getCurrentUser()).thenReturn(Response.success(user))

        val result = repository.getCurrentUser()

        assertTrue(result.isSuccess)
        assertEquals("test@test.com", result.getOrNull()?.email)
    }

    @Test
    fun `getCurrentUser returns failure on 401`() = runTest {
        val errorBody = "Unauthorized".toResponseBody(null)
        whenever(apiService.getCurrentUser()).thenReturn(Response.error(401, errorBody))

        val result = repository.getCurrentUser()

        assertTrue(result.isFailure)
    }

    // ---- Logout ----

    @Test
    fun `logout clears token`() {
        repository.logout()

        verify(tokenManager).clearToken()
    }
}
