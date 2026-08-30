package com.dataman.support.ui.viewmodel

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import com.dataman.support.data.local.TokenManager
import com.dataman.support.data.repository.AuthRepository
import com.dataman.support.data.repository.ChatRepository

class ViewModelFactory(private val context: Context) : ViewModelProvider.Factory {

    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        val tokenManager = TokenManager(context)
        
        // Note: For a real app, DI like Hilt or Dagger is recommended.
        // We're instantiating repositories with defaults here as per requirements.
        val authRepository = AuthRepository() 
        val chatRepository = ChatRepository()

        return when {
            modelClass.isAssignableFrom(AuthViewModel::class.java) -> {
                AuthViewModel(authRepository, tokenManager) as T
            }
            modelClass.isAssignableFrom(ChatViewModel::class.java) -> {
                ChatViewModel(chatRepository) as T
            }
            modelClass.isAssignableFrom(ProfileViewModel::class.java) -> {
                ProfileViewModel(authRepository) as T
            }
            else -> throw IllegalArgumentException("Unknown ViewModel class")
        }
    }
}
