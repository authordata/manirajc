package com.dataman.support.ui
import android.os.Bundle
import android.view.View
import androidx.appcompat.app.AlertDialog
import android.net.Uri
import android.content.Intent
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
binding.toolbar.setOnMenuItemClickListener { menuItem ->
when (menuItem.itemId) {
R.id.action_connect -> {
showFriendRequestDialog()
true
}
R.id.action_emergency -> {
showCrisisDialog()
true
}
else -> false
}
}
binding.toolbar.setNavigationOnClickListener {
onBackPressed()
}
binding.toggleSupport.addOnButtonCheckedListener { _, checkedId, isChecked ->
if (isChecked) {
val isAi = checkedId == R.id.btnAISupport
chatViewModel.startSession(cause = null, isAi = isAi)
showMoodTrackingDialog(true)
}
}
binding.btnSend.setOnClickListener {
val text = binding.etMessage.text.toString().trim()
if (text.isNotBlank()) {
chatViewModel.sendMessage(text)
binding.etMessage.text?.clear()
}
}
}
private fun observeViewModel() {
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
chatViewModel.messages.observe(this) { messages ->
chatAdapter.submitList(messages)
if (messages.isNotEmpty()) {
binding.rvMessages.scrollToPosition(messages.size - 1)
}
}
chatViewModel.sendingMessage.observe(this) { isSending ->
binding.btnSend.isEnabled = !isSending
}
}
private fun showMoodTrackingDialog(isStart: Boolean) {
val title = if (isStart) "How are you feeling right now?" else "How are you feeling now?"
val emojis = arrayOf("😢", "😟", "😐", "🙂", "😊")
AlertDialog.Builder(this)
.setTitle(title)
.setItems(emojis) { _, which ->
Snackbar.make(binding.root, "Mood recorded: ${emojis[which]}", Snackbar.LENGTH_SHORT).show()
}
.setCancelable(false)
.show()
}
private fun showCrisisDialog() {
AlertDialog.Builder(this)
.setTitle("🚨 We Care About You")
.setMessage("If you are in crisis, please reach out to professional help immediately.\n\n📞 988 Suicide & Crisis Lifeline\n📱 Crisis Text Line: Text HOME to 741741\n\nYou are not alone.")
.setPositiveButton("Call 988") { _, _ ->
val intent = Intent(Intent.ACTION_DIAL, Uri.parse("tel:988"))
startActivity(intent)
}
.setNegativeButton("Continue Chat", null)
.show()
}
private fun showFriendRequestDialog() {
AlertDialog.Builder(this)
.setTitle("🤝 Connect")
.setMessage("Send a friend request? Your identity will be revealed if they accept.")
.setPositiveButton("Send") { _, _ ->
Snackbar.make(binding.root, "Friend request sent", Snackbar.LENGTH_SHORT).show()
}
.setNegativeButton("Cancel", null)
.show()
}
private fun showLoading(isLoading: Boolean) {
binding.overlayLoading.visibility = if (isLoading) View.VISIBLE else View.GONE
}
}