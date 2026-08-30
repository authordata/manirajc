package com.dataman.support.ui

import android.os.Bundle
import android.view.View
import androidx.activity.viewModels
import androidx.recyclerview.widget.LinearLayoutManager
import com.dataman.support.R
import com.dataman.support.databinding.ActivityChatBinding
import com.dataman.support.ui.adapter.ChatAdapter
import com.dataman.support.ui.viewmodel.ChatViewModel
import com.dataman.support.ui.viewmodel.SessionState
import com.dataman.support.ui.viewmodel.ViewModelFactory
import com.google.android.material.snackbar.Snackbar

class ChatActivity : BaseActivity() {

    private lateinit var binding: ActivityChatBinding
    private lateinit var chatAdapter: ChatAdapter

    private val chatViewModel: ChatViewModel by viewModels {
        ViewModelFactory(applicationContext)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityChatBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupBottomNavigation(binding.navBottom.bottomNavigationView)
        updateNavigationBarState(binding.navBottom.bottomNavigationView, R.id.nav_chat)

        setupUI()
        setupListeners()
        observeViewModel()
    }

    private fun setupUI() {
        chatAdapter = ChatAdapter()
        binding.rvMessages.apply {
            layoutManager = LinearLayoutManager(this@ChatActivity).apply {
                stackFromEnd = true
            }
            adapter = chatAdapter
        }
    }

    private fun setupListeners() {
        binding.toolbar.setNavigationOnClickListener {
            onBackPressed()
        }

        // Toggle between Human and AI support — starts a new session
        binding.toggleSupport.addOnButtonCheckedListener { _, checkedId, isChecked ->
            if (isChecked) {
                val isAi = checkedId == R.id.btnAISupport
                chatViewModel.startSession(cause = null, isAi = isAi)
            }
        }

        // Send message to backend via ViewModel
        binding.btnSend.setOnClickListener {
            val text = binding.etMessage.text.toString().trim()
            if (text.isNotBlank()) {
                chatViewModel.sendMessage(text)
                binding.etMessage.text?.clear()
            }
        }
    }

    private fun observeViewModel() {
        // Observe session state changes
        chatViewModel.sessionState.observe(this) { state ->
            when (state) {
                is SessionState.Idle -> {
                    showLoading(false)
                }
                is SessionState.Loading -> {
                    showLoading(true)
                }
                is SessionState.Active -> {
                    showLoading(false)
                    binding.btnSend.isEnabled = true
                    Snackbar.make(binding.root, "Session started!", Snackbar.LENGTH_SHORT).show()
                }
                is SessionState.Error -> {
                    showLoading(false)
                    Snackbar.make(binding.root, "Error: ${state.message}", Snackbar.LENGTH_LONG).show()
                }
            }
        }

        // Observe messages — update RecyclerView when new messages arrive
        chatViewModel.messages.observe(this) { messages ->
            chatAdapter.submitList(messages)
            if (messages.isNotEmpty()) {
                binding.rvMessages.scrollToPosition(messages.size - 1)
            }
        }

        // Observe sending state — disable send button while message is being sent
        chatViewModel.sendingMessage.observe(this) { isSending ->
            binding.btnSend.isEnabled = !isSending
        }
    }

    private fun showLoading(isLoading: Boolean) {
        binding.overlayLoading.visibility = if (isLoading) View.VISIBLE else View.GONE
    }
}
