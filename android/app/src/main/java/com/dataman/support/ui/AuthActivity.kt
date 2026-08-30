package com.dataman.support.ui
import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.ArrayAdapter
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.snackbar.Snackbar
import com.dataman.support.databinding.ActivityAuthBinding
import com.dataman.support.ui.viewmodel.AuthViewModel
import com.dataman.support.ui.viewmodel.ViewModelFactory
class AuthActivity : AppCompatActivity() {
private lateinit var binding: ActivityAuthBinding
private var isLoginMode = true
private val authViewModel: AuthViewModel by viewModels { ViewModelFactory(applicationContext) }
override fun onCreate(savedInstanceState: Bundle?) {
super.onCreate(savedInstanceState)
binding = ActivityAuthBinding.inflate(layoutInflater)
setContentView(binding.root)
setupUI()
setupListeners()
setupObservers()
}
private fun setupObservers() {
authViewModel.loginResult.observe(this) { result ->
showLoading(false)
if (result != null) {
if (result.isSuccess) {
navigateToChat()
} else {
Snackbar.make(binding.root, result.exceptionOrNull()?.message ?: "Login failed", Snackbar.LENGTH_LONG).show()
}
}
}
authViewModel.registerResult.observe(this) { result ->
showLoading(false)
if (result != null) {
if (result.isSuccess) {
startActivity(Intent(this, OtpVerificationActivity::class.java))
finishAffinity()
} else {
Snackbar.make(binding.root, result.exceptionOrNull()?.message ?: "Registration failed", Snackbar.LENGTH_LONG).show()
}
}
}
}
private fun setupUI() {
val roles = arrayOf("Support Seeker", "Support Giver")
val adapter = ArrayAdapter(this, android.R.layout.simple_spinner_dropdown_item, roles)
binding.spinnerRole.adapter = adapter
updateModeUI()
}
private fun setupListeners() {
binding.btnCreateAccount.setOnClickListener {
if (isLoginMode) {
isLoginMode = false
updateModeUI()
} else {
handleRegister()
}
}
binding.btnLogin.setOnClickListener {
if (!isLoginMode) {
isLoginMode = true
updateModeUI()
} else {
handleLogin()
}
}
}
private fun updateModeUI() {
if (isLoginMode) {
binding.tilDisplayName.visibility = View.GONE
binding.spinnerRole.visibility = View.GONE
binding.cbAnonymous.visibility = View.GONE
binding.btnLogin.text = "Login"
binding.btnCreateAccount.text = "Create Account"
} else {
binding.tilDisplayName.visibility = View.VISIBLE
binding.spinnerRole.visibility = View.VISIBLE
binding.cbAnonymous.visibility = View.VISIBLE
binding.btnLogin.text = "Switch to Login"
binding.btnCreateAccount.text = "Sign Up"
}
}
private fun handleLogin() {
val email = binding.etEmail.text.toString()
val password = binding.etPassword.text.toString()
if (!validateInputs(email, password)) return
showLoading(true)
authViewModel.login(email, password)
}
private fun handleRegister() {
val email = binding.etEmail.text.toString()
val password = binding.etPassword.text.toString()
val displayName = binding.etDisplayName.text.toString()
if (!validateInputs(email, password)) return
val role = if (binding.spinnerRole.selectedItemPosition == 0) "seeker" else "giver"
val isAnonymous = binding.cbAnonymous.isChecked
showLoading(true)
authViewModel.register(email, password, displayName, role, isAnonymous)
}
private fun validateInputs(email: String, pass: String): Boolean {
if (email.isEmpty() || !android.util.Patterns.EMAIL_ADDRESS.matcher(email).matches()) {
binding.tilEmail.error = "Invalid email"
return false
}
binding.tilEmail.error = null
if (pass.length < 6) {
binding.tilPassword.error = "Password must be at least 6 characters"
return false
}
binding.tilPassword.error = null
return true
}
private fun showLoading(isLoading: Boolean) {
binding.progressBar.visibility = if (isLoading) View.VISIBLE else View.GONE
binding.btnLogin.isEnabled = !isLoading
binding.btnCreateAccount.isEnabled = !isLoading
}
private fun navigateToChat() {
startActivity(Intent(this, ChatActivity::class.java))
finishAffinity()
}
}