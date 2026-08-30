package com.dataman.support.ui.viewmodel

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.dataman.support.data.model.User
import com.dataman.support.data.repository.AuthRepository
import kotlinx.coroutines.launch

class ProfileViewModel(
    private val authRepository: AuthRepository
) : ViewModel() {

    private val _user = MutableLiveData<User?>()
    val user: LiveData<User?> = _user

    private val _saveResult = MutableLiveData<Result<User>?>()
    val saveResult: LiveData<Result<User>?> = _saveResult

    private val _isLoading = MutableLiveData<Boolean>(false)
    val isLoading: LiveData<Boolean> = _isLoading

    init {
        loadProfile()
    }

    fun loadProfile() {
        viewModelScope.launch {
            _isLoading.value = true
            val result = authRepository.getCurrentUser()
            if (result.isSuccess) {
                _user.value = result.getOrNull()
            }
            _isLoading.value = false
        }
    }

    fun saveProfile(displayName: String, avatar: String? = null) {
        // Dummy implementation since actual update method is not provided in requirements
    }
}
