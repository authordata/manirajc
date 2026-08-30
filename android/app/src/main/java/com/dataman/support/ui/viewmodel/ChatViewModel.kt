package com.dataman.support.ui.viewmodel

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.dataman.support.data.model.ChatMessage
import com.dataman.support.data.model.FeedbackRequest
import com.dataman.support.data.model.FeedbackResponse
import com.dataman.support.data.model.MessageRequest
import com.dataman.support.data.model.SessionRequest
import com.dataman.support.data.repository.ChatRepository
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

sealed class SessionState {
    object Idle : SessionState()
    object Loading : SessionState()
    data class Active(val sessionId: Int) : SessionState()
    data class Error(val message: String) : SessionState()
}

class ChatViewModel(
    private val chatRepository: ChatRepository
) : ViewModel() {

    private val _messages = MutableLiveData<List<ChatMessage>>(emptyList())
    val messages: LiveData<List<ChatMessage>> = _messages

    private val _sessionState = MutableLiveData<SessionState>(SessionState.Idle)
    val sessionState: LiveData<SessionState> = _sessionState

    private val _sendingMessage = MutableLiveData<Boolean>(false)
    val sendingMessage: LiveData<Boolean> = _sendingMessage

    private val _feedbackResult = MutableLiveData<Result<FeedbackResponse>?>()
    val feedbackResult: LiveData<Result<FeedbackResponse>?> = _feedbackResult

    private var pollingJob: Job? = null

    fun startSession(cause: String?, isAi: Boolean) {
        viewModelScope.launch {
            _sessionState.value = SessionState.Loading
            val result = chatRepository.createSession(SessionRequest(cause, isAi))
            if (result.isSuccess) {
                val session = result.getOrNull()
                if (session != null) {
                    _sessionState.value = SessionState.Active(session.id)
                    startPolling()
                } else {
                    _sessionState.value = SessionState.Error("Invalid session data")
                }
            } else {
                _sessionState.value = SessionState.Error(result.exceptionOrNull()?.message ?: "Unknown error")
            }
        }
    }

    fun loadMessages() {
        val currentState = _sessionState.value
        if (currentState is SessionState.Active) {
            viewModelScope.launch {
                val result = chatRepository.getMessages(currentState.sessionId)
                if (result.isSuccess) {
                    _messages.value = result.getOrNull() ?: emptyList()
                }
            }
        }
    }

    fun sendMessage(text: String) {
        val currentState = _sessionState.value
        if (currentState is SessionState.Active) {
            viewModelScope.launch {
                _sendingMessage.value = true
                val result = chatRepository.sendMessage(currentState.sessionId, MessageRequest(text))
                if (result.isSuccess) {
                    loadMessages()
                }
                _sendingMessage.value = false
            }
        }
    }

    fun submitFeedback(rating: Int, comment: String?) {
        val currentState = _sessionState.value
        if (currentState is SessionState.Active) {
            viewModelScope.launch {
                val result = chatRepository.submitFeedback(currentState.sessionId, FeedbackRequest(rating, comment))
                _feedbackResult.value = result
            }
        }
    }

    private fun startPolling() {
        pollingJob?.cancel()
        pollingJob = viewModelScope.launch {
            while (true) {
                loadMessages()
                delay(5000)
            }
        }
    }

    override fun onCleared() {
        super.onCleared()
        pollingJob?.cancel()
    }
}
