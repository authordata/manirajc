package com.dataman.support.ui

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.dataman.support.R

class AuthActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_auth)

        val emailField = findViewById<EditText>(R.id.emailField)
        val passwordField = findViewById<EditText>(R.id.passwordField)
        val status = findViewById<TextView>(R.id.authStatus)

        findViewById<Button>(R.id.loginButton).setOnClickListener {
            if (emailField.text.isNotBlank() && passwordField.text.isNotBlank()) {
                status.text = "Logged in (API integration ready)"
                startActivity(Intent(this, ChatActivity::class.java))
            } else {
                status.text = "Enter email and password"
            }
        }

        findViewById<Button>(R.id.signupButton).setOnClickListener {
            status.text = "Account created (API integration ready)"
            startActivity(Intent(this, ChatActivity::class.java))
        }
    }
}
