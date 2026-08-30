package com.dataman.support.ui

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.ArrayAdapter
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.snackbar.Snackbar
import com.dataman.support.databinding.ActivityAuthBinding

class AuthActivity : AppCompatActivity() {

    private lateinit var binding: ActivityAuthBinding
    private var isLoginMode = true

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityAuthBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupUI()
        setupListeners()
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
        // Mock success
        binding.root.postDelayed({
            showLoading(false)
            navigateToChat()
        }, 500)
    }

    private fun handleRegister() {
        val email = binding.etEmail.text.toString()
        val password = binding.etPassword.text.toString()
        val displayName = binding.etDisplayName.text.toString()

        if (!validateInputs(email, password)) return

        showLoading(true)
        // Mock success
        binding.root.postDelayed({
            showLoading(false)
            navigateToChat()
        }, 500)
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
