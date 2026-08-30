package com.dataman.support.ui.viewmodel

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.dataman.support.data.model.AuthResponse
import com.dataman.support.data.model.LoginRequest
import com.dataman.support.data.model.RegisterRequest
import com.dataman.support.data.model.User
import com.dataman.support.data.repository.AuthRepository
import com.dataman.support.data.local.TokenManager
import kotlinx.coroutines.launch

class AuthViewModel(
    private val authRepository: AuthRepository,
    private val tokenManager: TokenManager
) : ViewModel() {

    private val _loginResult = MutableLiveData<Result<AuthResponse>?>()
    val loginResult: LiveData<Result<AuthResponse>?> = _loginResult

    private val _registerResult = MutableLiveData<Result<AuthResponse>?>()
    val registerResult: LiveData<Result<AuthResponse>?> = _registerResult

    private val _isLoading = MutableLiveData<Boolean>(false)
    val isLoading: LiveData<Boolean> = _isLoading

    private val _currentUser = MutableLiveData<User?>()
    val currentUser: LiveData<User?> = _currentUser

    fun login(email: String, password: String) {
        viewModelScope.launch {
            _isLoading.value = true
            val result = authRepository.login(LoginRequest(email, password))
            if (result.isSuccess) {
                result.getOrNull()?.token?.let {
                    tokenManager.saveToken(it)
                }
            }
            _loginResult.value = result
            _isLoading.value = false
        }
    }

    fun register(email: String, password: String, displayName: String?, role: String, isAnonymous: Boolean) {
        viewModelScope.launch {
            _isLoading.value = true
            val result = authRepository.register(RegisterRequest(email, password, displayName, role, isAnonymous))
            if (result.isSuccess) {
                result.getOrNull()?.token?.let {
                    tokenManager.saveToken(it)
                }
            }
            _registerResult.value = result
            _isLoading.value = false
        }
    }

    fun loadCurrentUser() {
        viewModelScope.launch {
            _isLoading.value = true
            val result = authRepository.getCurrentUser()
            if (result.isSuccess) {
                _currentUser.value = result.getOrNull()
            }
            _isLoading.value = false
        }
    }

    fun logout() {
        tokenManager.clearToken()
        _currentUser.value = null
    }
}
